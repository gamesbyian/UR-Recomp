#!/usr/bin/env python3
"""Exact native PPU final-visibility witness from one removed Original OBJ slot.

Three *independent* same-guest-frame PPU captures are required:
  1. Unchanged complete stock raster;
  2. Source-only alpha for exactly one OAM slot (RemoveFromGame=0);
  3. Native PPU composite with only that slot removed (no HD paint).
Compare all 342x224 RGBA pixels, not just source color matches. A difference
identifies a final-composite contribution from the removed slot; a source
alpha pixel with no difference is NOT automatically visible. This is solely
an opt-in counterfactual and never authorizes host Remastered rendering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

WIDTH, HEIGHT = 342, 224
HEADER = (f"P7\nWIDTH {WIDTH}\nHEIGHT {HEIGHT}\nDEPTH 4\nMAXVAL 255\n"
          "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")


def read_pam(path: Path) -> bytes:
    raw = path.read_bytes()
    size = WIDTH * HEIGHT * 4
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + size:
        raise ValueError(f"not an exact 342x224 native RGBA PPU raster: {path}")
    return raw[len(HEADER):]


def assess(stock_file: Path, source_file: Path, removed_file: Path,
           stock_crc: Path, source_crc: Path, removed_crc: Path,
           removed_log: Path, *, slot: int, frame: int) -> dict:
    if slot not in (96, 97, 98, 99) or frame < 0:
        raise ValueError("out-of-range original OAM slot or guest frame")
    raster_name = f"ur-baldosa-ws342-{frame:06d}.pam"
    source_name = f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam"
    if (stock_file.name != raster_name or
        removed_file.name != raster_name or
        source_file.name != source_name):
        raise ValueError("source, stock and counterfactual guest-frame IDs differ")
    stock, source, removed = (read_pam(x) for x in
                               (stock_file, source_file, removed_file))
    streams = [p.read_bytes().splitlines() for p in
               (stock_crc, source_crc, removed_crc)]
    guest_equal = bool(streams[0]) and streams[0] == streams[1] == streams[2]
    log = removed_log.read_text(encoding="utf-8", errors="replace")
    exact_log = (f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={frame} slot={slot} "
                 "status=armed guest_unchanged=1")
    authorized = sum(line.strip() == exact_log for line in log.splitlines()) == 1
    opaque = visible = outside = top = bottom = 0
    left = right = 0
    # Compare all exact four-byte pixels. Source alpha is a necessary,
    # not a sufficient, condition for the slot to have visibly contributed.
    for at in range(0, len(stock), 4):
        index = at // 4
        alpha = source[at + 3] != 0
        if alpha:
            opaque += 1
        if stock[at:at + 4] != removed[at:at + 4]:
            if not alpha:
                outside += 1
                continue
            visible += 1
            y, x = divmod(index, WIDTH)
            if y < HEIGHT // 2:
                top += 1
            else:
                bottom += 1
            if x < 43:
                left += 1
            if x >= WIDTH - 43:
                right += 1
    ok = guest_equal and authorized and opaque > 0 and visible > 0 and outside == 0
    return {
        "schema_version": 1,
        "status": "passed" if ok else "unproven",
        "guest_frame": frame,
        "source_oam_slot": slot,
        "guest_crc_equal_in_all_three_processes": guest_equal,
        "single_slot_original_ppu_removal_armed": authorized,
        "source_emitted_alpha_pixels": opaque,
        "native_ppu_final_contributed_pixels": visible,
        "native_ppu_changed_outside_emitted_source_alpha": outside,
        "visible_pixels_top": top,
        "visible_pixels_bottom": bottom,
        "visible_pixels_left_margin": left,
        "visible_pixels_right_margin": right,
        "stock_sha256": hashlib.sha256(stock).hexdigest(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "counterfactual_sha256": hashlib.sha256(removed).hexdigest(),
        "limits": (
            "A same-guest-frame host-only one-slot removal counterfactual. "
            "Changed final pixels identify actual native PPU contributions, "
            "not an HD compositing permit, original-emulator parity, "
            "proof of every other OBJ, window/color-math semantics or 4K."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for flag in ("stock", "source", "removed", "stock-crc", "source-crc",
                 "removed-crc", "removed-log", "out"):
        p.add_argument("--" + flag, type=Path, required=True)
    p.add_argument("--slot", type=int, required=True)
    p.add_argument("--frame", type=int, required=True)
    a = p.parse_args()
    report = assess(a.stock, a.source, a.removed, a.stock_crc, a.source_crc,
                    a.removed_crc, a.removed_log, slot=a.slot, frame=a.frame)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_BALDOSA_WIDE_FINAL_SLOT " + report["status"] +
          f" frame={a.frame} slot={a.slot} emitted={report['source_emitted_alpha_pixels']}" +
          f" contributed={report['native_ppu_final_contributed_pixels']}" +
          f" outside={report['native_ppu_changed_outside_emitted_source_alpha']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

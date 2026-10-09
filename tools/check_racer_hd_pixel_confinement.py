#!/usr/bin/env python3
"""QA-08: compare full-resolution native HD screenshot against stock outside live OAM.

A replacement may legitimately change its own pixels, but must leave every
other game/HUD/split-view pixel exactly untouched. Read live sprite placements
from the *same frame's* native acceptance log, not from guessed positions.
A changed racer rectangle does not prove foreground occlusion correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

DRAW = re.compile(
    r"UR_RACER_HD_DRAW PASS frame=(\d+) semantic=[0-9A-Fa-f]+ "
    r"viewport=(top|bottom) slot=(\d+) x=(-?\d+) y=(\d+)"
)
EXPECTED = {("top", 98), ("top", 99), ("bottom", 97), ("bottom", 96)}


def parse_ppm(data: bytes) -> tuple[int, int, bytes]:
    parts = data.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P6" or parts[2] != b"255":
        raise ValueError("only uncompressed P6 native screenshots are supported")
    try:
        width, height = map(int, parts[1].split())
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid P6 width/height") from exc
    if not 0 < width <= 8192 or not 0 < height <= 8192:
        raise ValueError("invalid P6 dimensions")
    if len(parts[3]) != width * height * 3:
        raise ValueError("P6 payload length mismatch")
    return width, height, parts[3]


def live_placements(log: str, frame: int) -> list[tuple[str, int, int, int]]:
    found: dict[tuple[str, int], tuple[str, int, int, int]] = {}
    for match in DRAW.finditer(log):
        guest_frame, viewport, slot, x, y = match.groups()
        if int(guest_frame) != frame:
            continue
        key = viewport, int(slot)
        if key not in EXPECTED or key in found:
            raise ValueError(f"duplicate or unexpected split OAM slot: {key}")
        record = viewport, int(slot), int(x), int(y)
        if not -256 <= record[2] <= 255 or not 0 <= record[3] <= 255:
            raise ValueError(f"invalid signed X or raw Y: {record}")
        found[key] = record
    if set(found) != EXPECTED:
        raise ValueError(f"frame {frame}: missing active OAM placements: {sorted(EXPECTED - set(found))}")
    return [found[key] for key in sorted(EXPECTED)]


def allowed_logical_mask(placements: list[tuple[str, int, int, int]]) -> bytearray:
    mask = bytearray(256 * 224)
    for viewport, _slot, x, raw_y in placements:
        low, high = (0, 112) if viewport == "top" else (112, 224)
        for screen_y in range(low, high):
            if ((screen_y - raw_y) & 255) >= 64:
                continue
            left, right = max(0, x), min(256, x + 64)
            for screen_x in range(left, right):
                mask[screen_y * 256 + screen_x] = 1
    return mask


def audit(
    original: bytes,
    hd: bytes,
    log: str,
    frame: int,
    *,
    second_original: bytes | None = None,
    capture_only: bool = False,
) -> dict:
    sw, sh, stock = parse_ppm(original)
    if (sw, sh) != (256, 224):
        raise ValueError("stock raster must be complete 256x224")
    if second_original is not None and second_original != original:
        raise ValueError("independent stock controls differ: unstable screenshot reference")
    hw, hh, high = parse_ppm(hd)
    if hw % sw or hh % sh or hw // sw != hh // sh:
        raise ValueError("HD raster must be an integer square-density expansion")
    scale = hw // sw
    if scale not in (1, 2, 3, 4):
        raise ValueError("unsupported native presentation density")
    places = live_placements(log, frame)
    allowed = allowed_logical_mask(places)

    changed = 0
    top = 0
    bottom = 0
    outside = []
    for output_y in range(hh):
        src_row = output_y // scale
        for output_x in range(hw):
            src_col = output_x // scale
            dst_idx = (output_y * hw + output_x) * 3
            src_idx = (src_row * sw + src_col) * 3
            if high[dst_idx:dst_idx + 3] == stock[src_idx:src_idx + 3]:
                continue
            changed += 1
            if src_row < 112:
                top += 1
            else:
                bottom += 1
            if not allowed[src_row * sw + src_col] and len(outside) < 10:
                outside.append([output_x, output_y, src_col, src_row])
    return {
        "schema_version": 1,
        "candidate_guest_frame": frame,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "hd_sha256": hashlib.sha256(hd).hexdigest(),
        "output_scale": scale,
        "actual_live_oam_slots": [
            {"viewport": viewport, "slot": slot, "x": x, "raw_y": y}
            for viewport, slot, x, y in places
        ],
        "changed_output_density_pixels": changed,
        "top_changed_pixels": top,
        "bottom_changed_pixels": bottom,
        "outside_live_oam_pixel_samples": outside,
        "original_controls_pixel_exact": second_original is not None,
        "diagnostic_capture_only": capture_only,
        "viewports_with_visible_changes": [
            name for name, count in (("top", top), ("bottom", bottom)) if count
        ],
        "ok": bool(changed and not outside and (capture_only or (top and bottom))),
        "claim_scope": (
            "original raster remains bit-exact outside 64x64 split OBJ footprints; "
            "capture-only can only prove removal of visible source pixels, not "
            "an entirely occluded racer; neither mode establishes internal "
            "sprite-vs-foreground priority or temporal quality"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True, type=Path)
    ap.add_argument("--original-control", type=Path)
    ap.add_argument("--hd", required=True, type=Path)
    ap.add_argument("--hd-log", required=True, type=Path)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--capture-only", action="store_true",
                    help="PPU stock removal proof; allow wholly occluded viewport")
    args = ap.parse_args()
    result = audit(
        args.original.read_bytes(),
        args.hd.read_bytes(),
        args.hd_log.read_text(encoding="utf-8", errors="replace"),
        args.frame,
        capture_only=args.capture_only,
        second_original=(
            args.original_control.read_bytes() if args.original_control else None
        ),
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"UR_RACER_HD_OAM_CONFINEMENT {'PASS' if result['ok'] else 'FAIL'} "
        f"frame={args.frame} scale={result['output_scale']} "
        f"changed={result['changed_output_density_pixels']} "
        f"outside={len(result['outside_live_oam_pixel_samples'])}"
    )
    if not result["ok"]:
        print(json.dumps(result, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

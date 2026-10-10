#!/usr/bin/env python3
"""Exact original PPU rear-slot deletion observation, not HD admission.

Unlike a *front* racer, the rear OAM slot may emit sprite pixels without
contributing any distinct final RGB because the front slot wins. Zero
stock-vs-rear-removal pixel differences are useful negative causal evidence,
but NOT evidence of an invisible/occluded pixel or a shipping HD paint mask.
Require a real same-frame native PPU removal run and its full guest CRCs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from tools.check_baldosa_wide_slot_final_visibility import (
        WIDTH, HEIGHT, read_pam,
    )
else:
    from check_baldosa_wide_slot_final_visibility import (
        WIDTH, HEIGHT, read_pam,
    )


def assess_rear(stock_file: Path, source_file: Path, removed_file: Path,
                stock_crc: Path, source_crc: Path, removed_crc: Path,
                removed_log: Path, *, rear_slot: int, frame: int) -> dict:
    if rear_slot not in (97, 99) or frame < 0:
        raise ValueError("only rear OAM 97/99 at nonnegative frame")
    common = f"ur-baldosa-ws342-{frame:06d}.pam"
    source_name = f"ur-baldosa-ws342-obj-slot{rear_slot}-frame{frame:06d}.pam"
    if (stock_file.name != common or removed_file.name != common or
        source_file.name != source_name):
        raise ValueError("not matching rear slot or guest frame names")
    stock, source, removed = (
        read_pam(p) for p in (stock_file, source_file, removed_file))
    streams = [p.read_bytes().splitlines() for p in
               (stock_crc, source_crc, removed_crc)]
    equal = bool(streams[0]) and streams[0] == streams[1] == streams[2]
    exact_log = (f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={frame} "
                 f"slot={rear_slot} status=armed guest_unchanged=1")
    authorized = sum(
        line.strip() == exact_log for line in
        removed_log.read_text(encoding="utf-8", errors="replace").splitlines()
    ) == 1
    emitted = changed = outside = 0
    top = bottom = 0
    for at in range(0, len(stock), 4):
        source_alpha = source[at + 3] != 0
        emitted += int(source_alpha)
        if stock[at:at + 4] != removed[at:at + 4]:
            if source_alpha:
                changed += 1
                if at // 4 // WIDTH < HEIGHT // 2:
                    top += 1
                else:
                    bottom += 1
            else:
                outside += 1
    valid = equal and authorized and emitted > 0 and outside == 0
    return {
        "schema_version": 1,
        "status": ("observed-rear-color-change" if changed else
                   "observed-no-rear-color-change") if valid else "unproven",
        "guest_frame": frame,
        "rear_slot": rear_slot,
        "guest_crc_equal_in_all_three_processes": equal,
        "native_rear_remove_exactly_armed": authorized,
        "rear_source_emitted_pixels": emitted,
        "rear_deletion_changed_pixels": changed,
        "rear_deletion_changed_top": top,
        "rear_deletion_changed_bottom": bottom,
        "rear_deletion_changed_outside_source": outside,
        "stock_sha256": hashlib.sha256(stock).hexdigest(),
        "rear_source_sha256": hashlib.sha256(source).hexdigest(),
        "removed_sha256": hashlib.sha256(removed).hexdigest(),
        "winner_identity_proven": False,
        "release_hd_admission": False,
        "limits": (
            "No rendered RGB delta can mean occlusion, clipping, equal "
            "underlying colour or unrelated priority. A positive rear RGB "
            "delta proves an affected output pixel, not unique OAM winner "
            "or source-safe HD art compositing."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for flag in ("stock", "source", "removed", "stock-crc", "source-crc",
                 "removed-crc", "removed-log", "out"):
        p.add_argument("--" + flag, type=Path, required=True)
    p.add_argument("--rear-slot", type=int, choices=(97, 99), required=True)
    p.add_argument("--frame", type=int, required=True)
    a = p.parse_args()
    report = assess_rear(
        a.stock, a.source, a.removed, a.stock_crc, a.source_crc,
        a.removed_crc, a.removed_log, rear_slot=a.rear_slot, frame=a.frame)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_WIDE_REAR_REMOVAL " + report["status"] +
          f" frame={a.frame} slot={a.rear_slot}" +
          f" source={report['rear_source_emitted_pixels']}" +
          f" changed={report['rear_deletion_changed_pixels']}" +
          f" outside={report['rear_deletion_changed_outside_source']}")
    return 0 if report["status"].startswith("observed-") else 1


if __name__ == "__main__":
    raise SystemExit(main())

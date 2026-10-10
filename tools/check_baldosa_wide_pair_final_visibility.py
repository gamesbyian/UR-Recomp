#!/usr/bin/env python3
"""Native PPU **paired** OBJ removal, distinct from single-slot attribution.

Two adjacent racer OAM slots are removed on ONE exact guest frame in an
independent native process, with the original and both read-only source
planes preserved. The source *union* is a necessary change-boundary; same
colour after both are gone remains an observational ambiguity. Never use
this output as a shipping widened HD paint-ownership mask.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.check_baldosa_wide_slot_final_visibility import (
    HEIGHT, WIDTH, read_pam,
)


def assess_pair(stock_file: Path, first_source: Path, second_source: Path,
                removed_file: Path, stock_crc: Path, first_crc: Path,
                second_crc: Path, removed_crc: Path, log_path: Path,
                *, first_slot: int, frame: int) -> dict:
    if first_slot not in (96, 98) or frame < 0:
        raise ValueError("pair must be exactly 96-97 or 98-99 at a valid guest frame")
    main_name = f"ur-baldosa-ws342-{frame:06d}.pam"
    expected_sources = (
        f"ur-baldosa-ws342-obj-slot{first_slot}-frame{frame:06d}.pam",
        f"ur-baldosa-ws342-obj-slot{first_slot + 1}-frame{frame:06d}.pam",
    )
    if (stock_file.name != main_name or removed_file.name != main_name or
        (first_source.name, second_source.name) != expected_sources):
        raise ValueError("paired source/main/removal guest frame or slot names differ")
    stock, front, rear, removed = map(
        read_pam, (stock_file, first_source, second_source, removed_file))
    streams = [f.read_bytes().splitlines()
               for f in (stock_crc, first_crc, second_crc, removed_crc)]
    guest_equal = bool(streams[0]) and all(x == streams[0] for x in streams[1:])
    marker = (f"UR_RACER_HD_WIDE_REMOVE_PAIR frame={frame} "
              f"slots={first_slot}-{first_slot + 1} "
              "status=armed guest_unchanged=1")
    count = sum(x.strip() == marker for x in log_path.read_text(
        encoding="utf-8", errors="replace").splitlines())
    authorized = count == 1
    union = changed = outside = common = 0
    top_changed = bottom_changed = 0
    for at in range(0, len(stock), 4):
        a = front[at + 3] != 0
        b = rear[at + 3] != 0
        if a or b:
            union += 1
        if a and b:
            common += 1
        if stock[at:at + 4] != removed[at:at + 4]:
            if not (a or b):
                outside += 1
                continue
            changed += 1
            if at // 4 // WIDTH < HEIGHT // 2:
                top_changed += 1
            else:
                bottom_changed += 1
    ok = guest_equal and authorized and union > 0 and changed > 0 and outside == 0
    return {
        "schema_version": 1,
        "status": "passed" if ok else "unproven",
        "guest_frame": frame,
        "removed_oam_slots": [first_slot, first_slot + 1],
        "guest_crc_equal_in_all_four_processes": guest_equal,
        "exact_pair_removal_armed": authorized,
        "source_alpha_union_pixels": union,
        "source_alpha_pair_overlap_pixels": common,
        "final_changed_pixels": changed,
        "changed_outside_source_union": outside,
        "final_changed_top": top_changed,
        "final_changed_bottom": bottom_changed,
        "stock_sha256": hashlib.sha256(stock).hexdigest(),
        "first_source_sha256": hashlib.sha256(front).hexdigest(),
        "second_source_sha256": hashlib.sha256(rear).hexdigest(),
        "counterfactual_sha256": hashlib.sha256(removed).hexdigest(),
        "release_hd_admission": False,
        "limits": (
            "Two-slot diagnostic measures changes after BOTH overlap sources "
            "are removed, not a per-slot winner mask, independent source-owner "
            "proof, authored HD admissibility, guest gameplay fidelity or 4K."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for option in ("stock", "first-source", "second-source", "removed",
                   "stock-crc", "first-crc", "second-crc", "removed-crc",
                   "removed-log", "out"):
        p.add_argument("--" + option, required=True, type=Path)
    p.add_argument("--first-slot", required=True, type=int, choices=(96, 98))
    p.add_argument("--frame", required=True, type=int)
    args = p.parse_args()
    result = assess_pair(args.stock, args.first_source, args.second_source,
                         args.removed, args.stock_crc, args.first_crc,
                         args.second_crc, args.removed_crc, args.removed_log,
                         first_slot=args.first_slot, frame=args.frame)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("UR_BALDOSA_WIDE_FINAL_PAIR " + result["status"] +
          f" frame={args.frame} slots={args.first_slot}-{args.first_slot + 1}" +
          f" union={result['source_alpha_union_pixels']}" +
          f" changed={result['final_changed_pixels']}" +
          f" outside={result['changed_outside_source_union']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

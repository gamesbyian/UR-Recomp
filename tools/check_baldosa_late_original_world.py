#!/usr/bin/env python3
"""Adjudicate one independently captured late native wide-Original PPU frame.

The live guest state/game phase is not established merely because an
absolute frame is late. This is visual evidence only and cannot confer
gameplay/release/HD replacement admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from tools.check_baldosa_physical_4k_capture import read_pam
    from tools.baldosa_ws24_presentation_report import edge_differences
else:
    from check_baldosa_physical_4k_capture import read_pam
    from baldosa_ws24_presentation_report import edge_differences

LINE = re.compile(
    r"^UR_BALDOSA_WS342_LATE_PRESENT frame=(\d+) saved=1 "
    r"logical=342x224 density=1 source=native-original-ppu$", re.M
)
FRAME = re.compile(r"ur-baldosa-ws342-(\d{6})\.pam\Z")
WIDTH, HEIGHT = 342, 224


def assess(captures: Path, log: Path, baseline_crc: Path,
           candidate_crc: Path, after: int) -> dict:
    if not 2000 <= after <= 2400:
        raise ValueError("outside bounded late native diagnostic window")
    stock = baseline_crc.read_bytes().splitlines()
    candidate = candidate_crc.read_bytes().splitlines()
    if len(stock) != 2473 or stock != candidate:
        raise ValueError("independent native guest CRC sequence absent or different")
    marks = [int(m) for m in LINE.findall(log.read_text(
        encoding="utf-8", errors="replace"))]
    if len(marks) != 1 or not after <= marks[0] <= 2450:
        raise ValueError("missing, repeated or outside-window native PPU late marker")
    latest = marks[0]
    files = sorted(captures.glob("ur-baldosa-ws342-*.pam"))
    if not files:
        raise ValueError("no original wide PPU capture")
    entries = {}
    for file in files:
        match = FRAME.fullmatch(file.name)
        if not match:
            raise ValueError(f"invalid native capture name: {file.name}")
        frame = int(match[1])
        if frame in entries:
            raise ValueError("duplicate native guest-frame image")
        width, height, pixels = read_pam(file)
        if (width, height) != (WIDTH, HEIGHT):
            raise ValueError("wrong original wide-Ppu geometry")
        margins = edge_differences(pixels, width=WIDTH, extra=43)
        entries[frame] = {
            "sha256": hashlib.sha256(pixels).hexdigest(),
            "all_four_world_margins_nontrivial": all(v > 32 for v in margins.values()),
            "margin_pixel_differences": margins,
            "raw_pixels": pixels,
        }
    if latest not in entries or any(frame > latest for frame in entries):
        raise ValueError("late marker does not bind final captured native frame")
    earlier = sorted(frame for frame in entries if frame < after)
    if len(earlier) < 2:
        raise ValueError("missing established independent early moving native frames")
    preceding = earlier[-1]
    last = entries[latest]
    before = entries[preceding]
    modified = sum(
        before["raw_pixels"][k:k+4] != last["raw_pixels"][k:k+4]
        for k in range(0, WIDTH * HEIGHT * 4, 4)
    )
    if modified == 0 or not last["all_four_world_margins_nontrivial"]:
        raise ValueError("late frame is static or lacks split-world margin pixels")
    return {
        "schema_version": 1,
        "status": "observed-late-native-wide-original",
        "requested_after_guest_frame": after,
        "real_late_guest_frame": latest,
        "earlier_comparison_frame": preceding,
        "independent_guest_frames_equal": 2473,
        "real_late_ppu_size": [WIDTH, HEIGHT],
        "late_ppu_rgba_sha256": last["sha256"],
        "earlier_ppu_rgba_sha256": before["sha256"],
        "changed_full_ppu_pixels_from_earlier": modified,
        "late_four_margin_differences": last["margin_pixel_differences"],
        "retained_raw_native_image": f"ur-baldosa-ws342-{latest:06d}.pam",
        "release_gameplay_visual_acceptance": False,
        "source_visible_hd_replacement_admitted": False,
        "limits": (
            "Observed moving native PPU Original split-world pixels beyond the "
            "early capture window, not yet independently identified as post-countdown "
            "race action. Requires visual review and HUD/source-OBJ attribution. "
            "Absolute frame counts are diagnostic only, not product scene state."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--baseline-crc", required=True, type=Path)
    ap.add_argument("--candidate-crc", required=True, type=Path)
    ap.add_argument("--after", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    x = ap.parse_args()
    report = assess(x.captures, x.log, x.baseline_crc,
                    x.candidate_crc, x.after)
    x.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_LATE_ORIGINAL_WORLD "
          f"frame={report['real_late_guest_frame']} "
          f"changed={report['changed_full_ppu_pixels_from_earlier']} "
          "status=observed-late-native-wide-original")


if __name__ == "__main__":
    main()

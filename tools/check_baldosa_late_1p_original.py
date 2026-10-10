#!/usr/bin/env python3
"""Exact native 1P source-world observation AFTER the early countdown captures.

Reuse the actual separate 1x and 4x guest processes. This is a source
projection QA observation, never proof of rendered authored HD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from tools.check_baldosa_wide_density_parity import capture_files, assess as parity
    from tools.baldosa_ws24_presentation_report import edge_differences
else:
    from check_baldosa_wide_density_parity import capture_files, assess as parity
    from baldosa_ws24_presentation_report import edge_differences

LATE = re.compile(
    r"(?m)^UR_BALDOSA_WS342_LATE_PRESENT frame=(\d+) saved=1 "
    r"logical=342x224 density=([14]) source=native-original-ppu$"
)
MODE = re.compile(
    r"(?m)^UR_BALDOSA_WS342_LIVE_MODE frame=(\d+) mode=1 "
    r"guest_race=([0-9A-F]+) frontend=([0-9A-F]+)$"
)
RACE = re.compile(r"(?m)^script f=(\d+) until 00E1F ok after \d+ frames$")
END = re.compile(r"(?m)^script f=(\d+) dump end ok$")


def read_log(log: Path, expected_density: int, min_frame: int,
             total_frames: int) -> int:
    txt = log.read_text(encoding="utf-8", errors="replace")
    pairs = [(int(f), int(d)) for f, d in LATE.findall(txt)]
    if len(pairs) != 1 or pairs[0][1] != expected_density:
        raise ValueError("exact unique density-specific native late PPU marker required")
    frame = pairs[0][0]
    if not min_frame <= frame <= min(min_frame + 250, total_frames):
        raise ValueError("native late 1P frame not within bounded active-scene window")
    modes = [(int(f), int(r, 16), int(frontend, 16))
             for f, r, frontend in MODE.findall(txt)]
    if not modes or not any(f < frame and frontend == 0x3c
                            for f, _, frontend in modes):
        raise ValueError("missing real 1P native guest scene authorization")
    entry, final = RACE.findall(txt), END.findall(txt)
    if len(entry) != 1 or len(final) != 1 or (
        int(entry[0]) >= frame or int(final[0]) != total_frames
    ):
        raise ValueError("missing 1P race script milestone or terminal provenance")
    return frame


def assess(base_crc: Path, one_crc: Path, four_crc: Path,
           one_log: Path, four_log: Path,
           one_dir: Path, four_dir: Path,
           after: int = 2200) -> dict:
    if after < 2000 or after > 2400:
        raise ValueError("invalid one-player late source diagnostic threshold")
    crc = base_crc.read_bytes().splitlines()
    if len(crc) != 5447 or one_crc.read_bytes().splitlines() != crc or (
        four_crc.read_bytes().splitlines() != crc
    ):
        raise ValueError("full independent 5447-frame 1P guest CRC streams differ")
    frame1 = read_log(one_log, 1, after, len(crc))
    frame4 = read_log(four_log, 4, after, len(crc))
    if frame1 != frame4:
        raise ValueError("independent source and dense native guest-frame identities differ")
    images1, images4 = capture_files(one_dir, 1), capture_files(four_dir, 4)
    if set(images1) != set(images4) or len(images1) != 7 or frame1 not in images1:
        raise ValueError("must retain all six early native frames plus one late image in each run")
    result = parity(images1, images4, min_shared_frames=7)
    if result["status"] != "passed":
        raise ValueError("native late 1P PPU Original 1x/4x parity not exact")
    early = max(f for f in images1 if f < after)
    before, after_pixels = images1[early], images1[frame1]
    changed = sum(
        before[i:i+4] != after_pixels[i:i+4]
        for i in range(0, len(after_pixels), 4)
    )
    if changed <= 100:
        raise ValueError("late native 1P original PPU looks static versus countdown")
    margins = edge_differences(after_pixels, width=342, extra=43)
    if any(n <= 32 for n in margins.values()):
        raise ValueError("actual 1P source-world margins are not independently visible")
    return {
        "schema_version": 1,
        "status": "native-1p-post-countdown-source-exact",
        "guest_frame": frame1,
        "earlier_guest_frame": early,
        "full_independent_guest_crcs_equal": len(crc),
        "independent_same_frame_source_pairs": result["exact_image_pairs"],
        "source_logical_dimensions": [342, 224],
        "original_4x_dimensions": [1368, 896],
        "changed_original_ppu_pixels": changed,
        "late_source_rgba_sha256": hashlib.sha256(after_pixels).hexdigest(),
        "late_four_x_rgba_sha256": hashlib.sha256(images4[frame1]).hexdigest(),
        "native_world_margin_nontrivial_pixels": margins,
        "release_gameplay_visual_accepted": False,
        "authored_wide_hd_admitted": False,
        "limits": (
            "Authenticated moving 1P original 342-wide pixels after the "
            "original script race milestone. No HD P1 source attribution, "
            "full event/result parity, device 4K output or Windows UI admission."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("baseline-crc", "one-crc", "four-crc", "one-log",
                "four-log", "one-dir", "four-dir", "out"):
        p.add_argument("--" + arg, required=True, type=Path)
    p.add_argument("--after", type=int, default=2200)
    a = p.parse_args()
    result = assess(a.baseline_crc, a.one_crc, a.four_crc,
                    a.one_log, a.four_log, a.one_dir, a.four_dir, a.after)
    a.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("UR_BALDOSA_1P_LATE_ORIGINAL "
          f"frame={result['guest_frame']} "
          f"changed={result['changed_original_ppu_pixels']} "
          f"matched={result['independent_same_frame_source_pairs']} "
          "status=native-1p-post-countdown-source-exact")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Exact native 2P original-PPU multiframe response to first-line HDMA prime.

This is an OBSERVATIONAL test: changes outside the accepted seam are
reported as negatives, not silently masked or used as a release verdict.
Three independent 256x224 source frames are captured in each of two entire
2,473-frame guest processes. No HD, wide-world or guest simulation edits.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_compare_native_hdma_prime_trial import (
        BASELINE_REAL_SHA256, HEADER, W, H, extract,
    )
except ModuleNotFoundError:
    from qa08_compare_native_hdma_prime_trial import (
        BASELINE_REAL_SHA256, HEADER, W, H, extract,
    )

FRAMES = (400, 1856, 2208)
SCHEMA = "qa08-real-native-before-after-prime-multiframe-PPU/1"
SCENES = {400: "2P-frontend", 1856: "2P-countdown", 2208: "2P-postGO"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(before: dict[int, bytes], after: dict[int, bytes],
          original_crc: bytes, trial_crc: bytes) -> dict:
    if (set(before) != set(FRAMES) or set(after) != set(FRAMES)
        or not original_crc or original_crc != trial_crc
        or len(original_crc.splitlines()) != 2473):
        raise ValueError("requires all three true source frames and identical complete 2P CRC")
    if sha(before[2208]) != BASELINE_REAL_SHA256:
        raise ValueError("real 2208 native stock source is not the accepted reference")
    scenes = []
    for frame in FRAMES:
        src, trial = extract(before[frame]), extract(after[frame])
        rows = Counter()
        samples = []
        alpha_deltas = 0
        for y in range(H):
            for x in range(W):
                pos = 4 * (y * W + x)
                orig = src[pos:pos + 4]
                candidate = trial[pos:pos + 4]
                if orig == candidate:
                    continue
                rows[y] += 1
                if orig[3] != candidate[3]:
                    alpha_deltas += 1
                if len(samples) < 10:
                    samples.append({
                        "xy": [x, y],
                        "real_stock_RGBA": orig.hex(),
                        "real_consumed_prime_RGBA": candidate.hex(),
                    })
        row_diff = [{"y": y, "count": rows[y]} for y in sorted(rows)]
        difference_count = sum(rows.values())
        seam_only = row_diff == [{"y": 111, "count": W}, {"y": 113, "count": W}]
        def all_black(buf: bytes, y: int) -> bool:
            return all(buf[4 * (y * W + x):4 * (y * W + x) + 3] == b"\0\0\0"
                       for x in range(W))
        seam_placement = (
            [y for y in (111, 112, 113) if all_black(src, y)] == [112, 113]
            and [y for y in (111, 112, 113) if all_black(trial, y)] == [111, 112]
        )
        scenes.append({
            "real_native_frame": frame,
            "scene": SCENES[frame],
            "actual_unmodified_native_original_source_SHA256": sha(before[frame]),
            "actual_consumed_prime_native_original_source_SHA256": sha(after[frame]),
            "total_original_size_RGBA_pixels": W * H,
            "changed_source_RGBA_pixels": difference_count,
            "changed_output_rows": row_diff,
            "any_source_alpha_changed": alpha_deltas != 0,
            "changed_source_alpha_pixels": alpha_deltas,
            "observed_source_samples": samples,
            "matches_2208_accepted_exact_seam_correction":
                frame == 2208 and seam_only and seam_placement and alpha_deltas == 0,
            "different_pixels_outside_split_seam_rows_111_and_113":
                sum(count for y, count in rows.items() if y not in (111, 113)),
        })
    at_2208 = scenes[2]
    if not at_2208["matches_2208_accepted_exact_seam_correction"]:
        raise ValueError("new native pair no longer reproduces independently proven seam")
    other = scenes[:2]
    return {
        "schema": SCHEMA,
        "status": "real_native_2P_multiframe_response_measured",
        "frames": list(FRAMES),
        "independently_real_2P_native_processes": 2,
        "identical_guest_CRC_frames": 2473,
        "reference_native_source_2208_sha256": BASELINE_REAL_SHA256,
        "total_source_pixels_compared": 3 * W * H,
        "all_non2208_source_frames_unchanged": all(
            x["changed_source_RGBA_pixels"] == 0 for x in other),
        "non2208_source_frames_with_visible_differences": [
            x["real_native_frame"] for x in other
            if x["changed_source_RGBA_pixels"]],
        "full_real_PPU_source_frame_dispositions": scenes,
        "all_channel_register_and_window_effects_proven": False,
        "independently_compared_original_Snes9x_400_or_1856": False,
        "other_2P_frames_and_1P_events_proven": False,
        "widescreen_342_and_4x_original_reexecuted": False,
        "cross_game_first_line_compatibility_proven": False,
        "native_production_HDMA_correction_authorized": False,
        "physical_SNES_hardware_verified": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before-dir", required=True, type=Path)
    p.add_argument("--after-dir", required=True, type=Path)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--trial-crc", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    name = lambda fr: f"ur-baldosa-original-source-{fr:06d}.pam"
    result = check({fr: (a.before_dir / name(fr)).read_bytes() for fr in FRAMES},
                   {fr: (a.after_dir / name(fr)).read_bytes() for fr in FRAMES},
                   a.baseline_crc.read_bytes(), a.trial_crc.read_bytes())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("QA08_HDMA_PRIME_MULTIFRAME_OBSERVED "
          f"frontend={result['full_real_PPU_source_frame_dispositions'][0]['changed_source_RGBA_pixels']} "
          f"countdown={result['full_real_PPU_source_frame_dispositions'][1]['changed_source_RGBA_pixels']} "
          "postGO=512 exact_original_other_scenes=unverified")


if __name__ == "__main__":
    main()

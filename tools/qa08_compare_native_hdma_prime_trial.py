#!/usr/bin/env python3
"""Observe real unchanged-vs-prime-consumed native 2P source PPU rasters.

One real 256x224 full-source P7 per *independent process*, no tolerance,
blurring, recolouring or source pixel alteration. This gate deliberately
does not certify original Snes9x equality from a native-to-native pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

W, H, DEPTH = 256, 224, 4
HEADER = b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
BASELINE_REAL_SHA256 = "a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f"
BASELINE_REFERENCE_RUN = 38504531564
ORIGINAL_SNES9X_REFERENCE_RUN = 38543766102
ORIGINAL_PIXEL_PARITY_REPORT = (
    "analysis/data/qa08-original-native-2p-split-seam-rgb5-pixel-parity-20261014.json"
)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def extract(raw: bytes) -> bytes:
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + W * H * DEPTH:
        raise ValueError("must provide complete unaltered native 256x224 RGB_ALPHA P7")
    return raw[len(HEADER):]


def assess(baseline: bytes, trial: bytes, baseline_crc: bytes, trial_crc: bytes,
           *, enforce_accepted_baseline: bool = True) -> dict:
    first = extract(baseline)
    second = extract(trial)
    if enforce_accepted_baseline and digest(baseline) != BASELINE_REAL_SHA256:
        raise ValueError("baseline unmodified real native P7 differs from accepted original-source image")
    if (not baseline_crc or baseline_crc != trial_crc
        or len(baseline_crc.splitlines()) != 2473
        or any(not row.startswith(b"0x") or len(row) != 10 or
               any(v not in b"0123456789ABCDEF" for v in row[2:])
               for row in baseline_crc.splitlines())):
        raise ValueError("real two-player independent 2473-frame guest CRC series differ or are incomplete")
    row_differences = []
    total = 0
    sample = []
    for y in range(H):
        changed = 0
        for x in range(W):
            i = (y * W + x) * DEPTH
            if first[i:i + 4] != second[i:i + 4]:
                changed += 1
                if len(sample) < 12:
                    sample.append({
                        "xy": [x, y],
                        "baseline_RGBA": first[i:i + 4].hex(),
                        "experiment_RGBA": second[i:i + 4].hex(),
                    })
        if changed:
            row_differences.append({"y": y, "count": changed})
            total += changed
    def black_row(pix: bytes, y: int) -> bool:
        return all(pix[(y * W + x) * 4:(y * W + x) * 4 + 3] == b"\x00\x00\x00"
                   for x in range(W))
    before = [y for y in (110, 111, 112, 113, 114) if black_row(first, y)]
    after = [y for y in (110, 111, 112, 113, 114) if black_row(second, y)]
    exact_shift = (
        total == 512
        and row_differences == [{"y": 111, "count": 256}, {"y": 113, "count": 256}]
        and before == [112, 113]
        and after == [111, 112]
        and all(first[(111 * W + x) * 4 + 3] ==
                second[(111 * W + x) * 4 + 3] for x in range(W))
        and all(first[(113 * W + x) * 4 + 3] ==
                second[(113 * W + x) * 4 + 3] for x in range(W))
    )
    return {
        "schema": "qa08-pinned-native-2p-prime-consumption-full-P7-counterfactual/1",
        "classification": ("source_native_one_row_seam_shift_exact" if exact_shift
                           else "source_native_hypothesis_not_supported"),
        "accepted_unmodified_native_reference_run": BASELINE_REFERENCE_RUN,
        "accepted_original_Snes9x_reference_run": ORIGINAL_SNES9X_REFERENCE_RUN,
        "unchanged_native_original_source_P7_sha256": digest(baseline),
        "experiment_native_original_source_P7_sha256": digest(trial),
        "original_source_size": [W, H],
        "guest_frame": 2208,
        "independent_complete_2P_guest_CRC_records": 2473,
        "changed_256wide_RGBA_pixels": total,
        "changed_output_rows": row_differences,
        "bounded_actual_RGBA_differences": sample,
        "baseline_all_black_rows_110_to_114": before,
        "experiment_all_black_rows_110_to_114": after,
        "counterfactual_raster_matches_expected_original_split_band_placement": exact_shift,
        "non_seam_native_RGBA_changes_observed": any(x["y"] not in (111, 113) for x in row_differences),
        "original_Snes9x_RGB5_exact_equality_proven_by_this_pair": False,
        "cross_game_HDMA_prime_compatibility_proven": False,
        "other_racing_frames_PPU_composition_checked": False,
        "physical_SNES_hardware_or_shipping_correction_approved": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--trial", type=Path, required=True)
    p.add_argument("--baseline-crc", type=Path, required=True)
    p.add_argument("--trial-crc", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = assess(args.baseline.read_bytes(), args.trial.read_bytes(),
                    args.baseline_crc.read_bytes(), args.trial_crc.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_NATIVE_PRIME_REAL_RASTER "
          f"classification={result['classification']} "
          f"changed={result['changed_256wide_RGBA_pixels']} "
          f"rows={result['changed_output_rows']} "
          "original_Snes9x_exact=unverified")


if __name__ == "__main__":
    main()

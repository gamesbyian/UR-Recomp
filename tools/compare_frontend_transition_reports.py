#!/usr/bin/env python3
"""Compare two dense frontend-transition motion reports.

The comparison asks whether two captures share the same transition timing and
candidate displacement sequence. It deliberately does not require their branded
pixels, changed-pixel counts, or bounding boxes to match.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MOTION_GAIN_THRESHOLD = 0.05


def _candidate_shift(row: dict, axis: str) -> int:
    if axis == "horizontal":
        shift_key = "best_shift_pixels"
        gain_key = "agreement_gain"
    elif axis == "vertical":
        shift_key = "best_vertical_shift_pixels"
        gain_key = "vertical_agreement_gain"
    else:
        raise ValueError(f"unknown motion axis: {axis}")

    shift = row.get(shift_key)
    gain = row.get(gain_key)
    if not isinstance(shift, int) or not isinstance(gain, (int, float)):
        raise ValueError(f"motion row missing {axis} shift evidence")
    return shift if shift != 0 and gain >= MOTION_GAIN_THRESHOLD else 0


def validate_report(report: object, name: str) -> dict:
    if not isinstance(report, dict):
        raise ValueError(f"{name}: report root must be an object")
    if report.get("schema_version") != 1:
        raise ValueError(f"{name}: unsupported transition report schema")
    pairs = report.get("pairs")
    if not isinstance(pairs, list):
        raise ValueError(f"{name}: pairs must be an array")

    expected_from = None
    for index, row in enumerate(pairs):
        if not isinstance(row, dict):
            raise ValueError(f"{name}: pair {index} must be an object")
        left = row.get("from_index")
        right = row.get("to_index")
        changed = row.get("changed_pixels")
        if (
            not isinstance(left, int)
            or not isinstance(right, int)
            or right != left + 1
            or not isinstance(changed, int)
            or changed < 0
        ):
            raise ValueError(f"{name}: malformed pair {index}")
        if expected_from is not None and left != expected_from:
            raise ValueError(f"{name}: non-consecutive pair sequence")
        expected_from = right
        _candidate_shift(row, "horizontal")
        _candidate_shift(row, "vertical")

    if report.get("pair_count") != len(pairs):
        raise ValueError(f"{name}: pair_count does not match pairs")
    if report.get("frame_count") != len(pairs) + 1:
        raise ValueError(f"{name}: frame_count does not match pairs")
    return report


def transition_signature(report: dict) -> dict:
    pairs = report["pairs"]
    return {
        "changed_timing": [
            bool(row["changed_pixels"]) for row in pairs
        ],
        "horizontal_shifts": [
            _candidate_shift(row, "horizontal") for row in pairs
        ],
        "vertical_shifts": [
            _candidate_shift(row, "vertical") for row in pairs
        ],
    }


def _mismatch_indices(left: list, right: list) -> list[int]:
    limit = min(len(left), len(right))
    mismatches = [
        index for index in range(limit)
        if left[index] != right[index]
    ]
    mismatches.extend(range(limit, max(len(left), len(right))))
    return mismatches


def compare_reports(left: object, right: object) -> dict:
    a = validate_report(left, "left")
    b = validate_report(right, "right")
    sig_a = transition_signature(a)
    sig_b = transition_signature(b)

    timing_mismatch = _mismatch_indices(
        sig_a["changed_timing"], sig_b["changed_timing"]
    )
    horizontal_mismatch = _mismatch_indices(
        sig_a["horizontal_shifts"], sig_b["horizontal_shifts"]
    )
    vertical_mismatch = _mismatch_indices(
        sig_a["vertical_shifts"], sig_b["vertical_shifts"]
    )

    same_length = a["pair_count"] == b["pair_count"]
    timing_match = same_length and not timing_mismatch
    horizontal_match = same_length and not horizontal_mismatch
    vertical_match = same_length and not vertical_mismatch

    return {
        "schema_version": 1,
        "left_frame_count": a["frame_count"],
        "right_frame_count": b["frame_count"],
        "same_pair_count": same_length,
        "changed_timing_match": timing_match,
        "horizontal_motion_signature_match": horizontal_match,
        "vertical_motion_signature_match": vertical_match,
        "motion_signature_match": (
            timing_match and horizontal_match and vertical_match
        ),
        "changed_timing_mismatch_pairs": timing_mismatch,
        "horizontal_motion_mismatch_pairs": horizontal_mismatch,
        "vertical_motion_mismatch_pairs": vertical_mismatch,
        "left_signature": sig_a,
        "right_signature": sig_b,
        "interpretation": (
            "A matching signature supports shared transition timing and sampled "
            "motion steps; it does not prove identical pixels, palette behavior, "
            "layer ownership, audio, or guest-state implementation."
        ),
    }


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read transition report {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = compare_reports(load_json(args.left), load_json(args.right))
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

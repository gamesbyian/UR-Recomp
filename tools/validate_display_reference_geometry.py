#!/usr/bin/env python3
"""Validate retained Uniracers manual screenshot display-geometry evidence."""

from __future__ import annotations

import argparse
import json
import statistics
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "analysis/display-reference-geometry.json"


def ratio_interval(width: int, height: int, edge_uncertainty: int) -> tuple[float, float]:
    delta = edge_uncertainty * 2
    if width <= delta or height <= delta:
        raise ValueError("measurement smaller than uncertainty envelope")
    return (width - delta) / (height + delta), (width + delta) / (height - delta)


def analyze(data: dict) -> dict:
    samples = data["samples"]
    uncertainty = int(data["source"]["edge_uncertainty_pixels_per_side"])
    four_three = float(Fraction(4, 3))
    raw_square = float(Fraction(8, 7))

    rows = []
    for sample in samples:
        width = int(sample["width"])
        height = int(sample["height"])
        ratio = width / height
        low, high = ratio_interval(width, height, uncertainty)
        rows.append(
            {
                "id": sample["id"],
                "ratio": ratio,
                "uncertainty_interval": [low, high],
                "contains_4x3": low <= four_three <= high,
                "contains_raw_8x7": low <= raw_square <= high,
            }
        )

    ratios = [r["ratio"] for r in rows]
    mean = statistics.fmean(ratios)
    median = statistics.median(ratios)
    mean_error_4x3 = abs(mean - four_three)
    mean_error_raw = abs(mean - raw_square)

    accepted = (
        len(rows) >= 8
        and all(r["contains_4x3"] for r in rows)
        and not any(r["contains_raw_8x7"] for r in rows)
        and mean_error_4x3 < mean_error_raw / 5
        and data["interpretation"]["overscan_disposition"] == "unresolved"
    )

    return {
        "schema_version": 1,
        "sample_count": len(rows),
        "mean_ratio": mean,
        "median_ratio": median,
        "target_4x3": four_three,
        "raw_square_8x7": raw_square,
        "mean_absolute_error_4x3": mean_error_4x3,
        "mean_absolute_error_raw_8x7": mean_error_raw,
        "all_uncertainty_intervals_admit_4x3": all(r["contains_4x3"] for r in rows),
        "any_uncertainty_interval_admits_raw_8x7": any(r["contains_raw_8x7"] for r in rows),
        "pixel_aspect_consequence_for_256x224": "7:6",
        "overscan_disposition": data["interpretation"]["overscan_disposition"],
        "accepted": accepted,
        "samples": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    data = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = analyze(data)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

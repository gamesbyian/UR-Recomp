#!/usr/bin/env python3
"""Audit canonical Uniracers framebuffer edge rows for fixed overscan cropping.

This distinguishes preservation/reference active height from optional CRT-style
overscan treatment. It does not claim that every historical CRT exposed every
source row; it asks whether a fixed crop would discard authored source pixels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.compare_ui_frames import load_bmp
except ModuleNotFoundError:
    from compare_ui_frames import load_bmp


def analyze_pixels(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int]],
    *,
    crop_rows: int = 4,
    mismatch_threshold: float = 0.02,
) -> dict:
    if width <= 0 or height <= crop_rows * 4:
        raise ValueError("frame too small for requested edge audit")
    if len(pixels) != width * height:
        raise ValueError("pixel count does not match geometry")

    def band(y0: int, y1: int) -> list[tuple[int, int, int]]:
        return pixels[y0 * width : y1 * width]

    top = band(0, crop_rows)
    top_inner = band(crop_rows, crop_rows * 2)
    bottom_inner = band(height - crop_rows * 2, height - crop_rows)
    bottom = band(height - crop_rows, height)

    def mismatch_fraction(a, b) -> float:
        return sum(x != y for x, y in zip(a, b)) / len(a)

    top_mismatch = mismatch_fraction(top, top_inner)
    bottom_mismatch = mismatch_fraction(bottom, bottom_inner)
    top_unique = len(set(top))
    bottom_unique = len(set(bottom))

    top_authored = top_unique > 1 and top_mismatch >= mismatch_threshold
    bottom_authored = bottom_unique > 1 and bottom_mismatch >= mismatch_threshold

    return {
        "dimensions": [width, height],
        "crop_rows_per_edge": crop_rows,
        "top_edge": {
            "unique_colors": top_unique,
            "mismatch_fraction_vs_adjacent_band": top_mismatch,
            "non_padding_authored_content": top_authored,
        },
        "bottom_edge": {
            "unique_colors": bottom_unique,
            "mismatch_fraction_vs_adjacent_band": bottom_mismatch,
            "non_padding_authored_content": bottom_authored,
        },
        "fixed_center_crop_discards_authored_edge_pixels": top_authored and bottom_authored,
    }


def analyze_capture(path: Path, *, crop_rows: int = 4) -> dict:
    width, height, pixels = load_bmp(path)
    row = analyze_pixels(width, height, pixels, crop_rows=crop_rows)
    row["capture"] = path.name
    return row


def build_report(paths: list[Path], *, crop_rows: int = 4) -> dict:
    captures = [analyze_capture(path, crop_rows=crop_rows) for path in paths]
    accepted = (
        len(captures) >= 3
        and all(row["dimensions"] == [256, 224] for row in captures)
        and all(row["fixed_center_crop_discards_authored_edge_pixels"] for row in captures)
    )
    return {
        "schema_version": 1,
        "question": "Should Authentic/reference mode impose a fixed centered 4+4 row crop?",
        "tested_crop_rows_per_edge": crop_rows,
        "captures": captures,
        "all_captures_are_256x224": all(row["dimensions"] == [256, 224] for row in captures),
        "all_captures_have_authored_content_at_both_cropped_edges": all(
            row["fixed_center_crop_discards_authored_edge_pixels"] for row in captures
        ),
        "reference_active_height_policy": "full-224" if accepted else "unresolved",
        "crt_overscan_treatment": "optional-and-separate",
        "accepted": accepted,
        "interpretation": (
            "A fixed 216-line reference crop would discard nonuniform, non-repeated "
            "authored source pixels at both edges in every representative capture. "
            "Preserve all 224 active source rows in Authentic/reference geometry; "
            "model CRT-style overscan separately because physical display crop varied."
            if accepted
            else "Representative edge evidence is insufficient to close active height."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="append", type=Path, required=True)
    parser.add_argument("--crop-rows", type=int, default=4)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = build_report(args.capture, crop_rows=args.crop_rows)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

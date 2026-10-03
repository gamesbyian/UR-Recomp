#!/usr/bin/env python3
"""Measure whether a proposed centered vertical crop discards distinct rendered content.

This is a title-specific display-geometry discriminator. It reads canonical
framebuffer BMPs, compares the rows a candidate crop would remove against the
nearest retained boundary rows, and reports whether that crop is observationally
content-neutral. It does not infer CRT visibility or alter runtime state.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


def read_bmp_rgb(path: Path) -> tuple[int, int, list[list[tuple[int, int, int]]]]:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"{path}: unsupported or truncated BMP")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"{path}: unsupported DIB header")
    width = struct.unpack_from("<i", data, 18)[0]
    raw_height = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if width <= 0 or raw_height == 0 or planes != 1 or compression != 0:
        raise ValueError(f"{path}: unsupported BMP geometry/compression")
    if bpp not in (24, 32):
        raise ValueError(f"{path}: expected 24- or 32-bit BMP, got {bpp}")

    height = abs(raw_height)
    bytes_per_pixel = bpp // 8
    row_stride = ((width * bytes_per_pixel + 3) // 4) * 4
    needed = pixel_offset + row_stride * height
    if needed > len(data):
        raise ValueError(f"{path}: truncated pixel data")

    rows: list[list[tuple[int, int, int]]] = []
    for logical_y in range(height):
        stored_y = logical_y if raw_height < 0 else height - 1 - logical_y
        start = pixel_offset + stored_y * row_stride
        row = []
        for x in range(width):
            p = start + x * bytes_per_pixel
            b, g, r = data[p : p + 3]
            row.append((r, g, b))
        rows.append(row)
    return width, height, rows


def row_diff_count(a: list[tuple[int, int, int]], b: list[tuple[int, int, int]]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def horizontal_transition_count(row: list[tuple[int, int, int]]) -> int:
    return sum(1 for a, b in zip(row, row[1:]) if a != b)


def analyze_capture(path: Path, crop_top: int, crop_bottom: int) -> dict[str, Any]:
    width, height, rows = read_bmp_rgb(path)
    if crop_top < 0 or crop_bottom < 0 or crop_top + crop_bottom >= height:
        raise ValueError("invalid crop")
    top_ref = rows[crop_top] if crop_top else None
    bottom_ref = rows[height - crop_bottom - 1] if crop_bottom else None

    top_rows = []
    for y in range(crop_top):
        top_rows.append(
            {
                "y": y,
                "different_from_nearest_retained_row_pixels": row_diff_count(rows[y], top_ref),
                "horizontal_transitions": horizontal_transition_count(rows[y]),
                "unique_colors": len(set(rows[y])),
            }
        )

    bottom_rows = []
    for y in range(height - crop_bottom, height):
        bottom_rows.append(
            {
                "y": y,
                "different_from_nearest_retained_row_pixels": row_diff_count(rows[y], bottom_ref),
                "horizontal_transitions": horizontal_transition_count(rows[y]),
                "unique_colors": len(set(rows[y])),
            }
        )

    distinct = sum(r["different_from_nearest_retained_row_pixels"] for r in top_rows + bottom_rows)
    cropped_pixels = width * (crop_top + crop_bottom)
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "crop_top": crop_top,
        "crop_bottom": crop_bottom,
        "cropped_pixels": cropped_pixels,
        "distinct_cropped_pixels_vs_nearest_retained_boundary": distinct,
        "distinct_fraction": (distinct / cropped_pixels) if cropped_pixels else 0.0,
        "crop_content_neutral": distinct == 0,
        "top_rows": top_rows,
        "bottom_rows": bottom_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Uniracers active-height crop discriminator",
        "",
        f"Candidate crop: top {report['crop_top']} / bottom {report['crop_bottom']} "
        f"({report['active_height']} active rows from {report['source_height']}).",
        "",
        "| Capture | Distinct cropped pixels | Cropped pixels | Fraction distinct | Neutral? |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["captures"]:
        lines.append(
            f"| {Path(row['path']).name} | "
            f"{row['distinct_cropped_pixels_vs_nearest_retained_boundary']} | "
            f"{row['cropped_pixels']} | {row['distinct_fraction']:.4f} | "
            f"{'yes' if row['crop_content_neutral'] else 'no'} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        report["interpretation"],
        "",
        "This discriminator measures rendered-information loss only. It does not by itself "
        "prove how much of the raster a period CRT exposed.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="append", type=Path, required=True)
    ap.add_argument("--crop-top", type=int, default=4)
    ap.add_argument("--crop-bottom", type=int, default=4)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--md-out", type=Path, required=True)
    args = ap.parse_args()

    captures = [analyze_capture(p, args.crop_top, args.crop_bottom) for p in args.capture]
    geometries = {(c["width"], c["height"]) for c in captures}
    if len(geometries) != 1:
        raise SystemExit(f"capture geometries differ: {sorted(geometries)}")
    width, height = next(iter(geometries))
    active_height = height - args.crop_top - args.crop_bottom
    all_neutral = all(c["crop_content_neutral"] for c in captures)
    total_distinct = sum(c["distinct_cropped_pixels_vs_nearest_retained_boundary"] for c in captures)
    total_cropped = sum(c["cropped_pixels"] for c in captures)

    interpretation = (
        f"The centered {active_height}-line crop is observationally content-neutral "
        f"across these canonical Uniracers captures."
        if all_neutral
        else
        f"The centered {active_height}-line crop is not observationally content-neutral: "
        f"{total_distinct} of {total_cropped} cropped pixels differ from the nearest "
        f"retained boundary row across the canonical capture set. This is evidence that "
        f"the outer rows contain authored/rendered image information, so a {active_height}-line "
        f"Authentic policy would need historical visibility evidence rather than being treated "
        f"as a harmless crop."
    )

    report = {
        "schema_version": 1,
        "source_width": width,
        "source_height": height,
        "crop_top": args.crop_top,
        "crop_bottom": args.crop_bottom,
        "active_height": active_height,
        "captures": captures,
        "all_captures_crop_content_neutral": all_neutral,
        "total_distinct_cropped_pixels_vs_nearest_retained_boundary": total_distinct,
        "total_cropped_pixels": total_cropped,
        "interpretation": interpretation,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

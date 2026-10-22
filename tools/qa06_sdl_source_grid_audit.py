#!/usr/bin/env python3
"""Check archived Modern compact SDL P7 surfaces share a 256x224 source grid.

This is a byte-level consistency check, not proof that SDL emitted the frames,
that the source ROM was canonical, that the source checkout is current, or that
any human, physical display, or release gate has passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_WIDTH = 256
SOURCE_HEIGHT = 224
# Observed pair from the preserved H27 source captures, NOT arbitrary game
# presentation geometry, and not the 342-wide Modern source policy.
GEOMETRIES = {(1024, 768): (0, 1024), (1280, 720): (160, 960)}


def _read_p7(path: Path, width: int, height: int) -> bytes:
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
              "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    expected = width * height * 4
    with path.open("rb") as file:
        if file.read(len(header)) != header:
            raise ValueError("source P7 format/geometry mismatch")
        pixels = file.read(expected + 1)
        if len(pixels) != expected:
            raise ValueError("source P7 truncated or trailing pixel data")
    return pixels


def extract_grid(path: Path, width: int, height: int) -> bytes:
    """Require a complete nearest-neighbour image derived from its center samples."""
    if type(width) is not int or type(height) is not int or (width, height) not in GEOMETRIES:
        raise ValueError("unsupported historical SDL geometry")
    left, crop_width = GEOMETRIES[(width, height)]
    pixels = _read_p7(path, width, height)
    row_width = width * 4
    if left:
        blank_left = bytes(left * 4)
        blank_right = bytes((width - left - crop_width) * 4)
        for y in range(height):
            row = pixels[y * row_width:(y + 1) * row_width]
            if row[:left * 4] != blank_left or row[(left + crop_width) * 4:] != blank_right:
                raise ValueError("4:3 matte has nonzero RGBA bytes")

    # Sample pixel centers and compare every pixel to the corresponding
    # nearest-neighbour source pixel. No model-specific image library is used.
    source_cols = [min(crop_width - 1, ((2*x + 1) * crop_width) // (2 * SOURCE_WIDTH))
                   for x in range(SOURCE_WIDTH)]
    source_rows = [min(height - 1, ((2*y + 1) * height) // (2 * SOURCE_HEIGHT))
                   for y in range(SOURCE_HEIGHT)]
    samples = bytearray(SOURCE_WIDTH * SOURCE_HEIGHT * 4)
    for y, sy in enumerate(source_rows):
        for x, sx in enumerate(source_cols):
            i = (sy * width + left + sx) * 4
            j = (y * SOURCE_WIDTH + x) * 4
            samples[j:j+4] = pixels[i:i+4]
    source = bytes(samples)
    back_cols = [min(SOURCE_WIDTH - 1, ((2*x + 1) * SOURCE_WIDTH) // (2 * crop_width))
                 for x in range(crop_width)]
    back_rows = [min(SOURCE_HEIGHT - 1, ((2*y + 1) * SOURCE_HEIGHT) // (2 * height))
                 for y in range(height)]
    for y, sy in enumerate(back_rows):
        for x, sx in enumerate(back_cols):
            i = (y * width + left + x) * 4
            j = (sy * SOURCE_WIDTH + sx) * 4
            if pixels[i:i+4] != source[j:j+4]:
                raise ValueError("SDL P7 contains a non-nearest-neighbour source pixel")
    return source


def audit_pair(compact: Path, wide: Path) -> dict:
    """Bound two historical surfaces to identical source-grid bytes."""
    first = extract_grid(compact, 1024, 768)
    second = extract_grid(wide, 1280, 720)
    if first != second:
        raise ValueError("same-source compact/wide P7 source grids differ")
    return {
        "source_grid": [SOURCE_WIDTH, SOURCE_HEIGHT],
        "source_grid_sha256": hashlib.sha256(first).hexdigest(),
        "checked_surfaces": ["1024x768", "1280x720"],
        "compact_matte_rgba_pixels": 0,
        "wide_matte_rgba_pixels": 230400,
        "source_bound_by_independent_rebuild": False,
        "physical_device_approved": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compact_p7", type=Path)
    parser.add_argument("wide_p7", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_pair(args.compact_p7, args.wide_p7), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

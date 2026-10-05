#!/usr/bin/env python3
"""Validate a binary P6 frame capture and emit stable summary fields."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PpmSummary:
    width: int
    height: int
    payload: bytes
    sha256: str
    unique_rgb: int
    nonblack_pixels: int


def inspect_ppm(path: Path) -> PpmSummary:
    raw = path.read_bytes()
    with path.open("rb") as handle:
        magic = handle.readline().strip()
        dimensions = handle.readline().strip().split()
        maximum = handle.readline().strip()
        payload = handle.read()
    if magic != b"P6" or len(dimensions) != 2 or maximum != b"255":
        raise ValueError(
            f"unexpected PPM header: {magic!r} {dimensions!r} {maximum!r}"
        )
    try:
        width, height = map(int, dimensions)
    except ValueError as exc:
        raise ValueError(f"invalid PPM dimensions: {dimensions!r}") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid PPM dimensions: {width}x{height}")
    expected = width * height * 3
    if len(payload) != expected:
        raise ValueError(
            f"PPM payload length {len(payload)} != expected {expected}"
        )
    pixels = (payload[index:index + 3] for index in range(0, len(payload), 3))
    colors = set(pixels)
    return PpmSummary(
        width=width,
        height=height,
        payload=payload,
        sha256=hashlib.sha256(raw).hexdigest(),
        unique_rgb=len(colors),
        nonblack_pixels=nonblack_pixel_count(payload),
    )


def nonblack_pixel_count(payload: bytes) -> int:
    return sum(
        payload[index:index + 3] != b"\0\0\0"
        for index in range(0, len(payload), 3)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--min-colors", type=int, default=1)
    args = parser.parse_args()

    try:
        summary = inspect_ppm(args.path)
        if args.width is not None and summary.width != args.width:
            raise ValueError(f"width {summary.width} != expected {args.width}")
        if args.height is not None and summary.height != args.height:
            raise ValueError(f"height {summary.height} != expected {args.height}")
        if summary.unique_rgb < args.min_colors:
            raise ValueError(
                f"unique RGB colors {summary.unique_rgb} < {args.min_colors}"
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    pixels = summary.width * summary.height
    print(f"screenshot={args.path}")
    print(f"dimensions={summary.width}x{summary.height}")
    print(f"sha256={summary.sha256}")
    print(f"unique_rgb={summary.unique_rgb}")
    print(
        f"nonblack_pixels={summary.nonblack_pixels}/{pixels} "
        f"({summary.nonblack_pixels / pixels:.3%})"
    )
    print(f"channel_min={min(summary.payload)} channel_max={max(summary.payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

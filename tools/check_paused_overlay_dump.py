#!/usr/bin/env python3
"""Assert that a paused-host present actually carried a Modern modal panel.

The desktop host can freeze the guest without presenting anything new, which
leaves the Modern pause family invisible while every diagnostic still reports
it open. ``SNESRECOMP_PAUSED_OVERLAY_DUMP`` captures what the paused host last
presented; this check requires the shared dark modal fill (``0x202020`` drawn
at high alpha over the frozen field) to cover most of the frame centre, which
a bare race frame does not (measured: 0.008 on the Dragster race frame versus
0.950 with the pause menu open).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_MIN_FRACTION = 0.5
DARK_NEUTRAL_MIN = 0x18
DARK_NEUTRAL_MAX = 0x30


def read_ppm(path: Path) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    parts = raw.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P6" or parts[2] != b"255":
        raise ValueError(f"{path}: not a binary P6/255 PPM")
    try:
        width, height = map(int, parts[1].split())
    except ValueError as exc:
        raise ValueError(f"{path}: invalid dimensions {parts[1]!r}") from exc
    if width <= 0 or height <= 0 or len(parts[3]) != width * height * 3:
        raise ValueError(f"{path}: payload does not match {width}x{height}")
    return width, height, parts[3]


def centre_dark_neutral_fraction(width: int, height: int, payload: bytes) -> float:
    x0, x1 = width // 3, 2 * width // 3
    y0, y1 = height // 3, 2 * height // 3
    total = dark = 0
    for y in range(y0, y1):
        row = y * width
        for x in range(x0, x1):
            i = (row + x) * 3
            r, g, b = payload[i], payload[i + 1], payload[i + 2]
            total += 1
            if r == g == b and DARK_NEUTRAL_MIN <= r <= DARK_NEUTRAL_MAX:
                dark += 1
    return dark / total if total else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dump", type=Path)
    parser.add_argument("--min-fraction", type=float, default=DEFAULT_MIN_FRACTION)
    args = parser.parse_args(argv)
    if not args.dump.is_file():
        print(f"paused overlay dump missing: {args.dump}", file=sys.stderr)
        return 1
    try:
        width, height, payload = read_ppm(args.dump)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    fraction = centre_dark_neutral_fraction(width, height, payload)
    print(f"paused_overlay width={width} height={height} centre_panel_fraction={fraction:.3f}")
    if fraction < args.min_fraction:
        print(
            f"paused present carries no modal panel (centre fraction {fraction:.3f} < {args.min_fraction})",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

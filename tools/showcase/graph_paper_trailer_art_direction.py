#!/usr/bin/env python3
"""Compatibility renderer for owner-approved Uniracers promotional plates.

Historical graph-paper cards and bespoke frame drawings are retired. This
entrypoint keeps filenames expected by older trailer compositors, but emits
only the approved source image in the requested aspect ratio. Overlays and
live footage remain the parent editor's responsibility.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
APPROVED = ROOT / "assets/promo/canonical"
LEGACY_CARDS = ("windows", "4k", "cta")
LEGACY_FRAMES = (
    "reveal", "race", "code", "raster", "parity", "art",
    "animation", "art_p2", "modern",
)
SOURCES = {
    "16x9-left": "blueprint-16x9-logo-left.png",
    "16x9-right": "blueprint-16x9-logo-right.png",
    "4x3-left": "blueprint-4x3-logo-left.png",
    "4x3-right": "blueprint-4x3-logo-right.png",
    "portrait": "blueprint-9x16-portrait-2160x3840.png",
}
SIZE = {"16x9": (1920, 1080), "4x3": (1440, 1080), "portrait": (1080, 1920)}


def produce(out: Path, *, aspect: str = "16x9", logo_corner: str = "right") -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    key = "portrait" if aspect == "portrait" else f"{aspect}-{logo_corner}"
    source = APPROVED / SOURCES[key]
    if not source.is_file():
        raise FileNotFoundError(f"Required owner-approved promotional plate missing: {source}")
    with Image.open(source) as original:
        expected = SIZE[aspect]
        # Preserve exact pixels when source output size already matches;
        # never crop, redraw, or independently synthesize illustration.
        if original.size[0] * expected[1] != original.size[1] * expected[0]:
            raise ValueError(f"Approved plate has wrong aspect: {source}, {original.size}")
        if original.size == expected:
            rendered = original.copy()
        else:
            rendered = original.resize(expected, Image.Resampling.LANCZOS)
        filenames = [*(f"{name}.png" for name in LEGACY_CARDS),
                     *(f"{name}-frame.png" for name in LEGACY_FRAMES)]
        for filename in filenames:
            rendered.save(out / filename)
    print(f"Rendered {len(filenames)} approved {aspect} backgrounds from {source.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--aspect", choices=("16x9", "4x3", "portrait"), default="16x9")
    parser.add_argument("--logo-corner", choices=("left", "right"), default="right")
    # Historical invocation options remain accepted, but cannot alter the art.
    parser.add_argument("--logo", help="Retired; ignored (logo is part of approved plate)")
    parser.add_argument("--track", help="Retired; ignored (track is part of approved plate)")
    args = parser.parse_args()
    produce(args.out, aspect=args.aspect, logo_corner=args.logo_corner)


if __name__ == "__main__":
    main()

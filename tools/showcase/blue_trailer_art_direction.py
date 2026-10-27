#!/usr/bin/env python3
"""Compatibility entrypoint: only owner-approved plates may be emitted.

Former blue procedural card/frame generation is retired. Keep the public
produce(out) contract for the flagship assembler, but redirect it to the
canonical renderer. No source artwork is redrawn.
"""
from pathlib import Path
from graph_paper_trailer_art_direction import produce as _approved_produce


def produce(out, *, aspect="16x9", logo_corner="right"):
    return _approved_produce(Path(out), aspect=aspect, logo_corner=logo_corner)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--aspect", choices=("16x9", "4x3", "portrait"), default="16x9")
    parser.add_argument("--logo-corner", choices=("left", "right"), default="right")
    args = parser.parse_args()
    produce(args.out, aspect=args.aspect, logo_corner=args.logo_corner)

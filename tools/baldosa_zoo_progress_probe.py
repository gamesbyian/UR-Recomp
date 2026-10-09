#!/usr/bin/env python3
"""Bounded nonterminal readout of pinned upstream Zoom Zoo drive."""
from __future__ import annotations
import argparse
from pathlib import Path

END = "\nuntil16 0053 == F60C\nwait 300\ndump end\nquit"
START_GATE = "until 0E1F != 00\n"
# These diagnostic dumps have no button/wait command of their own.
# They bracket the fixed upstream inputs; do not split press left 6000.
FIRST_DRIVE = "press left 300\n"
FINAL_STEER = "press left+x 20\n"

def progress_route(source: str) -> str:
    normalized = source.rstrip()
    if (not normalized.endswith(END) or normalized.count(START_GATE) != 1
            or normalized.count(FIRST_DRIVE) != 1
            or normalized.count(FINAL_STEER) != 1):
        raise ValueError("Pinned Zoom Zoo route changed; do not silently rewrite")
    original_drive = normalized[:-len(END)]
    return (original_drive.replace(START_GATE, START_GATE + "dump go\n", 1)
            .replace(FIRST_DRIVE, FIRST_DRIVE + "dump after_first_left\n", 1)
            .replace(FINAL_STEER, FINAL_STEER + "dump before_long_left\n", 1)
            + "\ndump after_drive\nquit\n")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = progress_route(args.source.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(result, encoding="utf-8")
    print(f"Sealed nonterminal Zoom Zoo probe: {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

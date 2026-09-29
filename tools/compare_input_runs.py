#!/usr/bin/env python3
"""Compare two neutral controller-input files by parsed intervals, not comments."""

from __future__ import annotations

import argparse
from pathlib import Path

from replay_input_via_lua import load_runs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("left", type=Path)
    ap.add_argument("right", type=Path)
    args = ap.parse_args()

    left = load_runs(args.left)
    right = load_runs(args.right)
    if left == right:
        print(f"input streams match ({len(left)} nonzero intervals)")
        return 0

    limit = max(len(left), len(right))
    for i in range(limit):
        a = left[i] if i < len(left) else None
        b = right[i] if i < len(right) else None
        if a != b:
            raise SystemExit(
                f"input streams differ at interval {i}: {args.left}={a}, {args.right}={b}"
            )
    raise SystemExit("input streams differ")


if __name__ == "__main__":
    raise SystemExit(main())

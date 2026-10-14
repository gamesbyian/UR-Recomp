#!/usr/bin/env python3
"""Deterministic, timing-balanced partition of tests/unit modules.

Replaces hash partitioning (which left shards uneven and capped parallelism at
two). Every discovered module lands in exactly one shard; modules absent from
tools/unit_test_timings.json get a small default weight, so a stale timing file
only costs balance, never coverage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_WEIGHT = 0.3


def discover(unit_dir: Path) -> list[str]:
    return sorted(f"tests.unit.{p.stem}" for p in unit_dir.glob("test_*.py"))


def partition(modules: list[str], timings: dict[str, float], shards: int) -> list[list[str]]:
    if shards < 1:
        raise ValueError("shards must be >= 1")
    loads = [0.0] * shards
    out: list[list[str]] = [[] for _ in range(shards)]
    # Longest-processing-time-first greedy; name tiebreak keeps it deterministic.
    for module in sorted(modules, key=lambda m: (-timings.get(m, DEFAULT_WEIGHT), m)):
        idx = min(range(shards), key=lambda i: (loads[i], i))
        out[idx].append(module)
        loads[idx] += timings.get(module, DEFAULT_WEIGHT)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, required=True)
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--unit-dir", type=Path, default=Path("tests/unit"))
    ap.add_argument("--timings", type=Path, default=Path("tools/unit_test_timings.json"))
    args = ap.parse_args()
    timings = json.loads(args.timings.read_text()) if args.timings.is_file() else {}
    parts = partition(discover(args.unit_dir), timings, args.shards)
    print("\n".join(parts[args.index]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

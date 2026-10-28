#!/usr/bin/env python3
"""Rebalance the complete unit suite using measured, source-pinned CI modules.

Read-only until --out is explicitly supplied. Every module and shard must be
present exactly once from one successful full run; a partial/cancelled/failing
suite never becomes scheduling data. This changes ONLY future scheduling,
never discovery, verification requirements, or official release evidence.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re

try:
    from tools.partition_unit_tests import discover, partition
except ModuleNotFoundError:
    # Direct invocation via python3 tools/rebalance_unit_test_timings.py.
    from partition_unit_tests import discover, partition

SCHEMA = "ur-unit-module-timings/1"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def calibrate(root: Path, unit_dir: Path, source_sha: str, shards: int) -> dict:
    if not SHA.fullmatch(source_sha) or type(shards) is not int or shards not in (2, 3, 4):
        raise ValueError("expected complete source SHA and 2-4 measured shards")
    if not root.is_dir() or root.is_symlink() or not unit_dir.is_dir():
        raise ValueError("missing genuine unit timing or test directory")
    expected = discover(unit_dir)
    if not expected or len(expected) != len(set(expected)):
        raise ValueError("empty or duplicate discovered unit modules")
    observed: dict[str, float] = {}
    for i in range(shards):
        path = root / f"unit-module-timings-shard{i}.json"
        if not path.is_file() or path.is_symlink():
            raise ValueError("missing or redirected shard timing: " + str(i))
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("nonfinite module time " + value)),
        )
        if (type(payload) is not dict or payload.get("schema") != SCHEMA
                or payload.get("diagnostic_only") is not True
                or payload.get("full_test_suite_passed") is not True
                or payload.get("pr_or_test_merge_sha") != source_sha):
            raise ValueError("unqualified or mismatched full-suite timing: " + str(i))
        data = payload.get("module_timings_seconds")
        if (type(data) is not dict or payload.get("observed_modules") != len(data)
                or not data):
            raise ValueError("missing module timing population: " + str(i))
        for name, value in data.items():
            if name not in expected or name in observed:
                raise ValueError("unknown or duplicate measured module: " + name)
            if (type(value) not in (float, int) or
                    not math.isfinite(value) or not 0 <= value < 3600):
                raise ValueError("invalid measured module time: " + name)
            observed[name] = round(float(value), 4)
    if set(observed) != set(expected):
        raise ValueError("incomplete suite module timing coverage")
    return dict(sorted(observed.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--unit-dir", type=Path, default=Path("tests/unit"))
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--shards", type=int, required=True, choices=(2, 3, 4))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    weights = calibrate(args.source, args.unit_dir, args.source_sha, args.shards)
    if args.out.is_symlink():
        raise ValueError("refusing symlink output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(weights, indent=2) + "\n", encoding="utf-8")
    predicted = partition(list(weights), weights, args.shards)
    totals = [round(sum(weights[name] for name in part), 3) for part in predicted]
    print("Measured modules=" + str(len(weights)) +
          "; predicted shard-seconds on next same-host run=" + repr(totals) +
          ". This is a scheduling estimate, NOT a timed speedup or QA credit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

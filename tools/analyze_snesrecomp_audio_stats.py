#!/usr/bin/env python3
"""Reduce SNESRecomp's *production* audio ring/callback stats to bounded evidence.

SNESRECOMP_AUDIO_STATS=<file> is a framework-supported opt-in readout of the
always-on Release counters. It is independent from AUDIO_TRACE dev builds and
does not require exposing PCM or touching guest state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = (
    "ms produced consumed dropped dropped_audible drop_runs underflows "
    "consume_calls occupancy hiwater prod_cpu prod_audio missing_frames priming"
).split()
MONOTONIC = set(FIELDS) - {"ms", "occupancy"}
MONOTONIC.add("ms")


def parse_audio_stats(path: Path, *, min_records: int = 2) -> list[dict]:
    if min_records < 1:
        raise ValueError("min_records must be positive")
    lines = path.read_text(encoding="utf-8").splitlines()
    records: list[dict] = []
    saw_header = False
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line[1:].strip().split() != FIELDS or saw_header or records:
                raise ValueError(f"{path}:{n}: invalid or repeated audio stats header")
            saw_header = True
            continue
        if not saw_header:
            raise ValueError(f"{path}:{n}: missing audio stats header")
        values = line.split()
        if len(values) != len(FIELDS) or not all(v.isascii() and v.isdecimal() for v in values):
            raise ValueError(f"{path}:{n}: malformed audio stats row")
        record = dict(zip(FIELDS, map(int, values)))
        if record["dropped_audible"] > record["dropped"]:
            raise ValueError(f"{path}:{n}: audible drops exceed all drops")
        if record["prod_cpu"] + record["prod_audio"] > record["produced"]:
            raise ValueError(f"{path}:{n}: producer attribution exceeds output")
        if records:
            previous = records[-1]
            for field in MONOTONIC:
                if record[field] < previous[field]:
                    raise ValueError(f"{path}:{n}: counter {field} regressed")
        records.append(record)
    if len(records) < min_records:
        raise ValueError(
            f"{path}: only {len(records)} audio stats snapshots, need {min_records}"
        )
    return records


def summarize_audio_stats(
    path: Path,
    *,
    min_records: int = 2,
    max_new_audible_drops: int | None = None,
    max_new_underflows: int | None = None,
    max_new_missing_frames: int | None = None,
) -> dict:
    limits = {
        "dropped_audible": max_new_audible_drops,
        "underflows": max_new_underflows,
        "missing_frames": max_new_missing_frames,
    }
    if any(x is not None and x < 0 for x in limits.values()):
        raise ValueError("audio continuity limits must be non-negative")
    rows = parse_audio_stats(path, min_records=min_records)
    first, last = rows[0], rows[-1]
    diffs = {field: last[field] - first[field] for field in MONOTONIC if field != "ms"}
    for field, limit in limits.items():
        if limit is not None and diffs[field] > limit:
            raise ValueError(
                f"audio continuity {field} delta {diffs[field]} exceeds limit {limit}"
            )
    return {
        "schema_version": 1,
        "audio_origin": "snesrecomp-production-audio-stats",
        "snapshots": len(rows),
        "observed_ms": last["ms"] - first["ms"],
        "first": first,
        "last": last,
        "deltas": diffs,
        "occupancy_min": min(x["occupancy"] for x in rows),
        "occupancy_max": max(x["occupancy"] for x in rows),
        "limits_applied": {key: value for key, value in limits.items() if value is not None},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stats", type=Path)
    ap.add_argument("--min-records", type=int, default=2)
    ap.add_argument("--max-new-audible-drops", type=int)
    ap.add_argument("--max-new-underflows", type=int)
    ap.add_argument("--max-new-missing-frames", type=int)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = summarize_audio_stats(
        args.stats,
        min_records=args.min_records,
        max_new_audible_drops=args.max_new_audible_drops,
        max_new_underflows=args.max_new_underflows,
        max_new_missing_frames=args.max_new_missing_frames,
    )
    d = report["deltas"]
    print(
        "AUDIO_QUEUE_STATS PASS "
        f"snapshots={report['snapshots']} observed_ms={report['observed_ms']} "
        f"audible_drops={d['dropped_audible']} underflows={d['underflows']} "
        f"missing_frames={d['missing_frames']} produced={d['produced']} "
        f"consumed={d['consumed']}"
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

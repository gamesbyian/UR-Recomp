#!/usr/bin/env python3
"""Validate event-relative player-state semantics across two race fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_FIELDS = [
    "in_race",
    "track",
    "x_pos",
    "y_pos",
    "x_speed",
    "y_speed",
    "pitch_effective",
    "air_effective",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("native", type=Path)
    ap.add_argument("reference", type=Path)
    ap.add_argument("--field", action="append", dest="fields")
    ap.add_argument("--require-movement", action="store_true")
    ap.add_argument("--require-cross-engine-match", action="store_true")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    a = load(args.native)
    b = load(args.reference)
    fields = args.fields or DEFAULT_FIELDS

    report = {
        "fields": fields,
        "checkpoints": {},
        "cross_engine_match": True,
        "movement": {},
    }

    if list(a) != list(b):
        raise SystemExit(
            f"checkpoint order mismatch: native={list(a)} reference={list(b)}"
        )

    for checkpoint in a:
        diffs = {}
        for field in fields:
            if field not in a[checkpoint] or field not in b[checkpoint]:
                raise SystemExit(f"{checkpoint}: missing field {field}")
            if a[checkpoint][field] != b[checkpoint][field]:
                diffs[field] = {
                    "native": a[checkpoint][field],
                    "reference": b[checkpoint][field],
                }
        if diffs:
            report["cross_engine_match"] = False
        report["checkpoints"][checkpoint] = {"differences": diffs}
        print(
            f"{checkpoint}: "
            + ("MATCH" if not diffs else " ".join(
                f"{k}={v['native']}/{v['reference']}" for k, v in diffs.items()
            ))
        )

    first = next(iter(a))
    last = next(reversed(a))
    for label, data in (("native", a), ("reference", b)):
        x0 = data[first]["x_pos"]
        x1 = data[last]["x_pos"]
        speeds = [state["x_speed"] for state in data.values()]
        moved = x1 != x0 or any(v != 0 for v in speeds[1:])
        max_abs_speed = max(abs(v) for v in speeds)
        report["movement"][label] = {
            "start_checkpoint": first,
            "end_checkpoint": last,
            "x_pos_start": x0,
            "x_pos_end": x1,
            "x_pos_delta": x1 - x0,
            "x_speeds": speeds,
            "max_abs_x_speed": max_abs_speed,
            "moved": moved,
        }
        print(
            f"{label}: xPos {x0}->{x1} delta={x1-x0}; "
            f"xSpeed={speeds}; moved={moved}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.require_cross_engine_match and not report["cross_engine_match"]:
        return 1
    if args.require_movement and not all(x["moved"] for x in report["movement"].values()):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

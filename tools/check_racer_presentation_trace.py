#!/usr/bin/env python3
"""Validate frame-independent relationships in Racer HD presentation logs.

This is intentionally a shadow validator. It does not decide which absolute
frames are product timing invariants; it validates structural relationships
within whatever draw transitions the runtime logged.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict


KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
TRACE_MARKERS = ("UR_RACER_PRESENTATION_TRACE", "UR_RACER_PRESENTATION_OBS")
DRAW_MARKER = "UR_RACER_HD_DRAW PASS"
EXPECTED_SLOTS = {
    ("top", 98): "p1_primary",
    ("top", 99): "p2_primary",
    ("bottom", 97): "p1_primary",
    ("bottom", 96): "p2_primary",
}


def _kv(line: str) -> dict[str, str]:
    return dict(KV_RE.findall(line))


def _parse_hex(value: str) -> int:
    return int(value, 16)


def analyze(text: str) -> dict[str, object]:
    traces: dict[int, dict[str, str]] = {}
    draws: dict[int, dict[tuple[str, int], int]] = defaultdict(dict)
    errors: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(marker in line for marker in TRACE_MARKERS):
            fields = _kv(line)
            if "frame" not in fields:
                continue
            try:
                frame = int(fields["frame"], 10)
            except ValueError:
                errors.append(f"line {line_number}: invalid trace frame")
                continue
            if "p1_primary" not in fields or "p2_primary" not in fields:
                continue
            prior = traces.get(frame)
            if prior is not None and (
                prior["p1_primary"] != fields["p1_primary"]
                or prior["p2_primary"] != fields["p2_primary"]
            ):
                errors.append(
                    f"frame {frame}: conflicting presentation trace primaries"
                )
                continue
            traces[frame] = fields

        if DRAW_MARKER in line:
            fields = _kv(line)
            required = {"frame", "semantic", "viewport", "slot"}
            if not required.issubset(fields):
                errors.append(
                    f"line {line_number}: incomplete Racer HD draw event"
                )
                continue
            try:
                frame = int(fields["frame"], 10)
                semantic = _parse_hex(fields["semantic"])
                slot = int(fields["slot"], 10)
            except ValueError:
                errors.append(f"line {line_number}: invalid Racer HD draw field")
                continue
            key = (fields["viewport"], slot)
            if key not in EXPECTED_SLOTS:
                continue
            if key in draws[frame]:
                errors.append(
                    f"frame {frame}: duplicate draw for {key[0]} slot {key[1]}"
                )
                continue
            draws[frame][key] = semantic

    complete_frames: list[int] = []
    validated_frames: list[int] = []
    frames_without_trace: list[int] = []

    for frame in sorted(draws):
        frame_draws = draws[frame]
        if not all(key in frame_draws for key in EXPECTED_SLOTS):
            continue
        complete_frames.append(frame)
        trace = traces.get(frame)
        if trace is None:
            frames_without_trace.append(frame)
            continue

        frame_ok = True
        for key, primary_field in EXPECTED_SLOTS.items():
            try:
                expected = _parse_hex(trace[primary_field])
            except ValueError:
                errors.append(
                    f"frame {frame}: invalid {primary_field} in presentation trace"
                )
                frame_ok = False
                continue
            actual = frame_draws[key]
            if actual != expected:
                errors.append(
                    f"frame {frame}: {key[0]} slot {key[1]} semantic "
                    f"{actual:04X} != {primary_field} {expected:04X}"
                )
                frame_ok = False
        if frame_ok:
            validated_frames.append(frame)

    return {
        "trace_frame_count": len(traces),
        "draw_frame_count": len(draws),
        "complete_draw_frames": complete_frames,
        "validated_complete_frames": validated_frames,
        "complete_frames_without_trace": frames_without_trace,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--min-complete-frames", type=int, default=1)
    args = parser.parse_args()

    report = analyze(args.log.read_text(encoding="utf-8", errors="replace"))
    errors = list(report["errors"])
    complete = report["complete_draw_frames"]
    validated = report["validated_complete_frames"]
    missing_trace = report["complete_frames_without_trace"]

    if len(complete) < args.min_complete_frames:
        errors.append(
            f"complete draw frames {len(complete)} < required "
            f"{args.min_complete_frames}"
        )
    if missing_trace:
        errors.append(
            "complete draw frames missing presentation trace: "
            + ",".join(str(frame) for frame in missing_trace)
        )
    if len(validated) != len(complete):
        errors.append(
            f"validated complete draw frames {len(validated)} "
            f"!= complete draw frames {len(complete)}"
        )

    report["errors"] = errors
    report["ok"] = not errors

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if errors:
        for error in errors:
            print(f"RACER_PRESENTATION_TRACE ERROR {error}", file=sys.stderr)
        return 1

    print(
        "RACER_PRESENTATION_TRACE PASS "
        f"trace_frames={report['trace_frame_count']} "
        f"draw_frames={report['draw_frame_count']} "
        f"complete={len(complete)} validated={len(validated)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate measured Zoo/Bowl host-frame arithmetic without upgrading QA status.

Different source entry frame calibrations cannot be conflated with original/
native absolute host frame labels. A one-frame scene-relative difference is
independent of the absolute shift, and is not evidence of a CPU/NMI defect.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_KINDS = {"circuit-a", "timed-stunt"}
FRAME_FIELDS = ("original_entry", "native_entry",
                "original_terminal", "native_terminal",
                "original_relative", "native_relative")


def check_crosswalk(doc: dict) -> dict:
    if doc.get("schema") != "UR-QA01-TWO-EVENT-RESULT-PHASE/1":
        raise ValueError("unsupported cross-event phase report")
    if doc.get("release_usa_accepted_courses") != 0 or doc.get("release_usa_denominator") != 45:
        raise ValueError("source candidate cannot promote a USA complete course")
    rows = doc.get("measurements")
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("require exactly the two independent source family witnesses")
    families = set()
    for row in rows:
        if not all(type(row.get(key)) is int and row[key] >= 0
                   for key in FRAME_FIELDS):
            raise ValueError("missing or invalid original/native absolute or relative frame")
        if not isinstance(row.get("derived"), dict):
            raise ValueError("missing source-measured offset calculation")
        if type(row.get("run")) is not int or type(row.get("artifact")) is not int:
            raise ValueError("missing pinned source run/artifact identity")
        if row["kind"] in families:
            raise ValueError("duplicate event family")
        families.add(row["kind"])
        original = row["original_terminal"] - row["original_entry"]
        native = row["native_terminal"] - row["native_entry"]
        if original != row["original_relative"] or native != row["native_relative"]:
            raise ValueError("incorrect scene-relative terminal frame or entry anchor")
        measures = {
            "native_minus_original_entry_host_frames":
                row["native_entry"] - row["original_entry"],
            "native_minus_original_terminal_host_frames":
                row["native_terminal"] - row["original_terminal"],
            "native_minus_original_terminal_scene_relative_frames":
                native - original,
            "result_host_shift_minus_entry_host_shift":
                (row["native_terminal"] - row["original_terminal"])
                - (row["native_entry"] - row["original_entry"]),
        }
        if row["derived"] != measures:
            raise ValueError("source frame offset arithmetic inconsistent")
        if measures["native_minus_original_terminal_scene_relative_frames"] != -1:
            raise ValueError("candidate does not reproduce observed minus-one phase lead")
    if families != REQUIRED_KINDS:
        raise ValueError("missing Circuit or Stunt independent pair")
    return {
        "event_families": sorted(families),
        "phase_offset_native_minus_original": -1,
        "official_usa_complete_accepted": 0,
        "causal_conclusion": "unresolved",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=Path("analysis/data/two-event-original-native-result-phase-crosswalk-20261009.json"))
    args = ap.parse_args()
    print(json.dumps(check_crosswalk(json.loads(args.input.read_text())), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

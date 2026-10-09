#!/usr/bin/env python3
"""Static checkpoint/finish candidate cell census for every USA ROM course.

Resource 0x24 incidence alone is weaker than a placed 16x16 world cell.
This ROM-identity-gated census counts the exact descriptor-owned resource
placements for ALL 45 courses and ranks historical finish-X gaps. It cannot
infer event activation, contact footprint, lap order or result completion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from probe_course_checkpoint_placements import (
    CHECKPOINT_RESOURCE_ID, USA_SHA256, c000_resource_ranges,
    place_resource_cells, summarize_placements,
)
from rnc_method1 import unpack_method1

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
CORPUS = ROOT / "analysis/data/course-corpus.json"
KINDS = ("race-a", "circuit-a", "stunt", "race-b", "circuit-b")


class CourseCellCensusError(ValueError):
    pass


def classify_course(course: dict, parsed: dict, cells: list[dict]) -> dict:
    present = CHECKPOINT_RESOURCE_ID in parsed["resource_ids"]
    stunt = course["track_kind"] == "stunt"
    if present == stunt:
        raise CourseCellCensusError(
            f"{course['id']}: resource 0x24 mode incidence contradicts course kind"
        )
    if not present and cells:
        raise CourseCellCensusError(
            f"{course['id']}: resource 0x24 cells returned without resource"
        )
    world_extent_x = parsed["layout_dims"][0] * 256
    finish_x = course["historical_landmarks"]["finish_x"]
    if not (0 <= finish_x < world_extent_x):
        raise CourseCellCensusError(
            f"{course['id']}: historical optimizer finish X outside decoded extent"
        )
    summary = summarize_placements(cells, probe_x=finish_x)
    probe = summary["historical_finish_x_probe"]
    if stunt:
        priority = "timed_stunt_no_checkpoint_family"
    elif not cells:
        priority = "race_resource_present_but_no_placed_cells"
    elif probe["matching_candidate_cells"] == 0:
        priority = "race_finish_x_has_no_same_column_checkpoint_candidate"
    else:
        priority = "race_finish_x_overlaps_static_candidate"
    return {
        "course_id": course["id"],
        "stream_index": course["stream_index"],
        "name": course["name"],
        "event_kind": course["track_kind"],
        "resource_0x24_listed": present,
        "resource_0x24_placed": bool(cells),
        "candidate_world_cells": summary["candidate_world_cells"],
        "candidate_coarse_sectors": summary["candidate_coarse_sectors"],
        "candidate_c000_slot_counts": summary["candidate_cells_by_c000_slot"],
        "historical_finish_x": finish_x,
        "historical_finish_x_candidate_count": probe["matching_candidate_cells"],
        "closest_finish_x_candidate_gap": probe["closest_candidate_x_distance"],
        "priority_class": priority,
    }


def summarize(entries: list[dict]) -> dict:
    kinds = Counter(e["event_kind"] for e in entries)
    priorities = Counter(e["priority_class"] for e in entries)
    if len(entries) != 45 or any(kinds[kind] != 9 for kind in KINDS):
        raise CourseCellCensusError("must cover all nine original tour events per family")
    if sum(e["resource_0x24_listed"] for e in entries) != 36:
        raise CourseCellCensusError("checkpoint/finish resource incidence changed")
    if any(e["event_kind"] == "stunt" and e["resource_0x24_placed"]
           for e in entries):
        raise CourseCellCensusError("timed Stunt has unexpected ordinary checkpoint cells")
    ranked = sorted((e for e in entries if e["event_kind"] != "stunt"),
                    key=lambda e: (
                        0 if not e["resource_0x24_placed"] else 1,
                        -(e["closest_finish_x_candidate_gap"] or 0),
                        e["stream_index"],
                    ))
    return {
        "schema_version": 1,
        "source": "exact USA retail ROM decoded RNC, resource descriptor and course corpus",
        "scope": "STATIC course-placement evidence; no guest event/finish acceptance",
        "denominator": 45,
        "ordinary_race_circuit_count": 36,
        "timed_stunt_count": 9,
        "race_with_any_placed_checkpoint_family_cells": sum(
            e["resource_0x24_placed"] for e in entries
            if e["event_kind"] != "stunt"
        ),
        "race_with_no_placed_checkpoint_family_cells": sum(
            not e["resource_0x24_placed"] for e in entries
            if e["event_kind"] != "stunt"
        ),
        "priority_class_counts": dict(sorted(priorities.items())),
        "static_finish_x_nonoverlap_cases": [
            {"course_id": e["course_id"], "name": e["name"],
             "closest_x_gap": e["closest_finish_x_candidate_gap"]}
            for e in ranked if e["priority_class"] !=
            "race_finish_x_overlaps_static_candidate"
        ],
        "cases": entries,
        "caution": (
            "Missing a same-column cell at a hand-entered historical finish X "
            "does not prove an incorrect finish. Side-approach, footprint, "
            "packed control bits and runtime dispatch phase remain unknown."
        ),
    }


def build_report(rom: bytes, corpus: dict) -> dict:
    if hashlib.sha256(rom).hexdigest() != USA_SHA256:
        raise CourseCellCensusError("requires exact canonical USA retail ROM")
    courses = corpus.get("courses")
    if not isinstance(courses, list) or len(courses) != 45:
        raise CourseCellCensusError("requires exactly 45 named course identities")
    streams = list(find_streams(rom))
    if len(streams) != 45:
        raise CourseCellCensusError("requires exactly 45 original RNC course streams")
    results = []
    for index, (entry, (_offset, packed, _header)) in enumerate(zip(courses, streams), 1):
        if (entry.get("id") != f"course:{index:02d}"
                or entry.get("stream_index") != index
                or entry.get("track_kind") != KINDS[(index - 1) % 5]):
            raise CourseCellCensusError("course identity/order mismatch")
        decoded = unpack_method1(packed)
        parsed = parse_course_resource_list(decoded)
        ranges = c000_resource_ranges(rom, parsed["resource_ids"])
        cells = place_resource_cells(decoded, ranges)
        results.append(classify_course(entry, parsed, cells))
    return summarize(results)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=ROM)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--fail-missing-race-placement", action="store_true")
    args = ap.parse_args()
    report = build_report(args.rom.read_bytes(), json.loads(args.corpus.read_text()))
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.fail_missing_race_placement and report["race_with_no_placed_checkpoint_family_cells"]:
        raise SystemExit("one or more race/circuit courses list 0x24 without placing a cell")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

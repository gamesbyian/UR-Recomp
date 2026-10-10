#!/usr/bin/env python3
"""Fail-closed QA-01/QA-07 content/event census, never an emulator oracle.

Course identity and type come from the normalized ROM-derived course corpus.
Release evidence must be supplied separately, with event-level reference/native
witnesses. Static RNC decoding, candidate finish cells and partial experiments
can never silently pass a complete player journey.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "analysis/data/course-corpus.json"
EVIDENCE = ROOT / "analysis/data/course-event-runtime-evidence.json"
OUTPUT = ROOT / "analysis/generated/course-event-qa-census.json"

# Primary Windows candidate is USA retail. The two PAL variants are
# comparative originals, not automatic L4 shipping blockers.
PRIMARY_RELEASE_ROM = "usa-retail"
COMPARISON_ROMS = ("usa-retail", "europe-retail", "pal-prototype-1994-11-29")
SLOT_KINDS = ("race-a", "circuit-a", "stunt", "race-b", "circuit-b")
RACE_EVENTS = ("menu_entry", "start_state", "contact", "checkpoint",
               "lap", "finish", "result")
STUNT_EVENTS = ("menu_entry", "start_state", "contact", "stunt_scoring",
                "timer_expiry", "result")
ACCEPTED_CORE = ("pinned-snes9x", "mesen-ce")


def validate_catalog(catalog: dict) -> list[dict]:
    courses = catalog.get("courses")
    if not isinstance(courses, list) or len(courses) != 45:
        raise ValueError("census requires all 45 canonical courses")
    expected_ids = [f"course:{index:02d}" for index in range(1, 46)]
    if [c.get("id") for c in courses] != expected_ids:
        raise ValueError("missing, repeated or out-of-order canonical course ID")
    if [c.get("stream_index") for c in courses] != list(range(1, 46)):
        raise ValueError("stream identity is not contiguous 1..45")
    if len({c.get("name") for c in courses}) != 45:
        raise ValueError("course names must be present and unique")
    if len({c.get("tour") for c in courses}) != 9:
        raise ValueError("expected nine named tours")
    for index, course in enumerate(courses):
        kind = SLOT_KINDS[index % 5]
        if course.get("track_kind") != kind:
            raise ValueError(f"{course['id']}: wrong event-slot kind")
        if course.get("tour_slot") != (index % 5) + 1:
            raise ValueError(f"{course['id']}: wrong tour slot")
        header = course.get("header", {})
        if header.get("stunt_time_or_mode") != (45 if kind == "stunt" else 0):
            raise ValueError(f"{course['id']}: inconsistent stunt header")
        resources = course.get("resources", {}).get("ids", [])
        if (0x24 in resources) != (kind != "stunt"):
            raise ValueError(f"{course['id']}: checkpoint family incidence mismatch")
    return courses


def historic_start_probe(course: dict) -> dict:
    """Classify hand-entered TAS optimizer X leads, not live spawn evidence.

    The preserved magicnumber.lua script assigns startX constants but never
    uses them to compute its boost/finish distance. Zero is especially
    ambiguous; equality with a zero header does NOT verify a spawn.
    """
    landmark = course["historical_landmarks"]
    historic = landmark["start_x"]
    header_x = course["header"]["spawn_or_landmark_a"][0] * 16
    if historic == 0:
        status = "zero_optimizer_constant_unqualified"
    elif historic == header_x:
        status = "nonzero_numeric_match_only"
    else:
        status = "nonzero_numeric_disagreement"
    return {
        "course_id": course["id"],
        "name": course["name"],
        "historical_start_x": historic,
        "header_candidate_x16": header_x,
        "status": status,
        "runtime_spawn_proven": False,
    }


def validated_witness(witness: dict, kind: str) -> bool:
    """True only for a full, independently compared end-to-end event.

    These assertions validate report completeness, not the truth of an
    external measurement. A human/reviewer still admits its provenance.
    """
    required = STUNT_EVENTS if kind == "stunt" else RACE_EVENTS
    observed = witness.get("event_observations")
    return (
        witness.get("reference_core") in ACCEPTED_CORE
        and isinstance(witness.get("candidate_sha"), str)
        and len(witness["candidate_sha"]) == 40
        and isinstance(witness.get("rom_sha256"), str)
        and len(witness["rom_sha256"]) == 64
        and isinstance(witness.get("reference_run"), str)
        and bool(witness["reference_run"].strip())
        and isinstance(witness.get("native_run"), str)
        and bool(witness["native_run"].strip())
        and isinstance(witness.get("input_script"), str)
        and bool(witness["input_script"].strip())
        and isinstance(observed, dict)
        and all(observed.get(event) == "reference_matched" for event in required)
        and witness.get("result_compared") is True
        and witness.get("fresh_process") is True
    )


def build_census(catalog: dict, source: dict) -> dict:
    courses = validate_catalog(catalog)
    observations = source.get("observations")
    if source.get("schema_version") != 1 or not isinstance(observations, list):
        raise ValueError("expected version-1 independent observation register")
    known = {c["id"]: c for c in courses}
    keyed = {}
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("observation must be an object")
        region = observation.get("rom")
        cid = observation.get("course_id")
        if region not in COMPARISON_ROMS or cid not in known:
            raise ValueError(f"unknown ROM or canonical course in observation: {region}/{cid}")
        key = (region, cid)
        if key in keyed:
            raise ValueError(f"duplicate course/ROM observation: {key}")
        if observation.get("status") not in ("partial", "passed", "failed", "blocked"):
            raise ValueError(f"unsupported observation status: {key}")
        if not observation.get("evidence_ref"):
            raise ValueError(f"observation missing evidence path: {key}")
        if observation["status"] == "passed" and not validated_witness(
            observation, known[cid]["track_kind"]
        ):
            raise ValueError(f"complete event pass lacks independent witness: {key}")
        keyed[key] = observation
    entries = []
    for rom in COMPARISON_ROMS:
        for course in courses:
            note = keyed.get((rom, course["id"]))
            row = {
                "rom": rom, "course_id": course["id"],
                "stream_index": course["stream_index"],
                "name": course["name"], "tour": course["tour"],
                "event_kind": course["track_kind"],
                "expected_events": (
                    list(STUNT_EVENTS) if course["track_kind"] == "stunt"
                    else list(RACE_EVENTS)
                ),
                "status": note["status"] if note else "unverified",
                "evidence_ref": note["evidence_ref"] if note else None,
                "coverage_note": note.get("coverage_note") if note else None,
            }
            entries.append(row)
    counts = Counter(row["status"] for row in entries)
    coordinate_probes = [historic_start_probe(course) for course in courses]
    coordinate_counts = Counter(p["status"] for p in coordinate_probes)
    by_rom = {rom: dict(sorted(Counter(
        row["status"] for row in entries if row["rom"] == rom
    ).items())) for rom in COMPARISON_ROMS}
    by_family = {kind: dict(sorted(Counter(
        row["status"] for row in entries if row["event_kind"] == kind
    ).items())) for kind in SLOT_KINDS}
    return {
        "schema_version": 1,
        "source_catalog": "analysis/data/course-corpus.json",
        "source_observations": "analysis/data/course-event-runtime-evidence.json",
        "meaning": "release-event acceptance, not RNC/parser or static contact coverage",
        "primary_release_rom": PRIMARY_RELEASE_ROM,
        "regions": list(COMPARISON_ROMS),
        "denominators": {
            "courses_per_rom": 45,
            "primary_release_cases": len(courses),
            "regional_comparison_cases": len(entries) - len(courses),
            "tracked_region_course_cases": len(entries),
            "race_circuit_cases": sum(r["event_kind"] != "stunt" for r in entries),
            "stunt_cases": sum(r["event_kind"] == "stunt" for r in entries),
            "family_cases_per_region": 9,
        },
        "status_counts": dict(sorted(counts.items())),
        "by_rom": by_rom, "by_event_family": by_family,
        "historical_start_probes": {
            "authority": "hand-entered magicnumber.lua constants, no runtime spawn witness",
            "classification_counts": dict(sorted(coordinate_counts.items())),
            "unqualified_and_disagreements": [
                p for p in coordinate_probes
                if p["status"] != "nonzero_numeric_match_only"
            ],
        },
        "entries": entries,
        "limits": [
            "The 45 valid RNC streams and checkpoint resource incidence are STATIC coverage only.",
            "A native-only Dragster checkpoint transition is partial; instruction-time causality is unresolved.",
            "Independently paired original/native Zoom Zoo Circuit matches course/laps/contact and settled PPU result, but retains an unresolved one-scene-frame native result/restore phase lead; no accepted complete-course witness.",
            "Original-only archived Bowl proves settled scored Stunt result; no paired original/native timed Stunt is certified.",
            "Input-only Jumpover CIRCUIT-B rewards are partial; no paired Circuit result or scored 45-second Stunt outcome was certified.",
            "Neither PAL register homology nor identical prototype streams proves PAL runtime parity.",
            "Historical optimizer startX constants are never read by magicnumber.lua; zero does not prove a runtime spawn.",
            "A complete pass requires original menu entry, player result and event-relative independent reference comparison.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_census(
        json.loads(args.catalog.read_text(encoding="utf-8")),
        json.loads(args.evidence.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(report, indent=2) + "\n"
    if args.check:
        if not args.out.exists() or args.out.read_text(encoding="utf-8") != rendered:
            raise SystemExit("course-event census is missing/stale; regenerate")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps(report["denominators"], sort_keys=True))
    print(json.dumps(report["status_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

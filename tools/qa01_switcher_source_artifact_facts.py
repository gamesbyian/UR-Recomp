#!/usr/bin/env python3
"""Cross-reference immutable executed source-byte witnesses without replay credit.

A diagnostic snapshot extracted from an archived 2014 Snes9x/native Switcher
CI artifact, not a guest trace synthesizer or an original/native phase waiver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "UR-QA01-SWITCHER-2014-SOURCE-DIAGNOSTIC-CROSS-EVENT-0313/1"
RESULT = { "menu": 153, "in_race": 0, "track": 3, "tour_row": 0 }
BOWL_TALLY = { "menu": 47, "in_race": 60, "track": 2, "tour_row": 0 }


def verify(facts: dict, archived_pair: dict, diagnostic: dict | None = None,
           diagnostic_bytes: bytes | None = None) -> dict:
    if not isinstance(facts, dict) or facts.get("schema") != SCHEMA:
        raise ValueError("not the original 2014 source scratch-state evidence")
    exe = facts.get("execution")
    original = facts.get("original_movie_context")
    states = facts.get("source_state_examples")
    prelude = facts.get("source_foreign_active_track_zero_prelude")
    if (not isinstance(exe, dict) or not isinstance(original, dict)
            or not isinstance(states, list) or not isinstance(prelude, dict)
            or not isinstance(archived_pair, dict)):
        raise ValueError("incomplete source/ZIP and original movie provenance")
    pair_exe = archived_pair.get("execution")
    src = archived_pair.get("original_source")
    if (not isinstance(pair_exe, dict) or not isinstance(src, dict)
            or exe.get("workflow_run_id") != pair_exe.get("workflow_run_id")
            or exe.get("artifact_id") != pair_exe.get("artifact_id")
            or exe.get("artifact_zip_sha256") != pair_exe.get("artifact_zip_sha256")
            or exe.get("artifact_member") != "switcher/source/source-event-diagnostic.json"
            or exe.get("member_sha256")
               != "6e116814d848d1946880627adc241b5738b9e363d5f051e8c31b9b001bf6aab8"
            or exe.get("actual_job_conclusion") != "failure"
            or exe.get("failure_is_strict_original_native_terminal_phase_rejection") is not True
            or original.get("source_horizon_host_frame") != 22000
            or original.get("source_trace_frames") != [0, 22000]
            or original.get("source_movie_switcher_entry")
               != src.get("original_movie_course_entry_frame")
            or original.get("source_movie_switcher_result")
               != src.get("original_movie_result_frame")
            or original.get("original_source_result_menu") != 153
            or original.get("original_source_result_track") != 3
            or original.get("original_source_result_in_race") != 0
            or original.get("original_source_result_stable_end") != 17087
            or original.get("independent_source_qualification_only") is not True
            or prelude != {"start":16991,"end_inclusive":17024,"track":0,"length":34}
            or facts.get("release") != {"usa_accepted_events":0,
                                         "usa_total_events":45,"qa_credit":0}):
        raise ValueError("not the hash-attested original source run/entry/result")
    observations = {row.get("frame"): row for row in states
                    if isinstance(row, dict) and type(row.get("frame")) is int}
    if len(states) != len(observations) or set(observations) != {
            11915, 11985, 11997, 17030, 17087}:
        raise ValueError("missing or duplicated source samples")
    expected = {
        11915: (47,2,60),
        11985: (24,2,60),
        11997: (24,2,0),
        17030: (153,3,0),
        17087: (153,3,0),
    }
    for frame, (menu, track, in_race) in expected.items():
        row = observations[frame]
        if (row.get("menu") != menu or row.get("track") != track
                or row.get("raw_0313") != in_race):
            raise ValueError("changed genuine original 0313 source byte witness")
    if diagnostic is not None or diagnostic_bytes is not None:
        if diagnostic_bytes is None:
            raise ValueError("source diagnostic bytes required for digest verification")
        if (hashlib.sha256(diagnostic_bytes).hexdigest()
                != exe["member_sha256"]):
            raise ValueError("wrong original Snes9x diagnostic artifact bytes")
        reconstructed = json.loads(diagnostic_bytes)
        if diagnostic is not None and reconstructed != diagnostic:
            raise ValueError("source diagnostic object conflicts with original artifact bytes")
        if (reconstructed.get("source_trace_frames") != [0,22000]
                or reconstructed.get("original_source_horizon_host_frame") != 22000
                or reconstructed.get("original_source_horizon_observed_from_guest_dump")
                   is not True):
            raise ValueError("original source horizon not attested")
        rows = reconstructed.get("sampled_state_at_source_result_neighbors")
        if not isinstance(rows, dict):
            raise ValueError("source state samples not found in original diagnostic")
        for frame, (menu, track, in_race) in expected.items():
            actual = rows.get(str(frame))
            if (not isinstance(actual, dict)
                    or actual.get("menu") != menu
                    or actual.get("track") != track
                    or actual.get("in_race") != in_race):
                raise ValueError("source samples differ from original downloaded diagnostic")
    return {"source_observation_count":len(expected),
            "original_stunt_raw_0313_nonbinary_confirmed":True,
            "actual_original_source_horizon":22000,
            "release_usa_events_accepted":0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=Path(
        "analysis/data/qa01-switcher-2014-original-source-scratch-20261011.json"))
    parser.add_argument("--pair", type=Path, default=Path(
        "analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json"))
    parser.add_argument("--original-diagnostic", type=Path,
                        help="optional exact diagnostic JSON from archived GitHub Actions ZIP")
    args = parser.parse_args()
    facts = json.loads(args.facts.read_text(encoding="utf-8"))
    paired = json.loads(args.pair.read_text(encoding="utf-8"))
    contents = (args.original_diagnostic.read_bytes()
                if args.original_diagnostic is not None else None)
    print(json.dumps(verify(facts, paired, diagnostic_bytes=contents), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

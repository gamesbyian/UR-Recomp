#!/usr/bin/env python3
"""Source-authenticated Race/Circuit/Stunt result-phase arithmetic.

Reconcile independently executed archived source-original/native host-frame
observations, not display timing inferred from a scene screenshot. A distinct
-2-frame Race B scene-relative result lead forbids automatically applying the
-1-frame Circuit/Stunt calibration to all event families. Never accept events.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import check_two_event_result_phase as two

SCHEMA = "UR-QA01-THREE-FAMILY-RESULT-PHASE/1"
TWO = {
    "circuit-a": ("course:02", 38018081196, 11656564258,
                  1604, 1606, 6767, 6768),
    "timed-stunt": ("course:03", 38021981513, 11658009292,
                    984, 985, 4349, 4349),
}
RACE = (1079, 1081, 5783, 5783)
SWITCHER_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SWITCHER_MOVIE_SHA = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"


def positive_integer(x: object) -> bool:
    return type(x) is int and x >= 0


def phase(entry_original: int, entry_native: int,
          result_original: int, result_native: int) -> dict:
    if not all(positive_integer(x) for x in
               (entry_original, entry_native, result_original, result_native)):
        raise ValueError("missing valid measured frame")
    if result_original < entry_original or result_native < entry_native:
        raise ValueError("result precedes measured entry")
    return {
        "original_entry_host": entry_original,
        "native_entry_host": entry_native,
        "original_result_host": result_original,
        "native_result_host": result_native,
        "original_result_relative": result_original - entry_original,
        "native_result_relative": result_native - entry_native,
        "native_entry_minus_original": entry_native - entry_original,
        "native_result_minus_original": result_native - result_original,
        "native_relative_result_minus_original": (
            result_native - entry_native - (result_original - entry_original)),
    }


def summarize(two_source: dict, switcher: dict) -> dict:
    # Reuse, do not replace or weaken, the existing circuit/stunt authority.
    two.check_crosswalk(two_source)
    witnesses = []
    for row in two_source["measurements"]:
        kind = row["kind"]
        if kind not in TWO:
            raise ValueError("unknown Circuit/Stunt family")
        course, run, artifact, oe, ne, ot, nt = TWO[kind]
        if (row.get("course") != course or row.get("run") != run
                or row.get("artifact") != artifact
                or any(row.get(key) != value for key, value in (
                    ("original_entry", oe), ("native_entry", ne),
                    ("original_terminal", ot), ("native_terminal", nt)))):
            raise ValueError("archived Zoo/Bowl execution provenance or frame changed")
        witnesses.append({
            "kind": kind, "course": course, "execution_run_id": run,
            "artifact_id": artifact,
            "phase": phase(oe, ne, ot, nt),
            "independent_original_native_source_execution": True,
        })
    if not isinstance(switcher, dict) or switcher.get("schema") != (
            "UR-QA01-ORIGINAL-BALDOSA-SWITCHER-RACE-B-RESULT/1"):
        raise ValueError("not the independently executed Switcher Race B archive")
    ex = switcher.get("execution")
    origin = switcher.get("provenance")
    source = switcher.get("original_source")
    r = switcher.get("independently_observed_replay")
    release = switcher.get("release")
    if not all(isinstance(x, dict) for x in (ex, origin, source, r, release)):
        raise ValueError("missing original Switcher source, replay, or release evidence")
    expected_final = {
        "menu": 153, "in_race": 0, "p1_laps": 0, "p2_laps": 0,
        "p1_finish_gate": 1, "p1_checkpoint": 1,
    }
    expected_result_rows = [
        "SWITCHER", "COMPLETE", "PLAYER     TIME", "MIKE", "1:08.81",
        "SOMEONE", "NO TIME", "SOMEONE", "NO TIME", "SOMEONE", "NO TIME",
    ]
    if (ex.get("workflow_run_id") != 38064406315
            or ex.get("artifact_id") != 11674751560
            or ex.get("job_conclusion") != "failure"
            or origin.get("course_id") != "course:04"
            or origin.get("family") != "race-b"
            or origin.get("usa_rom_sha256") != SWITCHER_ROM_SHA
            or origin.get("original_movie_sha256") != SWITCHER_MOVIE_SHA
            or source.get("original_movie_course_entry_frame") != 12327
            or source.get("original_movie_result_frame") != 17030
            or source.get("original_only_source_event_frames_to_result") != 4703
            or source.get("original_only_terminal_prelude")
               != "switcher_34_frame_track0_terminal_prelude"
            or r.get("original_source_vs_fresh_entry_equivalent") is not True
            or r.get("reference_native_fresh_entry_equivalent") is not True
            or r.get("sampled_active_semantic_fields_equal") is not True
            or r.get("terminal_guest_relative_result_frame_matched") is not False
            or r.get("terminal_absolute_host_result_frame_matched") is not True
            or r.get("full_event_parity_admitted") is not False
            or r.get("player_one") != "MIKE"
            or r.get("player_one_time") != "1:08.81"
            or r.get("original_final_guest") != expected_final
            or r.get("native_final_guest") != expected_final
            or r.get("identical_result_screen_text_stable") != expected_result_rows
            or r.get("first_sample_disagreement", "missing") is not None
            or r.get("active_sample_count") != 28
            or r.get("active_latest_relative_frame") != 2400
            or release != {"usa_accepted_events": 0, "usa_total_events": 45,
                           "qa_credit": 0}):
        raise ValueError("Switcher genuine Race B result/source identity is unverified")
    keys = (
        "reference_entry_absolute_host_frame",
        "native_entry_absolute_host_frame",
        "reference_result_onset_absolute_host_frame",
        "native_result_onset_absolute_host_frame",
    )
    values = [r.get(k) for k in keys]
    if (values != list(RACE)
            or r.get("reference_result_guest_relative_frame") != 4704
            or r.get("native_result_guest_relative_frame") != 4702):
        raise ValueError("not the original 5783 same-host result with -2 relative offset")
    rr = phase(*values)
    # Two original Snes9x contexts do not share a course-entry host:
    # movie-reset trace (12327..17030) vs fresh calibrated replay
    # (1079..5783). The extra +1 original-relative frame is a measured
    # calibration/context difference, not a sanctioned timing waiver.
    archive_duration = (source["original_movie_result_frame"]
                        - source["original_movie_course_entry_frame"])
    if archive_duration != 4703:
        raise ValueError("original 2014 source movie duration changed")
    fresh_original_delta_from_movie = rr["original_result_relative"] - archive_duration
    fresh_native_delta_from_movie = rr["native_result_relative"] - archive_duration
    if (fresh_original_delta_from_movie != 1
            or fresh_native_delta_from_movie != -1):
        raise ValueError("Switcher three-context relative-frame gap changed")
    witnesses.append({
        "kind": "race-b", "course": "course:04",
        "execution_run_id": ex["workflow_run_id"],
        "artifact_id": ex["artifact_id"],
        "phase": rr,
        "independent_original_native_source_execution": True,
    })
    order = {"circuit-a": 0, "timed-stunt": 1, "race-b": 2}
    witnesses.sort(key=lambda row: order[row["kind"]])
    leads = {row["kind"]: row["phase"]["native_relative_result_minus_original"]
             for row in witnesses}
    if leads != {"circuit-a": -1, "timed-stunt": -1, "race-b": -2}:
        raise ValueError("the three independently observed phase classes changed")
    return {
        "schema": SCHEMA,
        "archived_source_qualified_event_family_count": 3,
        "witnesses": witnesses,
        "native_minus_original_scene_relative_terminal_by_family": leads,
        "switcher_three_context_phase": {
            "2014_source_movie_relative_frames": archive_duration,
            "fresh_original_snes9x_relative_frames": rr["original_result_relative"],
            "fresh_native_baldosa_relative_frames": rr["native_result_relative"],
            "fresh_original_minus_source_movie_relative_frames": fresh_original_delta_from_movie,
            "fresh_native_minus_source_movie_relative_frames": fresh_native_delta_from_movie,
            "original_source_movie_and_fresh_replay_have_different_boot_contexts": True,
        },
        "original_reference_vs_source_movie_plus_one_frame_is_observed_not_normalized": True,
        "single_universal_scene_relative_frame_offset_disproven": True,
        "common_absolute_host_terminal_frame_alone_does_not_prove_parity": True,
        "original_movie_frame_is_not_fresh_guest_host_frame": True,
        "guest_cpu_instruction_phase_equivalence_proven": False,
        "source_critical_timing_cause_established": False,
        "retroactive_retiming_or_result_phase_waiver_permitted": False,
        "first_completed_usa_course_accepted": False,
        "official_usa_complete_event_count": 0,
        "official_usa_course_denominator": 45,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--circuit-stunt", type=Path, default=Path(
        "analysis/data/two-event-original-native-result-phase-crosswalk-20261009.json"))
    ap.add_argument("--switcher", type=Path, default=Path(
        "analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json"))
    args = ap.parse_args()
    result = summarize(json.loads(args.circuit_stunt.read_text(encoding="utf-8")),
                       json.loads(args.switcher.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

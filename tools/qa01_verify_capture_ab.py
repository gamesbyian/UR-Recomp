#!/usr/bin/env python3
"""QA01 independently compare actual original/native capture-off/on replays.

Runs no emulator. Requires two authentic source-bound complete-event producer
reports plus raw retained capture bytes. Does not turn matched checkpoint
semantics into proof of intervening guest instructions or Windows persistence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import qa01_frame_capture_replay as guest_receipts
import qa01_frame_fingerprint as frames
import qa01_verify_frame_capture as independent


SCHEMA = "ur-qa01-capture-ab-noninterference-review/1"
CONTROL = "ur-qa01-capture-ab-replay-control/1"

# Named existing observations. A new producer field must be consciously
# reviewed instead of blanket-ignoring its significance as 'debug metadata'.
SEMANTIC_FIELDS = (
    "original_source_event", "original_source_vs_fresh_entry",
    "reference_entry", "native_entry", "native_frame_shift",
    "relative_sample_frames", "comparison", "tally_anchored_guest_phase",
    "zoo_terminal_host_phase", "zoo_race_mesh",
    "switcher_same_host_penultimate", "switcher_same_host_full_memory_offsets",
    "source_terminal_followthrough", "zoo_next_bowl_handoff",
    "bowl_next_switcher_handoff", "bowl_source_movie_three_guest_memory",
    "dragster_next_zoo_handoff", "reference", "native",
)
IDENTITIES = (
    "course_id", "name", "family", "native_backend", "rom_sha256",
    "original_movie_sha256", "source_sram_sha256", "native_executable_sha256",
    "reference_core_sha256", "original_movie_window_sha256",
)
SAME_CONTROLS = (
    "repository_source_sha", "controller_movie_window_sha256",
    "reference_supplied_input_sha256", "native_supplied_input_sha256",
    "reference_supplied_input_bytes", "native_supplied_input_bytes",
)


def must(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha(path: Path) -> str:
    must(path.is_file() and not path.is_symlink(),
         "missing or symlinked original/native log or report: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(baseline: dict, captured: dict, fingerprints: dict,
          retained_root: Path, fingerprint_sha256: str,
          guest_logs: dict[str, Path] | None = None) -> dict:
    for role, report in (("baseline", baseline), ("captured", captured)):
        must(type(report) is dict and report.get("schema_version") == 1 and
             report.get("admission") ==
             "investigative candidate; not a release-ledger pass",
             role + " invalid source producer schema/acceptance scope")
        must(all(key in report for key in IDENTITIES + SEMANTIC_FIELDS),
             role + " missing required original/native source semantics")
    for field in IDENTITIES:
        must(baseline[field] == captured[field],
             "source/controller/binary identity mismatch: " + field)
    for field in SEMANTIC_FIELDS:
        must(baseline[field] == captured[field],
             "capture perturbed an existing observed gameplay field: " + field)
    controls = [x.get("qa01_capture_ab_control") for x in (baseline, captured)]
    for role, control in zip(("baseline", "captured"), controls):
        must(type(control) is dict and control.get("schema") == CONTROL
             and all(field in control for field in SAME_CONTROLS),
             role + " missing exact supplied-controller A/B binding")
        must(control.get("cpu_joypad_reads_proven") is False and
             control.get("full_event_accepted") is False,
             role + " attempted unsupported CPU/acceptance attestation")
        must(all(type(control.get(key)) is int and control[key] >= 0
                 for key in ("reference_supplied_input_bytes",
                             "native_supplied_input_bytes")),
             role + " invalid supplied input lengths")
        for key in ("reference_replay_wall_seconds",
                    "native_replay_wall_seconds"):
            v = control.get(key)
            must(type(v) in (float, int) and math.isfinite(v) and v > 0,
                 role + " invalid measured guest runtime " + key)
    for field in SAME_CONTROLS:
        must(controls[0][field] == controls[1][field],
             "capture changed actual input/source authority: " + field)
    must(controls[0].get("capturing_continuous_frames") is False
         and controls[1].get("capturing_continuous_frames") is True
         and baseline.get("qa01_continuous_memory_capture") is None,
         "mislabelled baseline or absent capture treatment")
    witness = captured.get("qa01_continuous_memory_capture")
    must(type(witness) is dict and
         witness.get("accepted_complete_USA_events") == 0 and
         witness.get("actual_cpu_joypad_poll_consumption_proven") is False and
         witness.get("capture_overhead_vs_identical_no-capture_control_measured") is False and
         witness.get("fingerprints_sha256") == fingerprint_sha256 and
         witness.get("native_binary_sha256") == captured["native_executable_sha256"] and
         witness.get("reference_core_sha256") == captured["reference_core_sha256"],
         "capture fingerprint file/binaries unbound or unsupported claim")
    must(witness.get("original_controller_supplied_file_sha256") ==
         controls[1]["reference_supplied_input_sha256"] and
         witness.get("native_controller_supplied_file_sha256") ==
         controls[1]["native_supplied_input_sha256"] and
         witness.get("source_controller_window_sha256") ==
         captured["original_movie_window_sha256"],
         "capture source/input file hashes disagree")
    identity = fingerprints.get("source_identity")
    must(type(identity) is dict and
         identity.get("source_sha") == controls[1]["repository_source_sha"] and
         identity.get("rom_sha256") == captured["rom_sha256"] and
         identity.get("movie_sha256") == captured["original_movie_sha256"] and
         identity.get("input_sha256") == captured["original_movie_window_sha256"] and
         identity.get("original_frame_origin") == captured["reference_entry"] and
         identity.get("native_frame_origin") == captured["native_entry"] and
         identity.get("masked_wram_bytes") == identity.get("masked_sram_bytes") == 0,
         "full memory witness and actual source/input/frame-origin identity disagree")
    # This consumer independently recomputes the retained decision bytes.
    verified = independent.verify(fingerprints, retained_root)
    must(verified["complete_USA_events_accepted"] == 0,
         "independent frame verifier wrongly awarded event")
    coverage = fingerprints["coverage"]
    metrics = witness.get("metrics")
    must(type(metrics) is dict and
         metrics.get("window") == {
             "start": coverage["start"], "end": coverage["end"],
             "count": coverage["required_frames"]} and
         metrics.get("original_guest_acknowledged_frames") ==
         coverage["required_frames"] and
         metrics.get("native_guest_acknowledged_frames") ==
         coverage["required_frames"],
         "source/native frame ACKs inconsistent with audited coverage")
    # Once genuine log files have been preserved, re-open all four raw
    # baseline/capture host logs and independently bind their SHA256 hashes
    # to their own producer controls. Merely trusting the producer's '9 ACKs'
    # counter does NOT independently establish nine successful guest dumps.
    actual_logs_reopened = False
    if guest_logs is not None:
        must(type(guest_logs) is dict and set(guest_logs) ==
             {"baseline_original", "baseline_native",
              "captured_original", "captured_native"},
             "incomplete original/native capture-on/off raw guest logs")
        for index, mode in enumerate(("baseline", "captured")):
            control = controls[index]
            for guest, prefix in (("original", "reference"), ("native", "native")):
                path = guest_logs[mode + "_" + guest]
                expected_sha = control[prefix + "_guest_log_sha256"]
                must(type(expected_sha) is str and
                     frames.HEX64.fullmatch(expected_sha) and
                     sha(path) == expected_sha,
                     mode + "/" + guest + " actual guest log hash changed")
        must(
            sha(guest_logs["captured_original"]) ==
            witness.get("reference_guest_acknowledgment_log_sha256") and
            sha(guest_logs["captured_native"]) ==
            witness.get("native_guest_acknowledgment_log_sha256"),
            "captured actual frame-ACK log does not match producer binary receipt")
        required = set(range(coverage["start"], coverage["end"] + 1))
        for guest, origin_field in (("original", "original_frame_origin"),
                                    ("native", "native_frame_origin")):
            observed = guest_receipts.acknowledgments(
                guest_logs["captured_" + guest], "qa01-frame-", 6, guest)
            must(set(observed) == required and
                 all(observed[frame] ==
                     identity[origin_field] + frame for frame in required),
                 guest + " actual successful frame-dump sequence incomplete or shifted")
        actual_logs_reopened = True

    timing = {}
    for side in ("reference", "native"):
        base = controls[0][side + "_replay_wall_seconds"]
        instrumented = controls[1][side + "_replay_wall_seconds"]
        timing[side] = {
            "baseline_seconds": base,
            "captured_seconds": instrumented,
            "additional_seconds": round(instrumented - base, 6),
            "relative_overhead_pct": round((instrumented/base - 1)*100, 3),
        }
    return {
        "schema": SCHEMA,
        "same_source_controller_and_binaries": True,
        "same_supplied_original_native_input_bytes_digest": True,
        "existing_semantic_observations_unchanged": True,
        "raw_differences_retained_and_independently_rechecked": True,
        "actual_complete_consecutive_frame_acknowledgments": coverage["required_frames"],
        "captured_successful_guest_acknowledgment_logs_independently_reopened":
            actual_logs_reopened,
        "four_original_native_on_off_guest_log_hashes_rechecked":
            actual_logs_reopened,
        "bounded_capture_start": coverage["start"],
        "bounded_capture_end": coverage["end"],
        "time": timing,
        "retained_evidence_bytes": metrics.get("retained_full_raw_image_bytes"),
        "evidence_phase_claim": "actual script-dump observation only",
        "actual_input_CPU_read_trace_proven": False,
        "full_race_or_Windows_persistence_proven": False,
        "admitted_usa_events": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("baseline", "captured", "fingerprints", "retained-raw",
                "baseline-original-log", "baseline-native-log",
                "captured-original-log", "captured-native-log", "output"):
        p.add_argument("--" + arg, type=Path, required=True)
    a = p.parse_args()
    must(not a.output.exists(), "refuse overwrite of A/B independent receipt")
    result = audit(json.loads(a.baseline.read_text()),
                   json.loads(a.captured.read_text()),
                   json.loads(a.fingerprints.read_text()),
                   a.retained_raw, sha(a.fingerprints),
                   guest_logs={
                       "baseline_original": a.baseline_original_log,
                       "baseline_native": a.baseline_native_log,
                       "captured_original": a.captured_original_log,
                       "captured_native": a.captured_native_log,
                   })
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("QA01 bounded source and guest capture-on/off A/B validated; 0/45")


if __name__ == "__main__":
    main()

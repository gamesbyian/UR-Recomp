#!/usr/bin/env python3
"""Fail-closed QA01 research-factory readiness gate (no emulator or CI dispatch).

Consumes already generated diagnostics and explicit independently signed-off
producer attestations. A green verdict authorizes a *bounded research pilot*
only, not a full course, release gate or large factory escalation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

import qa01_causal_window as causal_verifier
import qa01_verify_frame_capture as frame_verifier

SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
SCHEMA = "ur-qa01-research-factory-preflight/1"
REQUIRED_ATTESTATIONS = (
    "authentic_source_binary_verified",
    "authentic_native_binary_verified",
    "actual_controller_consumption_verified_both_guests",
    "real_guest_frame_acknowledgments_verified",
    "original_native_sample_phase_independently_qualified",
    "instrumented_vs_uninstrumented_noninterference_verified",
    "unaltered_input_and_independent_clock_domains",
    "unmasked_raw_bytes_independently_preserved",
)


def assert_valid(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def load(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    result = json.loads(raw)
    assert_valid(type(result) is dict, "expected JSON object: " + str(path))
    return result, hashlib.sha256(raw).hexdigest()


def evaluate(attestation: dict, causal: dict | None, frames: dict | None,
             independent: dict | None, input_hashes: dict[str, str]) -> dict:
    assert_valid(attestation.get("schema") == SCHEMA, "invalid preflight attestation schema")
    assert_valid(type(attestation.get("source_sha")) is str and
                 SOURCE.fullmatch(attestation["source_sha"]), "missing exact source")
    for key in ("rom_sha256", "movie_sha256", "input_sha256"):
        assert_valid(type(attestation.get(key)) is str and
                     SHA.fullmatch(attestation[key]), "missing exact identity: " + key)
    checks = attestation.get("checks")
    assert_valid(type(checks) is dict, "missing independent attestation")
    for key in REQUIRED_ATTESTATIONS:
        assert_valid(type(checks.get(key)) is bool, "missing explicit check: " + key)
    assert_valid(all(type(v) is str and SHA.fullmatch(v)
                     for v in input_hashes.values()), "invalid input artifact digest")
    if causal is not None:
        assert_valid(causal.get("schema") == "ur-qa01-causal-window-readonly-report/1",
                     "invalid causal report")
        assert_valid(causal.get("source_sha") == attestation["source_sha"],
                     "causal source mismatch")
        assert_valid(causal.get("accepted_complete_USA_events") == 0 and
                     causal.get("complete_gameplay_or_instruction_equivalence_proven") is False,
                     "causal report claims unsupported event proof")
        expected_input = {key: attestation[key] for key in (
            "source_sha", "rom_sha256", "movie_sha256", "input_sha256")}
        assert_valid(causal.get("input_identity") == expected_input and
                     all(type(causal.get(key)) is str and SHA.fullmatch(causal[key])
                         for key in ("original_event_sha256", "native_event_sha256")),
                     "causal original/native event or immutable ROM/movie/input mismatch")
        assert_valid(type(causal.get("addresses")) is list and causal["addresses"],
                     "causal report missing address decisions")
        for item in causal["addresses"]:
            assert_valid(type(item) is dict and item.get("causal_equivalence_proven") is False
                         and type(item.get("checkpoint_differs")) is bool,
                         "causal report lacks unpromoted difference witness")
    if frames is not None:
        assert_valid(frames.get("schema") == "ur-qa01-frame-fingerprint/1",
                     "invalid frame digest report")
        identity = frames.get("source_identity")
        assert_valid(type(identity) is dict and
                     all(identity.get(k) == attestation[k]
                         for k in ("source_sha", "rom_sha256", "movie_sha256", "input_sha256")),
                     "frame report wrong immutable source/input identity")
        assert_valid(identity.get("masked_wram_bytes") == 0 and
                     identity.get("masked_sram_bytes") == 0, "masked frame population")
        extent = frames.get("coverage")
        assert_valid(type(extent) is dict and
                     extent.get("continuous_at_declared_frame_phase") is True and
                     extent.get("between_frame_opcode_semantics_proven") is False and
                     type(extent.get("required_frames")) is int and
                     extent["required_frames"] >= 1 and
                     extent.get("observed_original_frames") == extent["required_frames"] and
                     extent.get("observed_native_frames") == extent["required_frames"],
                     "incomplete or misreported source/native frame coverage")
        assert_valid(frames.get("accepted_USA_events") == 0,
                     "diagnostic frame producer asserted release credit")
    if independent is not None:
        assert_valid(independent.get("schema") == "ur-qa01-independent-frame-capture-audit/1"
                     and independent.get("complete_USA_events_accepted") == 0
                     and independent.get("source_sha") == attestation["source_sha"]
                     and independent.get("source_memory_bytes_independently_recomputed_for_retained_frames") is True,
                     "missing independent raw image byte verification")
    known = {
        "causal_report": causal is not None,
        "frame_report": frames is not None,
        "independent_raw_report": independent is not None,
        **checks,
    }
    reasons = [name for name in REQUIRED_ATTESTATIONS if checks[name] is not True]
    if causal is None: reasons.append("missing_executed_causal_report")
    if frames is None: reasons.append("missing_contiguous_frame_report")
    if independent is None: reasons.append("missing_independent_raw_byte_verifier")
    if causal is not None and not any(r["checkpoint_differs"] for r in causal["addresses"]):
        reasons.append("no_observed_mismatch_for_a_causal_discriminator")
    return {
        "schema": "ur-qa01-research-factory-preflight-result/1",
        "source_sha": attestation["source_sha"],
        "artifact_sha256": input_hashes,
        "readiness": "bounded_pilot_ready" if not reasons else "hold",
        "missing_or_negative_conditions": reasons,
        "allowed_next_case_count": 10 if not reasons else 0,
        "automatic_dispatch_authorized": False,
        "one_thousand_or_more_cases_authorized": False,
        "independent_USA_events_accepted": 0,
        "release_QA_gates_awarded": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--attestation", type=Path, required=True)
    ap.add_argument("--causal-report", type=Path)
    ap.add_argument("--frame-report", type=Path)
    ap.add_argument("--independent-raw-report", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    attestation, ah = load(args.attestation)
    provided = [("causal_report", args.causal_report),
                ("frame_report", args.frame_report),
                ("independent_raw_report", args.independent_raw_report)]
    loaded = [(load(p) if p is not None else (None, None)) for _, p in provided]
    hashes = {"attestation": ah}
    hashes.update({label: sha for (label, _), (_, sha) in zip(provided, loaded)
                   if sha is not None})
    verdict = evaluate(attestation, *(x for x, _ in loaded), hashes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(verdict["readiness"], "-", ", ".join(verdict["missing_or_negative_conditions"]) or
          "bounded pilot allowed; no automatic dispatch")
    if verdict["readiness"] != "bounded_pilot_ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

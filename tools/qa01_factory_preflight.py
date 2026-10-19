#!/usr/bin/env python3
"""Fail-closed QA01 factory readiness gate; *no* experiment dispatch.

A source-bound manual review must pin the exact three diagnostic reports. For
positive readiness, independently reopen the source/native raw captures, verify
all retained bytes and match the causal checkpoint to that very frame/phase.
This remains a research preflight, not original-guest or release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import qa01_verify_frame_capture as raw_verifier
import qa01_causal_window as causal_consumer

SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
ADDRESS = re.compile(r"7[EF]:[0-9A-F]{4}\Z")
SCHEMA = "ur-qa01-research-factory-preflight/2"
LEGACY_SCHEMA = "ur-qa01-research-factory-preflight/1"
REPORTS = ("causal_report", "frame_report", "independent_raw_report")
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
    assert_valid(path.is_file() and not path.is_symlink(),
                 "missing/symlinked evidence JSON: " + str(path))
    raw = path.read_bytes()
    result = json.loads(raw)
    assert_valid(type(result) is dict, "expected JSON object: " + str(path))
    return result, hashlib.sha256(raw).hexdigest()


def causal_scope(causal: dict, frames: dict, raw_root: Path) -> dict:
    """Verify real original/native checkpoint *bytes* at the common phase.

    Independent clocks are preserved: only the semantically declared frame
    index is used here. The producer must separately prove genuine guest frame
    registration; this lookup alone cannot do that.
    """
    identity, coverage = frames["source_identity"], frames["coverage"]
    phase = identity.get("observation_phase")
    assert_valid(type(phase) is str and bool(phase) and
                 causal.get("observation_phase") == phase,
                 "causal/frame observation phase differs")
    a, b = causal.get("original_window"), causal.get("native_window")
    assert_valid(type(a) is dict and type(b) is dict, "missing actual causal windows")
    assert_valid(all(w.get("complete") is True and w.get("overflow") is False
                     and w.get("phase") == phase for w in (a, b)),
                 "incomplete/overflowed causal producer or inconsistent phase")
    frame = a.get("checkpoint")
    assert_valid(type(frame) is int and b.get("checkpoint") == frame
                 and type(coverage.get("start")) is int
                 and type(coverage.get("end")) is int
                 and coverage["start"] <= frame <= coverage["end"],
                 "causal checkpoint not in the real frame capture interval")
    assert_valid(a.get("addresses") == b.get("addresses") and
                 type(a.get("addresses")) is list and a["addresses"],
                 "unmatched original/native causal address population")
    assert_valid(all(type(causal.get(k)) is str and SHA.fullmatch(causal[k])
                     for k in ("original_event_sha256", "native_event_sha256")),
                 "missing hashed actually executed guest events")
    samples = causal.get("addresses")
    assert_valid(type(samples) is list and
                 len(samples) == len(a["addresses"]) and
                 len(set(a["addresses"])) == len(samples),
                 "incomplete or duplicated causal addresses")
    retained = {}
    for guest in ("original", "native"):
        name = f"{guest}-relative-{frame:06d}-wram.bin"
        path = raw_root / name
        # The independent verifier already checked this member's length,
        # SHA256 and raw-per-frame pairing against the producer report.
        assert_valid(path.is_file() and not path.is_symlink(),
                     "causal checkpoint raw WRAM not retained: " + name)
        retained[guest] = path.read_bytes()
        assert_valid(len(retained[guest]) == 131072, "wrong causal raw WRAM length")
    different = 0
    for address, sample in zip(a["addresses"], samples):
        assert_valid(type(address) is str and bool(ADDRESS.fullmatch(address))
                     and type(sample) is dict and sample.get("address") == address
                     and sample.get("causal_equivalence_proven") is False,
                     "invalid causal source address/witness identity")
        offset = (int(address[:2], 16) - 0x7E) * 65536 + int(address[3:], 16)
        original, native = sample.get("original"), sample.get("native")
        assert_valid(type(original) is dict and type(native) is dict,
                     "missing actual guest checkpoint bytes")
        actual = retained["original"][offset], retained["native"][offset]
        assert_valid(original.get("checkpoint_byte") == actual[0]
                     and native.get("checkpoint_byte") == actual[1],
                     "causal byte is not from the retained original/native WRAM")
        changed = actual[0] != actual[1]
        assert_valid(sample.get("checkpoint_differs") is changed,
                     "causal difference flag disagrees with actual WRAM")
        different += int(changed)
    row = frames.get("rows")
    assert_valid(type(row) is list and len(row) == coverage["required_frames"],
                 "missing actual raw frame population")
    audit = row[frame - coverage["start"]]
    assert_valid(audit.get("relative_frame") == frame
                 and type(audit.get("types")) is dict
                 and type(audit["types"].get("wram")) is dict
                 and audit["types"]["wram"].get("unmasked_differing_byte_count", -1) >= different,
                 "causal mismatch exceeds full-WRAM observed byte difference")
    return {"relative_frame": frame, "observation_phase": phase,
            "causal_addresses_reopened": len(samples),
            "causal_differences_recomputed_from_raw": different,
            "independent_clock_domains_remain_unaligned": True}


def evaluate(attestation: dict, causal: dict | None, frames: dict | None,
             independent: dict | None, input_hashes: dict[str, str],
             *, raw_root: Path | None = None,
             original_event_bytes: bytes | None = None,
             native_event_bytes: bytes | None = None) -> dict:
    assert_valid(attestation.get("schema") in (SCHEMA, LEGACY_SCHEMA),
                 "invalid preflight attestation schema")
    assert_valid(type(attestation.get("source_sha")) is str and
                 SOURCE.fullmatch(attestation["source_sha"]), "missing exact source")
    for key in ("rom_sha256", "movie_sha256", "input_sha256"):
        assert_valid(type(attestation.get(key)) is str and
                     SHA.fullmatch(attestation[key]), "missing exact identity: " + key)
    checks = attestation.get("checks")
    assert_valid(type(checks) is dict, "missing independent attestation")
    for key in REQUIRED_ATTESTATIONS:
        assert_valid(type(checks.get(key)) is bool, "missing explicit check: " + key)
    assert_valid(type(input_hashes) is dict and
                 all(type(v) is str and SHA.fullmatch(v)
                     for v in input_hashes.values()), "invalid input artifact digest")
    pins = attestation.get("evidence_sha256")
    reasons = [name for name in REQUIRED_ATTESTATIONS if checks[name] is not True]
    if attestation["schema"] != SCHEMA:
        reasons.append("legacy_attestation_lacks_report_pins")
    if type(pins) is not dict or set(pins) != set(REPORTS) or not all(
            type(pins[k]) is str and SHA.fullmatch(pins[k]) for k in REPORTS):
        reasons.append("missing_independent_report_digest_pins")
    elif not all(input_hashes.get(k) is not None for k in REPORTS):
        reasons.append("missing_actual_report_file_sha256")
    else:
        for name in REPORTS:
            assert_valid(pins[name] == input_hashes[name],
                         "independent review digest pin disagrees: " + name)
    if causal is None:
        reasons.append("missing_executed_causal_report")
    else:
        assert_valid(causal.get("schema") == "ur-qa01-causal-window-readonly-report/1"
                     and causal.get("source_sha") == attestation["source_sha"],
                     "wrong causal source/schema")
        assert_valid(causal.get("accepted_complete_USA_events") == 0 and
                     causal.get("complete_gameplay_or_instruction_equivalence_proven") is False,
                     "causal report claims unsupported event proof")
        assert_valid(type(causal.get("addresses")) is list and causal["addresses"],
                     "causal report missing address observations")
        if not any(x.get("checkpoint_differs") is True for x in causal["addresses"]):
            reasons.append("no_observed_mismatch_for_a_causal_discriminator")
    if frames is None:
        reasons.append("missing_contiguous_frame_report")
    else:
        assert_valid(frames.get("schema") == "ur-qa01-frame-fingerprint/1",
                     "invalid frame digest report")
        identity = frames.get("source_identity")
        assert_valid(type(identity) is dict and
                     all(identity.get(k) == attestation[k] for k in
                         ("source_sha", "rom_sha256", "movie_sha256", "input_sha256")),
                     "frame report wrong immutable source/input identity")
        assert_valid(identity.get("masked_wram_bytes") == 0 and
                     identity.get("masked_sram_bytes") == 0, "masked frame population")
        coverage = frames.get("coverage")
        assert_valid(type(coverage) is dict and
                     coverage.get("continuous_at_declared_frame_phase") is True
                     and coverage.get("between_frame_opcode_semantics_proven") is False
                     and type(coverage.get("required_frames")) is int
                     and coverage["required_frames"] >= 1
                     and coverage.get("observed_original_frames") == coverage["required_frames"]
                     and coverage.get("observed_native_frames") == coverage["required_frames"],
                     "incomplete or misreported source/native frame coverage")
        assert_valid(frames.get("accepted_USA_events") == 0,
                     "diagnostic frame producer asserted release credit")
    if independent is None:
        reasons.append("missing_independent_raw_byte_verifier")
    else:
        assert_valid(independent.get("schema") == "ur-qa01-independent-frame-capture-audit/1"
                     and independent.get("complete_USA_events_accepted") == 0
                     and independent.get("source_sha") == attestation["source_sha"]
                     and independent.get("source_memory_bytes_independently_recomputed_for_retained_frames") is True
                     and independent.get("whole_race_opcode_equivalence_proven") is False
                     and independent.get("actual_guest_frame_acknowledgments_verified") is False
                     and independent.get("original_input_consumption_verified") is False,
                     "invalid/overclaimed independent raw-image audit")
    if original_event_bytes is None or native_event_bytes is None:
        reasons.append("missing_actual_original_native_event_payloads")
    elif causal is not None:
        # The caller-provided artifact fingerprints must match the exact
        # event bytes consumed, not a previous read of a mutable file.
        for guest, raw in (("original", original_event_bytes),
                           ("native", native_event_bytes)):
            assert_valid(input_hashes.get(guest + "_event_payload") ==
                         hashlib.sha256(raw).hexdigest(),
                         "actual " + guest + " event payload digest changed")
        # Re-execute the merged read-only causal parser over actual source and
        # native event payload bytes, not an unverified human-edited report.
        rederived = causal_consumer.assess(
            json.loads(original_event_bytes), json.loads(native_event_bytes),
            original_event_bytes, native_event_bytes)
        assert_valid(rederived == causal,
                     "causal report does not reproduce from actual event payloads")
    if raw_root is None:
        reasons.append("missing_retained_raw_dir_for_independent_reopen")
    crosscheck = None
    if causal is not None and frames is not None:
        # Phase/window inconsistencies are always fatal even if other evidence
        # remains HOLD, because this is not a valid comparable experiment.
        phase = frames["source_identity"].get("observation_phase")
        assert_valid(causal.get("observation_phase") == phase
                     and causal.get("original_window", {}).get("phase") == phase
                     and causal.get("native_window", {}).get("phase") == phase,
                     "cross-report observation phase differs")
    if raw_root is not None and frames is not None:
        # Re-run the actual byte verifier, do not trust someone else's green
        # boolean or a separately copied independent report.
        fresh = raw_verifier.verify(frames, raw_root)
        if independent is not None:
            for k in ("schema", "source_sha", "verified_raw_frames",
                      "verified_raw_files", "verified_differing_byte_occurrences",
                      "digest_only_equal_frames_not_independently_reopened",
                      "source_memory_bytes_independently_recomputed_for_retained_frames"):
                assert_valid(independent.get(k) == fresh[k],
                             "independent raw report does not describe provided frames: " + k)
        if causal is not None:
            crosscheck = causal_scope(causal, frames, raw_root)
    return {
        "schema": "ur-qa01-research-factory-preflight-result/2",
        "source_sha": attestation["source_sha"],
        "artifact_sha256": input_hashes,
        "readiness": "bounded_pilot_ready" if not reasons else "hold",
        "missing_or_negative_conditions": reasons,
        "raw_checkpoint_crosscheck": crosscheck,
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
    ap.add_argument("--original-events", type=Path,
                    help="actual original executed-bus JSON; required for pilot readiness")
    ap.add_argument("--native-events", type=Path,
                    help="actual native executed-bus JSON; required for pilot readiness")
    ap.add_argument("--retained-raw", type=Path,
                    help="source/native raw image directory; required to authorize a pilot")
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
    events = {}
    for guest, path in (("original", args.original_events),
                        ("native", args.native_events)):
        if path is not None:
            assert_valid(path.is_file() and not path.is_symlink(),
                         "missing/symlinked event payload: " + str(path))
            raw = path.read_bytes()
            assert_valid(type(json.loads(raw)) is dict,
                         "event payload must be an object")
            hashes[guest + "_event_payload"] = hashlib.sha256(raw).hexdigest()
            events[guest] = raw
    verdict = evaluate(attestation, *(x for x, _ in loaded), hashes,
                       raw_root=args.retained_raw,
                       original_event_bytes=events.get("original"),
                       native_event_bytes=events.get("native"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(verdict["readiness"], "-", ", ".join(verdict["missing_or_negative_conditions"]) or
          "bounded pilot allowed; no automatic dispatch")
    if verdict["readiness"] != "bounded_pilot_ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

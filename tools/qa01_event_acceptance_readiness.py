#!/usr/bin/env python3
"""Read-only QA-01 readiness audit of an existing classified campaign case.

This is not a new gameplay oracle, full-event certificate, or ledger writer.
Synthetic tests never count as executed USA evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "ur-qa01-independent-event-readiness/1"
HEX = re.compile(r"[0-9a-f]{64}\Z")
CASES = {"zoom-zoo": "course:02", "bowl": "course:03", "switcher": "course:04"}
FOLLOW = {"not_observed", "sampled_named_divergence", "six_sample_triplet_named_agreement"}
HANDOFF = {"not_observed", "sampled_progression_divergence", "bounded_source_handoff_agreement"}


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def assess(row: dict) -> dict:
    """Classify the bounded evidence and expose what it cannot certify. Always HOLD."""
    require(isinstance(row, dict) and row.get("schema") == "ur-qa01-event-campaign/1",
            "expected existing QA-01 classified case receipt")
    case = row.get("case")
    require(case in CASES and row.get("course_id") == CASES[case], "wrong case/course")
    require(row.get("disposition") in {"strict_candidate", "strict_divergence", "producer_error"},
            "unexpected campaign outcome")
    require(type(row.get("release_credit")) is int and row["release_credit"] == 0,
            "receipt attempts event/release credit")
    require(isinstance(row.get("source_sha"), str) and
            re.fullmatch(r"[0-9a-f]{40}", row["source_sha"]) is not None,
            "unbound source revision")
    require(isinstance(row.get("plan_sha256"), str) and HEX.fullmatch(row["plan_sha256"]),
            "unbound campaign plan")
    result = {
        "schema": SCHEMA, "case": case, "course_id": row["course_id"],
        "source_sha": row["source_sha"], "plan_sha256": row["plan_sha256"],
        "campaign_disposition": row["disposition"],
        "event_adjudication": "HOLD", "accepted_event_credit": 0,
        "review_scope": "classified original/native bounded evidence; NOT shipping Windows",
        "bounded_findings": {}, "blocking_requirements": [],
    }
    block, bounded = result["blocking_requirements"], result["bounded_findings"]
    if row["disposition"] == "producer_error":
        bounded["producer"] = "error"
        block.append("producer_error_requires_genuine_source_bound_replay")
    else:
        ev = row.get("evidence")
        require(isinstance(ev, dict), "missing classified evidence")
        for key in ("producer_sha256", "rom_sha256", "movie_sha256", "core_sha256",
                    "native_sha256", "input_sha256", "source_sram_sha256",
                    "original_movie_window_sha256", "reference_script_sha256"):
            require(isinstance(ev.get(key), str) and HEX.fullmatch(ev[key]),
                    "missing/invalid classified hash " + key)
        strict = row["disposition"] == "strict_candidate"
        require(ev.get("strict_candidate") is strict and
                type(ev.get("terminal_frame_matched")) is bool,
                "contradictory strict candidate claims")
        audit = ev.get("strict_producer_gate_audit")
        require(isinstance(audit, dict) and isinstance(audit.get("gates"), dict) and
                audit.get("recomputed_candidate") is strict and
                all(type(v) is bool for v in audit["gates"].values()) and
                all(audit["gates"].values()) is strict,
                "contradictory strict producer-gate audit")
        phase = ev.get("source_original_movie_vs_fresh_guest_result_phase")
        require(isinstance(phase, dict) and
                type(phase.get("three_relative_durations_equal")) is bool and
                phase.get("continuous_original_to_fresh_equivalence_proven") is False and
                phase.get("independent_original_movie_and_fresh_guest_clocks_not_rebased") is True and
                type(phase.get("release_credit")) is int and phase["release_credit"] == 0,
                "contradictory three-clock source phase scope")
        post = ev.get("post_result_bounded")
        handoff = ev.get("next_bowl_bounded")
        require(isinstance(post, dict) and post.get("status") in FOLLOW and
                type(post.get("release_credit")) is int and post["release_credit"] == 0,
                "invalid post-result scope")
        require(isinstance(handoff, dict) and handoff.get("status") in HANDOFF and
                type(handoff.get("release_credit")) is int and handoff["release_credit"] == 0,
                "invalid handoff scope")
        require(case == "zoom-zoo" or handoff["status"] == "not_observed",
                "non-Zoo next-Bowl handoff")
        bounded.update({
            "strict_onset": "matched" if strict else "divergent",
            "archived_movie_vs_both_fresh_durations": (
                "matched_but_not_continuous" if phase["three_relative_durations_equal"]
                else "divergent"),
            "post_result_named_samples": post["status"],
            "next_course_samples": handoff["status"],
        })
        if not strict:
            block.append("strict_original_native_result_or_active_state_divergence")
        if not phase["three_relative_durations_equal"]:
            block.append("archived_movie_fresh_guest_result_clock_disagreement")
        if post["status"] != "six_sample_triplet_named_agreement":
            block.append("post_result_continuation_not_fully_matched_in_sampled_window")
        if handoff["status"] != "bounded_source_handoff_agreement":
            block.append("next_course_entry_and_persistence_not_jointly_observed")
        else:
            require(handoff.get("fresh_original_entry_offset") == 267 and
                    handoff.get("fresh_native_entry_offset") == 267 and
                    handoff.get("source_entry_offset") == 267 and
                    handoff.get("all_sampled_sram_pairs_equal") is True and
                    handoff.get("all_sampled_named_triplets_equal") is True and
                    handoff.get("unsampled_frames_or_windows_disk_persistence_proven") is False,
                    "contradictory bounded Zoo-to-Bowl report")
        offsets = handoff.get("raw_wram_differing_sample_offsets")
        count = handoff.get("raw_wram_differing_byte_occurrences")
        require(isinstance(offsets, list) and all(type(x) is int for x in offsets) and
                offsets == sorted(set(offsets)) and
                type(count) is int and count >= 0 and bool(count) == bool(offsets),
                "malformed full-WRAM residual")
        bounded["handoff_unmasked_wram_differing_offsets"] = offsets
        bounded["handoff_unmasked_wram_differing_byte_occurrences"] = count
        if count:
            block.append("observed_unwaived_handoff_full_wram_differences_need_causality")
    # The campaign receipt cannot independently prove any of these. External
    # witnesses require separate exact-executable/source adjudication.
    block += [
        "continuous_source_original_native_course_and_consumer_equivalence_unproven",
        "original_native_cpu_apu_timing_and_audio_consequence_not_independently_closed",
        "same_shipping_windows_executable_source_and_controller_route_unbound",
        "shipping_windows_cold_disk_record_publication_unbound",
        "independent_final_adjudication_and_census_write_not_performed",
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = assess(json.loads(args.case_result.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"QA01_READINESS_INVALID: {exc}\n")
    data = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

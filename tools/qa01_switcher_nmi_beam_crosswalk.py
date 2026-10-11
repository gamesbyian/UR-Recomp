#!/usr/bin/env python3
"""Classify measured original/native Switcher NMI writer clock anchors.

This is a bounded crosswalk of two source-executed reporter outputs, not a
cross-engine cycle normalization and never a strict event acceptance rule.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import qa01_original_nmi_stack_pull_report as original
import qa01_native_nmi_beam_report as native

SCHEMA = "UR-QA01-SWITCHER-NMI-PHA-DUAL-BEAM-CROSSWALK/1"


def summarize(source: dict, guest: dict) -> dict:
    if source.get("schema") != original.SCHEMA or guest.get("schema") != native.SCHEMA:
        raise ValueError("must receive exact separately qualified original/native NMI reports")
    if ("independently_authenticated_original_native_pair" not in source
            or "exact_original_native_switcher_pair_provenance" not in guest):
        raise ValueError("neither source report may omit authenticated paired provenance")
    source_sha = source.get("paired_report_bytes_sha256")
    native_sha = guest.get("paired_report_bytes_sha256")
    if (not isinstance(source_sha, str) or source_sha != native_sha
            or re.fullmatch(r"[0-9a-f]{64}", source_sha) is None
            or source["independently_authenticated_original_native_pair"]
               != guest["exact_original_native_switcher_pair_provenance"]):
        raise ValueError("original/native NMI clocks do not share exact paired result provenance")
    a = source["saved_4042_original_pha_horizontal_clock"]
    b = guest["native_original_nmi_writer_beam"]
    if (a["original_cpu_frame_before"] != 5780
            or a["ppu_vcounter_before"] != 225
            or a["original_pha_pc"] != "00:858E"
            or a["accumulator_before"] != "4042"
            or a["stack_pointer_before"] != "01DE"
            or b["native_host_frame"] != 5781
            or b["generated_owner"] != "I_NMI_M1X1"
            or b["stack_word_saved"] != "4004"
            or b["wram_write_destination"] != "7E:01DD"
            or not source["source_hcounter_vs_native_framework_hpos_unaligned"]
            or guest.get("native_cpu_master_counter_precharged_and_store_paced_not_pha_cycle") is not True
            or guest.get("native_pha_inside_basic_block_but_exact_instruction_cycle_unknown") is not True
            or guest.get("cpu_write16_paced_charges_before_writer_log") is not True
            or guest.get("modeled_beam_hpos_not_proven_instruction_aligned") is not True
            or not guest["framework_beam_vs_original_cpu_phase_unaligned"]):
        raise ValueError("one source writer or clock provenance diverged")
    native_block_start = b.get("native_cpu_basic_block_start_master_cycles")
    native_block_end = b.get("native_cpu_charged_counter_at_write")
    native_block_width = b.get("native_cpu_charged_delta_from_block_entry")
    if (not all(type(t) is int for t in
                (native_block_start, native_block_end, native_block_width))
            or native_block_start < 0
            or native_block_start > native_block_end
            or native_block_width != native_block_end - native_block_start):
        raise ValueError("native NMI PHA has invalid monotonic charged-counter pair")
    # Authenticate scalar types before candidate arithmetic. Malformed
    # external JSON must fail closed with ValueError, not leak TypeError.
    if (not all(type(x) is int for x in
                (b.get("framework_beam_vpos"), b.get("framework_beam_hpos"),
                 a.get("ppu_vcounter_before"),
                 a.get("source_original_cpu_hcounter_before")))
            or not 0 <= b["framework_beam_vpos"] < 263
            or not 0 <= b["framework_beam_hpos"] <= 1364
            or not 0 <= a["ppu_vcounter_before"] < 263
            or a["source_original_cpu_hcounter_before"] < 0):
        raise ValueError("invalid original/native NMI timing scalar")
    all_orig = source.get("observed_original_nmi_pha_horizontal_clocks")
    if (not isinstance(all_orig, list) or len(all_orig) != 5
            or any(not isinstance(x, dict) for x in all_orig)
            or [x.get("original_cpu_frame_before") for x in all_orig]
               != list(range(5778, 5783))):
        raise ValueError("missing the five independently observed original NMI PHA clocks")
    # The standalone saved-4042 witness must be the same event as the
    # frame-5780 row in the five-NMI time series, not a splice from another
    # original trace carrying the same paired replay SHA.
    series_writer = all_orig[2]
    for key in ("original_cpu_frame_before", "original_pha_pc",
                "accumulator_before", "stack_pointer_before",
                "ppu_vcounter_before",
                "source_original_cpu_hcounter_before",
                "source_original_cpu_hcounter_after",
                "original_cpu_frame_after", "stack_pointer_after"):
        if series_writer.get(key) != a.get(key):
            raise ValueError("saved original 4042 PHA conflicts with five-NMI clock series")
    candidates = []
    for row in all_orig:
        if (row.get("original_pha_pc") != "00:858E"
                or type(row.get("source_original_cpu_hcounter_before")) is not int
                or type(row.get("ppu_vcounter_before")) is not int
                or not 0 <= row["ppu_vcounter_before"] < 263
                or row["source_original_cpu_hcounter_before"] < 0
                or not isinstance(row.get("accumulator_before"), str)
                or not isinstance(row.get("stack_pointer_before"), str)):
            raise ValueError("incomplete original NMI source frame/accumulator/stack/beam evidence")
        same_acc = row["accumulator_before"] == b["stack_word_saved"]
        same_sp = row["stack_pointer_before"] == "01DE"
        candidates.append({
            "original_cpu_frame": row["original_cpu_frame_before"],
            "original_observed_saved_accumulator": row["accumulator_before"],
            "original_pre_pha_stack_pointer": row["stack_pointer_before"],
            "original_ppu_vcounter": row["ppu_vcounter_before"],
            "original_horizontal_cpu_cycles": row["source_original_cpu_hcounter_before"],
            "raw_h_delta_native_minus_original": (
                b["framework_beam_hpos"] - row["source_original_cpu_hcounter_before"]),
            "same_saved_accumulator_word_as_native_4004": same_acc,
            "same_pre_pha_stack_pointer_as_native_01de": same_sp,
            "same_vertical_line_number_as_native": (
                b["framework_beam_vpos"] == row["ppu_vcounter_before"]),
            "native_cpu_frame_identity_not_proven": True,
            "possible_same_interrupt_not_proven": True,
        })
    # Classify measured rows without pre-assigning values to original
    # CPU frames. Other-frame A and S values in unit tests are SYNTHETIC;
    # the combined five-NMI original/native runtime trace has not run yet.
    same_acc_frames = [c["original_cpu_frame"] for c in candidates
                       if c["same_saved_accumulator_word_as_native_4004"]]
    same_sp_frames = [c["original_cpu_frame"] for c in candidates
                      if c["same_pre_pha_stack_pointer_as_native_01de"]]
    both_match_frames = [c["original_cpu_frame"] for c in candidates
                         if c["same_saved_accumulator_word_as_native_4004"]
                         and c["same_pre_pha_stack_pointer_as_native_01de"]]
    o_h, n_h = a["source_original_cpu_hcounter_before"], b["framework_beam_hpos"]
    o_v, n_v = a["ppu_vcounter_before"], b["framework_beam_vpos"]
    return {
        "schema": SCHEMA,
        "paired_report_bytes_sha256": source_sha,
        "original_cpu_frame": 5780,
        "native_host_frame": 5781,
        "original_cpu_ppu_vcounter": o_v,
        "native_framework_beam_vpos": n_v,
        "observed_same_vertical_line_number": o_v == n_v,
        "original_cpu_horizontal_cycles": o_h,
        "native_framework_beam_hpos": n_h,
        "raw_horizontal_numeric_difference_native_minus_original": n_h - o_h,
        "original_saved_accumulator_word": "4042",
        "all_five_original_nmi_phase_candidates": candidates,
        "source_4004_accumulator_match_frames": same_acc_frames,
        "source_01de_stack_pointer_match_frames": same_sp_frames,
        "source_both_accumulator_and_stack_match_frames": both_match_frames,
        "no_original_nmi_matches_both_saved_a_and_pre_pha_s":
            not bool(both_match_frames),
        "candidate_beam_reading_cannot_rank_interrupt_identity": True,
        "native_saved_accumulator_word": "4004",
        "clock_unit_origin_and_execution_phase_equivalence_not_proven": True,
        "native_master_counter_is_precharged_and_store_paced": True,
        "native_basic_block_start_master_cycles": native_block_start,
        "native_charged_counter_at_write": native_block_end,
        "native_charged_delta_from_block_entry": native_block_width,
        "native_pha_exact_cycle_not_reconstructable_from_charged_counters": True,
        "matching_scanline_alone_is_not_causal_parity": True,
        "cpu_architectural_return_parity_not_proven": True,
        "strict_guest_relative_result_original_native": [4704, 4702],
        "completed_usa_course_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-report", type=Path, required=True)
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(json.loads(args.original_report.read_text(encoding="utf-8")),
                       json.loads(args.native_report.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
            or guest.get("native_cpu_master_counter_is_precharged_basic_block_not_pha_cycle") is not True
            or guest.get("native_pha_inside_basic_block_but_exact_instruction_cycle_unknown") is not True
            or guest.get("modeled_beam_hpos_not_proven_instruction_aligned") is not True
            or not guest["framework_beam_vs_original_cpu_phase_unaligned"]):
        raise ValueError("one source writer or clock provenance diverged")
    native_block_start = b.get("native_cpu_basic_block_start_master_cycles")
    native_block_end = b.get("native_cpu_basic_block_end_master_cycles")
    native_block_width = b.get("native_cpu_basic_block_bracket_width_master_cycles")
    if (not all(type(t) is int for t in
                (native_block_start, native_block_end, native_block_width))
            or native_block_start < 0
            or native_block_start > native_block_end
            or native_block_width != native_block_end - native_block_start):
        raise ValueError("native NMI PHA missing valid basic-block clock bracket")
    o_h, n_h = a["source_original_cpu_hcounter_before"], b["framework_beam_hpos"]
    o_v, n_v = a["ppu_vcounter_before"], b["framework_beam_vpos"]
    if not (type(o_h) is int and type(n_h) is int and type(n_v) is int):
        raise ValueError("invalid source-clock data type")
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
        "native_saved_accumulator_word": "4004",
        "clock_unit_origin_and_execution_phase_equivalence_not_proven": True,
        "native_master_counter_is_basic_block_not_pha_cycle": True,
        "native_basic_block_start_master_cycles": native_block_start,
        "native_basic_block_end_master_cycles": native_block_end,
        "native_basic_block_width_master_cycles": native_block_width,
        "native_pha_exact_cycle_inside_bracket_not_observed": True,
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

#!/usr/bin/env python3
"""Bind the native NMI writer beam and WRAM-read journal to one exact replay.

This reconciles two independently parsed instruments. It does not observe
new guest instructions, establish matching original/native CPU phase, identify
a scoring consumer, or admit a complete course.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import qa01_native_nmi_beam_report as beam
import qa01_native_stack_read_report as reads

SCHEMA = "UR-QA01-NATIVE-SWITCHER-NMI-WRITER-READ-JOURNAL-CROSSWALK/1"


def summarize(writer: dict, reader: dict) -> dict:
    if not isinstance(writer, dict) or not isinstance(reader, dict):
        raise ValueError("missing paired native NMI and read report dictionaries")
    if writer.get("schema") != beam.SCHEMA or reader.get("schema") != reads.SCHEMA:
        raise ValueError("wrong native writer/read source report schema")
    wsha, rsha = (writer.get("paired_report_bytes_sha256"),
                  reader.get("paired_report_bytes_sha256"))
    if (type(wsha) is not str or re.fullmatch(r"[0-9a-f]{64}", wsha) is None
            or wsha != rsha
            or writer.get("exact_original_native_switcher_pair_provenance")
               != reader.get("independently_authenticated_original_native_pair")
            or not isinstance(writer.get("exact_original_native_switcher_pair_provenance"), dict)
            or not writer["exact_original_native_switcher_pair_provenance"]):
        raise ValueError("the two native witnesses do not share authenticated paired replay bytes")
    event = writer.get("native_original_nmi_writer_beam")
    if (not isinstance(event, dict)
            or event.get("native_host_frame") != 5781
            or event.get("generated_owner") != "I_NMI_M1X1"
            or event.get("wram_write_destination") != "7E:01DD"
            or event.get("stack_word_saved") != "4004"
            or event.get("accumulator_at_write") != "4004"
            or event.get("stack_pointer_at_write") != "01DD"
            or writer.get("native_observation_host_frame_window") != [5778, 5782]
            or writer.get("accepted_usa_course_count_added") != 0
            or writer.get("framework_beam_vs_original_cpu_phase_unaligned") is not True
            or reader.get("native_frame_bounds") != [5778, 5782]
            or reader.get("native_read_observer_armed_by_real_nmi_4004_writer") is not True
            or reader.get("read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer")
               is not True
            or reader.get("release_complete_event_credit") != 0):
        raise ValueError("paired writer/read scope not the exact no-credit native NMI saved-A")
    rows = reader.get("native_stack_read_attempts")
    count = reader.get("native_bus_read_attempt_count")
    tally = reader.get("native_bus_read_attempts_by_target")
    if (not isinstance(rows, list) or type(count) is not int
            or len(rows) != count or not 0 <= count <= reads.LIMIT
            or not isinstance(tally, dict)
            or set(tally) != {"7E:01DD", "7E:01DE"}
            or any(type(v) is not int or v < 0 or v > count
                   for v in tally.values())
            or reader.get("zero_count_is_bounded_native_negative_not_no_reader_ever")
               is not (count == 0)):
        raise ValueError("read journal counts/zero-witness metadata invalid")
    actual = {"7E:01DD": 0, "7E:01DE": 0}
    derived_broad = 0
    derived_strict = 0
    derived_next_broad = 0
    derived_next_strict = 0
    previous_frame = 5778
    armed_in_read_journal = False
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("malformed read row in paired native journal")
        targets = row.get("target_stack_bytes_touched")
        if (not isinstance(targets, list) or not targets
                or len(targets) > 2 or len(set(targets)) != len(targets)
                or any(target not in actual for target in targets)):
            raise ValueError("native read row does not touch pinned stack targets")
        frame = row.get("native_snes_frame_counter")
        width = row.get("bus_read_width")
        bank = row.get("memory_bank_alias")
        start = row.get("word_start")
        word = row.get("read_value")
        sp = row.get("stack_pointer_at_read")
        a = row.get("register_a_at_read")
        scope = row.get("generated_or_interpreter_scope")
        armed = row.get("observed_after_4004_writer_callback_started")
        same_sp = row.get("stack_pointer_equals_read_start_at_callback")
        if (type(frame) is not int or not 5778 <= frame <= 5782
                or frame < previous_frame
                or type(width) is not int or width not in (1, 2)
                or type(bank) is not str
                or re.fullmatch(r"[0-9A-F]{2}", bank) is None
                or not (int(bank, 16) == 0x7E
                        or 0 <= int(bank, 16) <= 0x3F
                        or 0x80 <= int(bank, 16) <= 0xBF)
                or type(start) is not str
                or re.fullmatch(r"[0-9A-F]{4}", start) is None
                or type(word) is not str
                or re.fullmatch(r"[0-9A-F]{4}", word) is None
                or (width == 1 and int(word, 16) > 0xFF)
                or type(sp) is not str or re.fullmatch(r"[0-9A-F]{4}", sp) is None
                or type(a) is not str or re.fullmatch(r"[0-9A-F]{4}", a) is None
                or type(scope) is not str
                or re.fullmatch(r"[A-Za-z0-9_?]{1,120}", scope) is None
                or type(armed) is not bool or type(same_sp) is not bool
                or type(row.get("memory_width_flag_at_read")) is not int
                or row["memory_width_flag_at_read"] not in (0, 1)
                or row.get("register_s_does_not_prove_stack_instruction") is not True):
            raise ValueError("unqualified native stack read row timing/width/stack fields")
        start_num = int(start, 16)
        expected = [f"7E:{start_num + byte:04X}"
                    for byte in range(width)
                    if start_num + byte in (0x01DD, 0x01DE)]
        if targets != expected or same_sp is not (sp == start):
            raise ValueError("reported stack bytes/S equality contradict original read address")
        if frame < 5781 and armed:
            raise ValueError("native read cannot precede frame-5781 arming")
        if frame > 5781 and not armed:
            raise ValueError("native frame after writer cannot be marked pre-arm")
        if armed_in_read_journal and not armed:
            raise ValueError("native read journal reverted to pre-writer status")
        previous_frame = frame
        armed_in_read_journal = armed_in_read_journal or armed
        for target in targets:
            actual[target] += 1
        # The archived read JSON must not be able to alter candidate
        # counts separately from the actual normalized underlying rows.
        is_broad = (row["observed_after_4004_writer_callback_started"] is True
                    and frame in (5781, 5782) and width == 2
                    and row["word_start"] == "01DD"
                    and row.get("read_value") == "4004")
        if is_broad:
            if frame == 5781:
                derived_broad += 1
            else:
                derived_next_broad += 1
            if (row["stack_pointer_equals_read_start_at_callback"] is True
                    and row["memory_width_flag_at_read"] == 0):
                if frame == 5781:
                    derived_strict += 1
                else:
                    derived_next_strict += 1
    if tally != actual:
        raise ValueError("journal read counts disagree with actual declared target bytes")
    # Independently rederive the two-byte interpreter-shaped candidate;
    # a separate count cannot be trusted without the actual ordered rows.
    expected_pairs = []
    expected_next_pairs = []
    for index, (lo, hi) in enumerate(zip(rows, rows[1:])):
        frame = lo["native_snes_frame_counter"]
        if (lo["observed_after_4004_writer_callback_started"] is True
                and hi["observed_after_4004_writer_callback_started"] is True
                and frame in (5781, 5782)
                and hi["native_snes_frame_counter"] == frame
                and lo["bus_read_width"] == hi["bus_read_width"] == 1
                and lo["word_start"] == "01DD"
                and hi["word_start"] == "01DE"
                and lo["read_value"] == "0004"
                and hi["read_value"] == "0040"):
            (expected_pairs if frame == 5781 else expected_next_pairs).append(
                [index, index + 1])
    if (reader.get("native_post_writer_same_frame_4004_two_byte_target_row_pairs")
            != expected_pairs
            or type(reader.get(
                "native_post_writer_same_frame_4004_two_byte_pair_candidate_count")) is not int
            or reader["native_post_writer_same_frame_4004_two_byte_pair_candidate_count"]
               != len(expected_pairs)
            or reader.get(
                "native_post_writer_following_frame_4004_two_byte_target_row_pairs")
               != expected_next_pairs
            or type(reader.get(
                "native_post_writer_following_frame_4004_two_byte_pair_candidate_count")) is not int
            or reader["native_post_writer_following_frame_4004_two_byte_pair_candidate_count"]
               != len(expected_next_pairs)
            or reader.get("interpreter_16bit_pla_uses_two_independent_byte_bus_reads")
               is not True
            or reader.get("filtered_read_row_adjacency_does_not_prove_guest_opcode_adjacency")
               is not True
            or reader.get("cpu_state_s_and_m_at_interpreter_bridge_callback_not_proven_internal_interp_registers")
               is not True):
        raise ValueError("native interpreter-like byte-read pair is unverified")
    broad = reader.get("same_native_frame_post_writer_callback_read_4004_candidate_count")
    strict = reader.get("same_frame_post_writer_stack_position_consistent_word_4004_count")
    next_broad = reader.get(
        "following_frame_post_writer_callback_read_4004_candidate_count")
    next_strict = reader.get(
        "following_frame_post_writer_stack_position_consistent_word_4004_count")
    if (type(broad) is not int or type(strict) is not int
            or type(next_broad) is not int or type(next_strict) is not int
            or broad != derived_broad or strict != derived_strict
            or next_broad != derived_next_broad or next_strict != derived_next_strict
            or not 0 <= strict <= broad <= count
            or not 0 <= next_strict <= next_broad <= count
            or broad + next_broad > count
            or reader.get("stack_pointer_matches_bus_start_not_proof_of_pla") is not True):
        raise ValueError("native 4004 bus-read candidate classification metadata invalid")
    # Source-ordered within the read journal only. The independent write
    # logger samples CPU master cycles at another callback boundary.
    return {
        "schema": SCHEMA,
        "paired_report_bytes_sha256": wsha,
        "writer_host_frame": 5781,
        "writer_guest_saved_word": "4004",
        "writer_01dd_address": "7E:01DD",
        "native_read_attempt_count": count,
        "native_read_targets_tallied": actual,
        "native_same_frame_4004_word_read_candidates": broad,
        "native_stack_pointer_consistent_4004_word_read_candidates": strict,
        "native_interpreter_shaped_4004_two_byte_candidate_pairs": expected_pairs,
        "native_interpreter_shaped_4004_two_byte_candidate_count": len(expected_pairs),
        "native_following_frame_4004_word_read_candidates": next_broad,
        "native_following_frame_stack_pointer_consistent_word_read_candidates":
            next_strict,
        "native_following_frame_interpreter_shaped_4004_two_byte_candidate_pairs":
            expected_next_pairs,
        "native_following_frame_interpreter_shaped_4004_two_byte_candidate_count":
            len(expected_next_pairs),
        "following_frame_saved_a_read_is_candidate_not_architectural_restore": True,
        "native_internal_interp_stack_state_not_observed_by_bus_logger": True,
        "writer_and_reader_share_pair_bytes": True,
        "single_physical_writer_event_correlated_by_callbacks_not_cpu_cycle": True,
        "read_callback_after_writer_callback_not_proven_guest_restore": True,
        "source_original_and_native_beam_phase_alignment_proven": False,
        "native_guest_result_consumer_proven": False,
        "complete_usa_course_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-beam-report", type=Path, required=True)
    ap.add_argument("--native-read-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = summarize(
        json.loads(args.native_beam_report.read_text(encoding="utf-8")),
        json.loads(args.native_read_report.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

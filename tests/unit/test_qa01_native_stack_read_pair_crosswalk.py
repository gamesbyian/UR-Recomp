"""Synthetic cross-report native writer/read provenance, no release admission."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_stack_read_pair_crosswalk as x
import qa01_native_nmi_beam_report as beam
import qa01_native_stack_read_report as reads

SHA = "f" * 64
PAIR = {"course_id": "course:04", "trusted": True}
BEAM = {
    "schema": beam.SCHEMA,
    "paired_report_bytes_sha256": SHA,
    "exact_original_native_switcher_pair_provenance": PAIR,
    "native_observation_host_frame_window": [5778, 5782],
    "accepted_usa_course_count_added": 0,
    "framework_beam_vs_original_cpu_phase_unaligned": True,
    "native_original_nmi_writer_beam": {
        "native_host_frame": 5781,
        "generated_owner": "I_NMI_M1X1",
        "wram_write_destination": "7E:01DD",
        "stack_word_saved": "4004",
        "accumulator_at_write": "4004",
        "stack_pointer_at_write": "01DD",
    },
}
READ = {
    "schema": reads.SCHEMA,
    "paired_report_bytes_sha256": SHA,
    "independently_authenticated_original_native_pair": PAIR,
    "native_frame_bounds": [5778, 5782],
    "native_read_observer_armed_by_real_nmi_4004_writer": True,
    "read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer": True,
    "native_bus_read_attempt_count": 1,
    "native_stack_read_attempts": [{
        "target_stack_bytes_touched": ["7E:01DD", "7E:01DE"],
        "native_snes_frame_counter": 5781,
        "read_value": "4004",
        "word_start": "01DD",
        "memory_bank_alias": "00",
        "bus_read_width": 2,
        "stack_pointer_at_read": "01DC",
        "register_a_at_read": "0000",
        "generated_or_interpreter_scope": "I_NMI_M1X1",
        "register_s_does_not_prove_stack_instruction": True,
        "memory_width_flag_at_read": 0,
        "stack_pointer_equals_read_start_at_callback": False,
        "observed_after_4004_writer_callback_started": True,
    }],
    "native_bus_read_attempts_by_target": {"7E:01DD": 1, "7E:01DE": 1},
    "zero_count_is_bounded_native_negative_not_no_reader_ever": False,
    "same_native_frame_post_writer_callback_read_4004_candidate_count": 1,
    "same_frame_post_writer_stack_position_consistent_word_4004_count": 0,
    "stack_pointer_matches_bus_start_not_proof_of_pla": True,
    "native_post_writer_same_frame_4004_two_byte_target_row_pairs": [],
    "native_post_writer_same_frame_4004_two_byte_pair_candidate_count": 0,
    "native_post_writer_following_frame_4004_two_byte_target_row_pairs": [],
    "native_post_writer_following_frame_4004_two_byte_pair_candidate_count": 0,
    "following_frame_post_writer_callback_read_4004_candidate_count": 0,
    "following_frame_post_writer_stack_position_consistent_word_4004_count": 0,
    "interpreter_16bit_pla_uses_two_independent_byte_bus_reads": True,
    "filtered_read_row_adjacency_does_not_prove_guest_opcode_adjacency": True,
    "cpu_state_s_and_m_at_interpreter_bridge_callback_not_proven_internal_interp_registers": True,
    "release_complete_event_credit": 0,
}


class NativeStackReadPairCrosswalkTests(unittest.TestCase):
    def test_same_exact_replay_pair_and_one_observed_read_remains_no_credit(self):
        out = x.summarize(BEAM, READ)
        self.assertEqual(out["native_read_attempt_count"], 1)
        self.assertEqual(out["native_read_targets_tallied"],
                         {"7E:01DD": 1, "7E:01DE": 1})
        self.assertTrue(out["writer_and_reader_share_pair_bytes"])
        self.assertEqual(out["native_same_frame_4004_word_read_candidates"], 1)
        self.assertEqual(out["native_stack_pointer_consistent_4004_word_read_candidates"], 0)
        self.assertEqual(out["native_interpreter_shaped_4004_two_byte_candidate_count"], 0)
        self.assertFalse(out["native_guest_result_consumer_proven"])
        self.assertFalse(out["source_original_and_native_beam_phase_alignment_proven"])
        self.assertEqual(out["complete_usa_course_credit"], 0)

    def test_zero_read_witness_is_still_qualified_bounded_negative(self):
        doc = copy.deepcopy(READ)
        doc["native_bus_read_attempt_count"] = 0
        doc["native_stack_read_attempts"] = []
        doc["native_bus_read_attempts_by_target"] = {"7E:01DD": 0, "7E:01DE": 0}
        doc["zero_count_is_bounded_native_negative_not_no_reader_ever"] = True
        doc["same_native_frame_post_writer_callback_read_4004_candidate_count"] = 0
        doc["same_frame_post_writer_stack_position_consistent_word_4004_count"] = 0
        data = x.summarize(BEAM, doc)
        self.assertEqual(data["native_read_attempt_count"], 0)
        self.assertFalse(data["native_guest_result_consumer_proven"])

    def test_mismatched_replay_identity_and_forged_attestations_fail_closed(self):
        for obj, key, value in (
            ("read", "paired_report_bytes_sha256", "e" * 64),
            ("read", "independently_authenticated_original_native_pair", {"course_id": "other"}),
            ("beam", "paired_report_bytes_sha256", "corrupt"),
            ("beam", "native_original_nmi_writer_beam", {"stack_word_saved": "4004"}),
            ("beam", "native_observation_host_frame_window", [5778, 5783]),
            ("read", "native_read_observer_armed_by_real_nmi_4004_writer", False),
            ("read", "native_bus_read_attempt_count", 2),
            ("read", "native_bus_read_attempt_count", True),
            ("read", "native_bus_read_attempts_by_target", {"7E:01DD": 0, "7E:01DE": 1}),
            ("read", "zero_count_is_bounded_native_negative_not_no_reader_ever", True),
            ("read", "release_complete_event_credit", 1),
            ("read", "same_native_frame_post_writer_callback_read_4004_candidate_count", 0),
            ("read", "same_frame_post_writer_stack_position_consistent_word_4004_count", 2),
        ):
            writer, reader = copy.deepcopy(BEAM), copy.deepcopy(READ)
            (writer if obj == "beam" else reader)[key] = value
            with self.subTest(obj=obj, field=key), self.assertRaises(ValueError):
                x.summarize(writer, reader)

    def test_counters_are_rederived_from_actual_rows_not_just_bounded(self):
        for field, replacement in (
            ("read_value", "4042"),
            ("word_start", "01DE"),
            ("bus_read_width", 1),
            ("native_snes_frame_counter", 5782),
            ("observed_after_4004_writer_callback_started", False),
            ("memory_width_flag_at_read", "0"),
        ):
            doc = copy.deepcopy(READ)
            doc["native_stack_read_attempts"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                x.summarize(BEAM, doc)
        doc = copy.deepcopy(READ)
        doc["native_stack_read_attempts"][0][
            "stack_pointer_equals_read_start_at_callback"] = True
        with self.assertRaises(ValueError):
            x.summarize(BEAM, doc)
        doc["native_stack_read_attempts"][0]["stack_pointer_at_read"] = "01DD"
        doc["same_frame_post_writer_stack_position_consistent_word_4004_count"] = 1
        result = x.summarize(BEAM, doc)
        self.assertEqual(result["native_stack_pointer_consistent_4004_word_read_candidates"], 1)
        self.assertFalse(result["native_guest_result_consumer_proven"])

    def test_rejects_forged_stack_alias_target_and_callback_order(self):
        for key, bad in (
            ("memory_bank_alias", "7F"),
            ("memory_bank_alias", "40"),
            ("memory_bank_alias", True),
            ("stack_pointer_at_read", "01DD"),
            ("stack_pointer_at_read", "broken"),
            ("word_start", "01DC"),
            ("target_stack_bytes_touched", ["7E:01DD"]),
            ("target_stack_bytes_touched", ["7E:01DE", "7E:01DD"]),
            ("register_a_at_read", "fake"),
            ("generated_or_interpreter_scope", ""),
            ("register_s_does_not_prove_stack_instruction", False),
            ("observed_after_4004_writer_callback_started", 1),
        ):
            candidate = copy.deepcopy(READ)
            candidate["native_stack_read_attempts"][0][key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                x.summarize(BEAM, candidate)

    def test_rejects_out_of_order_or_impossible_writer_arm_frames(self):
        first = copy.deepcopy(READ["native_stack_read_attempts"][0])
        variants = (
            [dict(first, native_snes_frame_counter=5780)],
            [dict(first, native_snes_frame_counter=5782,
                  observed_after_4004_writer_callback_started=False)],
            [dict(first, native_snes_frame_counter=5782),
             dict(first, native_snes_frame_counter=5781)],
            [dict(first, native_snes_frame_counter=5781),
             dict(first, native_snes_frame_counter=5781,
                  observed_after_4004_writer_callback_started=False)],
        )
        for rows in variants:
            candidate = copy.deepcopy(READ)
            candidate["native_stack_read_attempts"] = rows
            candidate["native_bus_read_attempt_count"] = len(rows)
            candidate["native_bus_read_attempts_by_target"] = {
                "7E:01DD": len(rows), "7E:01DE": len(rows)}
            candidate["same_native_frame_post_writer_callback_read_4004_candidate_count"] = sum(
                int(r["native_snes_frame_counter"] == 5781 and
                    r["observed_after_4004_writer_callback_started"] is True) for r in rows)
            with self.subTest(frames=[r["native_snes_frame_counter"] for r in rows]):
                with self.assertRaises(ValueError):
                    x.summarize(BEAM, candidate)

    def test_real_report_parser_and_crosswalk_agree_on_two_byte_shape(self):
        journal = (
            "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
            "A=4004 S=01DD scope=I_NMI_M1X1\n"
            "QANATIVEREAD f=5781 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
            "QANATIVEREAD f=5781 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
        )
        parsed = reads.summarize(journal)
        parsed["paired_report_bytes_sha256"] = SHA
        parsed["independently_authenticated_original_native_pair"] = PAIR
        result = x.summarize(BEAM, parsed)
        self.assertEqual(result["native_interpreter_shaped_4004_two_byte_candidate_pairs"], [[0,1]])
        self.assertEqual(result["native_interpreter_shaped_4004_two_byte_candidate_count"], 1)
        self.assertFalse(result["native_guest_result_consumer_proven"])
        for field, fake in (
            ("native_post_writer_same_frame_4004_two_byte_pair_candidate_count", 0),
            ("native_post_writer_same_frame_4004_two_byte_target_row_pairs", [[1,0]]),
            ("interpreter_16bit_pla_uses_two_independent_byte_bus_reads", False),
        ):
            candidate = copy.deepcopy(parsed)
            candidate[field] = fake
            with self.subTest(field=field), self.assertRaises(ValueError):
                x.summarize(BEAM, candidate)

    def test_following_frame_candidates_are_checked_against_real_journal_rows(self):
        journal = (
            "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
            "A=4004 S=01DD scope=I_NMI_M1X1\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DD width=2 value=4004 "
            "A=0000 S=01DD M=0 scope=AotReturn\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
        )
        parsed = reads.summarize(journal)
        parsed["paired_report_bytes_sha256"] = SHA
        parsed["independently_authenticated_original_native_pair"] = PAIR
        observed = x.summarize(BEAM, parsed)
        self.assertEqual(observed["native_same_frame_4004_word_read_candidates"], 0)
        self.assertEqual(observed["native_following_frame_4004_word_read_candidates"], 1)
        self.assertEqual(observed[
            "native_following_frame_stack_pointer_consistent_word_read_candidates"], 1)
        self.assertEqual(observed[
            "native_following_frame_interpreter_shaped_4004_two_byte_candidate_pairs"], [[1, 2]])
        self.assertTrue(observed[
            "following_frame_saved_a_read_is_candidate_not_architectural_restore"])
        self.assertFalse(observed["native_guest_result_consumer_proven"])
        self.assertEqual(observed["complete_usa_course_credit"], 0)
        for field, fake in (
            ("following_frame_post_writer_callback_read_4004_candidate_count", 0),
            ("following_frame_post_writer_stack_position_consistent_word_4004_count", 0),
            ("native_post_writer_following_frame_4004_two_byte_target_row_pairs", []),
            ("native_post_writer_following_frame_4004_two_byte_pair_candidate_count", 0),
        ):
            tampered = copy.deepcopy(parsed)
            tampered[field] = fake
            with self.subTest(field=field), self.assertRaises(ValueError):
                x.summarize(BEAM, tampered)

    def test_manual_workflow_produces_separate_crosscheck_from_existing_logs(self):
        wf = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        self.assertIn("qa01_native_stack_read_pair_crosswalk.py", wf)
        self.assertIn("--native-read-report", wf)
        self.assertIn("--native-beam-report", wf)
        self.assertIn("native-read-writer-crosswalk.json", wf)


if __name__ == "__main__":
    unittest.main()

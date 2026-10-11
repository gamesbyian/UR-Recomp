"""Synthetic-only NMI A/S fixtures; never claim five-frame original execution."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_original_nmi_stack_pull_report as o
import qa01_native_nmi_beam_report as n
import qa01_switcher_nmi_beam_crosswalk as cross

ORIGINAL = {
    "schema": o.SCHEMA,
    "paired_report_bytes_sha256": "a" * 64,
    "independently_authenticated_original_native_pair": {"course_id": "course:04"},
    "source_hcounter_vs_native_framework_hpos_unaligned": True,
    "observed_original_nmi_pha_horizontal_clocks": [
        {"original_cpu_frame_before": frame,
         "original_pha_pc": "00:858E",
         "accumulator_before": saved_a,
         "stack_pointer_before": stack,
         "stack_pointer_after": next_sp,
         "original_cpu_frame_after": frame,
         "ppu_vcounter_before": 225,
         "source_original_cpu_hcounter_before": h,
         "source_original_cpu_hcounter_after": h + 8}
        for frame, saved_a, stack, next_sp, h in (
            (5778, "4040", "01E2", "01E0", 800),
            (5779, "4004", "01EA", "01E8", 807),
            (5780, "4042", "01DE", "01DC", 816),
            (5781, "4042", "01E7", "01E5", 832),
            (5782, "4004", "01E5", "01E3", 844),
        )
    ],
    "saved_4042_original_pha_horizontal_clock": {
        "original_cpu_frame_before": 5780,
        "ppu_vcounter_before": 225,
        "original_pha_pc": "00:858E",
        "accumulator_before": "4042",
        "stack_pointer_before": "01DE",
        "stack_pointer_after": "01DC",
        "original_cpu_frame_after": 5780,
        "source_original_cpu_hcounter_before": 816,
        "source_original_cpu_hcounter_after": 824,
    },
}
NATIVE = {
    "schema": n.SCHEMA,
    "paired_report_bytes_sha256": "a" * 64,
    "exact_original_native_switcher_pair_provenance": {"course_id": "course:04"},
    "framework_beam_vs_original_cpu_phase_unaligned": True,
    "native_cpu_master_counter_precharged_and_store_paced_not_pha_cycle": True,
    "native_pha_inside_basic_block_but_exact_instruction_cycle_unknown": True,
    "cpu_write16_paced_charges_before_writer_log": True,
    "modeled_beam_hpos_not_proven_instruction_aligned": True,
    "native_original_nmi_writer_beam": {
        "native_host_frame": 5781,
        "generated_owner": "I_NMI_M1X1",
        "stack_word_saved": "4004",
        "wram_write_destination": "7E:01DD",
        "framework_beam_vpos": 225,
        "framework_beam_hpos": 821,
        "native_cpu_basic_block_start_master_cycles": 945130,
        "native_cpu_charged_counter_at_write": 945374,
        "native_cpu_charged_delta_from_block_entry": 244,
    },
}


class SwitcherNmiBeamCrosswalkTests(unittest.TestCase):
    def test_same_line_different_h_count_is_diagnostic_not_acceptance(self):
        data = cross.summarize(ORIGINAL, NATIVE)
        self.assertTrue(data["observed_same_vertical_line_number"])
        self.assertEqual(data["raw_horizontal_numeric_difference_native_minus_original"], 5)
        self.assertTrue(data["clock_unit_origin_and_execution_phase_equivalence_not_proven"])
        self.assertTrue(data["native_master_counter_is_precharged_and_store_paced"])
        self.assertTrue(data["native_pha_exact_cycle_not_reconstructable_from_charged_counters"])
        self.assertEqual(data["native_charged_delta_from_block_entry"], 244)
        self.assertTrue(data["cpu_architectural_return_parity_not_proven"])
        self.assertEqual(data["strict_guest_relative_result_original_native"], [4704, 4702])
        self.assertEqual(data["completed_usa_course_credit"], 0)
        self.assertEqual(data["source_4004_accumulator_match_frames"], [5779, 5782])
        self.assertEqual(data["source_01de_stack_pointer_match_frames"], [5780])
        self.assertTrue(data["no_original_nmi_matches_both_saved_a_and_pre_pha_s"])
        self.assertEqual(data["source_both_accumulator_and_stack_match_frames"], [])
        self.assertEqual(len(data["observed_original_nmi_pha_candidates"]), 5)
        self.assertTrue(data["five_original_nmi_hardware_entries_do_not_prove_five_matching_phas"])
        self.assertTrue(data["candidate_beam_reading_cannot_rank_interrupt_identity"])
        self.assertEqual(data["paired_report_bytes_sha256"], "a" * 64)

    def test_matching_raw_horizontal_number_is_still_not_phase_proof(self):
        native = copy.deepcopy(NATIVE)
        native["native_original_nmi_writer_beam"]["framework_beam_hpos"] = 816
        data = cross.summarize(ORIGINAL, native)
        self.assertEqual(data["raw_horizontal_numeric_difference_native_minus_original"], 0)
        self.assertTrue(data["matching_scanline_alone_is_not_causal_parity"])
        self.assertTrue(data["clock_unit_origin_and_execution_phase_equivalence_not_proven"])

    def test_synthetic_accumulator_and_stack_agreements_differ(self):
        native = copy.deepcopy(NATIVE)
        native["native_original_nmi_writer_beam"]["framework_beam_hpos"] = 816
        data = cross.summarize(ORIGINAL, native)
        rows = data["all_five_original_nmi_phase_candidates"]
        writer = next(r for r in rows if r["original_cpu_frame"] == 5780)
        self.assertEqual(writer["raw_h_delta_native_minus_original"], 0)
        self.assertTrue(writer["same_pre_pha_stack_pointer_as_native_01de"])
        self.assertFalse(writer["same_saved_accumulator_word_as_native_4004"])
        earlier = next(r for r in rows if r["original_cpu_frame"] == 5779)
        self.assertTrue(earlier["same_saved_accumulator_word_as_native_4004"])
        self.assertFalse(earlier["same_pre_pha_stack_pointer_as_native_01de"])
        self.assertTrue(earlier["possible_same_interrupt_not_proven"])

    def test_other_original_frame_values_are_measured_not_expected_fixtures(self):
        # Only the independently pinned 5780 PHA is fixed. These neighboring
        # example frames are not real five-frame runtime observations.
        src = copy.deepcopy(ORIGINAL)
        src["observed_original_nmi_pha_horizontal_clocks"][1].update({
            "accumulator_before": "4099", "stack_pointer_before": "01DE",
        })
        src["observed_original_nmi_pha_horizontal_clocks"][4].update({
            "accumulator_before": "4004", "stack_pointer_before": "01DE",
        })
        data = cross.summarize(src, NATIVE)
        self.assertEqual(data["source_4004_accumulator_match_frames"], [5782])
        self.assertEqual(data["source_01de_stack_pointer_match_frames"],
                         [5779, 5780, 5782])
        self.assertEqual(data["source_both_accumulator_and_stack_match_frames"],
                         [5782])
        self.assertFalse(data["no_original_nmi_matches_both_saved_a_and_pre_pha_s"])
        self.assertTrue(data["candidate_beam_reading_cannot_rank_interrupt_identity"])
        self.assertEqual(data["completed_usa_course_credit"], 0)

    def test_only_one_actual_original_pha_is_enough_to_admit_bounded_crosswalk(self):
        source = copy.deepcopy(ORIGINAL)
        source["observed_original_nmi_pha_horizontal_clocks"] = [
            source["observed_original_nmi_pha_horizontal_clocks"][2]]
        result = cross.summarize(source, NATIVE)
        self.assertEqual(result["observed_original_nmi_pha_row_count"], 1)
        self.assertEqual(result["source_4004_accumulator_match_frames"], [])
        self.assertEqual(result["source_01de_stack_pointer_match_frames"], [5780])
        self.assertEqual(len(result["observed_original_nmi_pha_candidates"]), 1)
        self.assertEqual(result["completed_usa_course_credit"], 0)

    def test_invalid_source_or_native_writer_never_crosswalks(self):
        for key, value in (
            ("schema", "incorrect"),
            ("source_hcounter_vs_native_framework_hpos_unaligned", False),
            ("saved_4042_original_pha_horizontal_clock.original_cpu_frame_before", 5781),
            ("saved_4042_original_pha_horizontal_clock.accumulator_before", "4004"),
            ("saved_4042_original_pha_horizontal_clock.original_pha_pc", "80:858F"),
            ("saved_4042_original_pha_horizontal_clock.source_original_cpu_hcounter_after", 823),
            ("observed_original_nmi_pha_horizontal_clocks", []),
            ("observed_original_nmi_pha_horizontal_clocks", [
                {"original_cpu_frame_before": 5780}]),
            ("observed_original_nmi_pha_horizontal_clocks", [
                ORIGINAL["observed_original_nmi_pha_horizontal_clocks"][1]]),
        ):
            src = copy.deepcopy(ORIGINAL)
            obj, member = (key.split(".", 1) + [None])[:2]
            if member is None:
                src[obj] = value
            else:
                src[obj][member] = value
            with self.subTest(original=key):
                with self.assertRaises(ValueError):
                    cross.summarize(src, NATIVE)
        for key, value in (
            ("schema", "wrong"),
            ("paired_report_bytes_sha256", "b" * 64),
            ("paired_report_bytes_sha256", "invalid"),
            ("exact_original_native_switcher_pair_provenance", {"different": "guest"}),
            ("framework_beam_vs_original_cpu_phase_unaligned", False),
            ("native_cpu_master_counter_precharged_and_store_paced_not_pha_cycle", False),
            ("modeled_beam_hpos_not_proven_instruction_aligned", False),
            ("native_pha_inside_basic_block_but_exact_instruction_cycle_unknown", False),
            ("cpu_write16_paced_charges_before_writer_log", False),
            ("native_original_nmi_writer_beam.native_cpu_basic_block_start_master_cycles", 945375),
            ("native_original_nmi_writer_beam.native_cpu_charged_delta_from_block_entry", 243),
            ("native_original_nmi_writer_beam.native_host_frame", 5782),
            ("native_original_nmi_writer_beam.stack_word_saved", "4042"),
            ("native_original_nmi_writer_beam.framework_beam_hpos", "oops"),
        ):
            native = copy.deepcopy(NATIVE)
            obj, member = (key.split(".", 1) + [None])[:2]
            if member is None:
                native[obj] = value
            else:
                native[obj][member] = value
            with self.subTest(native=key):
                with self.assertRaises(ValueError):
                    cross.summarize(ORIGINAL, native)


if __name__ == "__main__":
    unittest.main()

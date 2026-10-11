"""No-credit crosswalk between separately authenticated Switcher NMI clocks."""
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
    "saved_4042_original_pha_horizontal_clock": {
        "original_cpu_frame_before": 5780,
        "ppu_vcounter_before": 225,
        "original_pha_pc": "00:858E",
        "accumulator_before": "4042",
        "stack_pointer_before": "01DE",
        "source_original_cpu_hcounter_before": 816,
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
        self.assertEqual(data["paired_report_bytes_sha256"], "a" * 64)

    def test_matching_raw_horizontal_number_is_still_not_phase_proof(self):
        native = copy.deepcopy(NATIVE)
        native["native_original_nmi_writer_beam"]["framework_beam_hpos"] = 816
        data = cross.summarize(ORIGINAL, native)
        self.assertEqual(data["raw_horizontal_numeric_difference_native_minus_original"], 0)
        self.assertTrue(data["matching_scanline_alone_is_not_causal_parity"])
        self.assertTrue(data["clock_unit_origin_and_execution_phase_equivalence_not_proven"])

    def test_invalid_source_or_native_writer_never_crosswalks(self):
        for key, value in (
            ("schema", "incorrect"),
            ("source_hcounter_vs_native_framework_hpos_unaligned", False),
            ("saved_4042_original_pha_horizontal_clock.original_cpu_frame_before", 5781),
            ("saved_4042_original_pha_horizontal_clock.accumulator_before", "4004"),
            ("saved_4042_original_pha_horizontal_clock.original_pha_pc", "80:858F"),
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

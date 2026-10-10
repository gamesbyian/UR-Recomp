"""QA-01 independently captured native/original Switcher result stack writer witness."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "analysis/data/switcher-native-stack-actual-writers-20261010.json"
ORIGINAL = ROOT / "analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json"


class NativeSwitcherStackSourceWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(NATIVE.read_text(encoding="utf-8"))
        cls.original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.native = cls.evidence["actual_native_stack_writer_window"]

    def test_actual_original_native_run_and_artifact_identity(self):
        e, p = self.evidence, self.evidence["reproducibility"]
        self.assertEqual(e["schema"], "UR-QA01-SWITCHER-PAIRED-NATIVE-STACK-SOURCE-TRACE/1")
        self.assertEqual(p["actual_one_shot_workflow_run"], 38090897908)
        self.assertEqual(p["actual_one_shot_job"], 114326935017)
        self.assertEqual(p["artifact_id"], 11684141556)
        self.assertEqual(p["artifact_zip_sha256"],
                         "9b202ec36bfd60dc1cece9e0d2c9027275d669f8ab4100d349c69848f250eaf9")
        self.assertEqual(p["native_framework_pin"],
                         "baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709")
        self.assertTrue(p["input_unchanged"])
        self.assertEqual(e["confidence_limits"]["complete_event_release_credit"], 0)

    def test_genuine_5782_original_native_result_qualifier_still_fails_strict_parity(self):
        e = self.evidence["independent_original_native"]
        self.assertEqual(e["course_id"], "course:04")
        self.assertEqual(e["original_source_result_movie_host"], 17030)
        self.assertEqual(e["original_guest_result_relative_frame"], 4704)
        self.assertEqual(e["native_guest_result_relative_frame"], 4702)
        self.assertEqual(e["actual_original_native_same_host_frame"], 5782)
        self.assertEqual(e["native_result_host_frame"], 5783)
        self.assertEqual(e["reference_result_host_frame"], 5783)
        for name in ("authentic_rendered_result_text_matched",
                     "original_native_terminal_menu_both_true",
                     "real_positive_timed_race_result_both_true",
                     "both_guests_outside_active_race"):
            with self.subTest(name=name):
                self.assertIs(e[name], True)
        self.assertIs(e["strict_guest_relative_result_frame_matched"], False)
        self.assertEqual(e["release_event_credit"], 0)

    def test_exhaustive_native_write_attempts_are_not_original_change_scope_counts(self):
        n = self.native
        counts = n["counts_by_wram_address"]
        self.assertEqual(sum(counts.values()), 32333)
        self.assertEqual(n["total_guest_wram_write_attempts"], 32333)
        self.assertEqual(counts["7E:01DD"], 1)
        self.assertEqual(counts["7E:01E6"], 11)
        self.assertEqual(counts["7E:01E7"], 146)
        self.assertEqual(counts["7E:01F1"], 8378)
        self.assertEqual(counts["7E:01F2"], 8007)
        self.assertEqual(counts["7E:01F3"], 5017)
        self.assertEqual(n["counts_by_generated_function_or_interpreter_scope"]
                         ["7E:01DD"], {"I_NMI_M1X1": 1})
        self.assertEqual(n["counts_by_generated_function_or_interpreter_scope"]
                         ["7E:01E6"]["Text_FormatRaceTime_FastRom_M0X0"], 7)
        self.assertEqual(n["counts_by_generated_function_or_interpreter_scope"]
                         ["7E:01F1"]["Res_LoadToVram_B1F2_M1X0"], 2774)
        self.assertEqual(n["counts_by_generated_function_or_interpreter_scope"]
                         ["7E:01F1"]["Snd_SendQueuedCommand_M1X0"], 4830)
        self.assertEqual(sum(n["logged_native_writer_frames"].values()), 32333)
        self.assertEqual(min(map(int,n["logged_native_writer_frames"])), 5775)
        self.assertEqual(max(map(int,n["logged_native_writer_frames"])), 5788)
        self.assertEqual(n["snes_frame_counter_end"], 5790)
        self.assertEqual(n["snes_frame_counter_start"], 5775)
        self.assertEqual(self.original["observed"]["original_bounded_opcode_scope_write_events"],
                         13709)
        self.assertNotEqual(n["total_guest_wram_write_attempts"],
                            self.original["observed"]["original_bounded_opcode_scope_write_events"])

    def test_native_return_byte_samples_match_original_jsr_low_addresses(self):
        events = self.native["first_five_actual_write_attempts_per_address"]["7E:01F1"]
        self.assertGreaterEqual(len(events), 4)
        self.assertIn("F4", {e["written_byte"] for e in events})
        self.assertIn("FB", {e["written_byte"] for e in events})
        self.assertTrue(any("Res_LoadToVram_B1F2" in e["native_scope"] for e in events))
        original = self.original["observed"]["dominant_01f1_jsr_source_pcs"]
        low_return_bytes = {s["observed_byte_after"] for s in original}
        self.assertEqual(low_return_bytes, {"F4", "FB"})
        for site in original:
            self.assertEqual(int(site["return_pc"].split(":")[1],16)&255,
                             int(site["observed_byte_after"],16))
        self.assertTrue(all(e["native_interpreter_pc_scope"] == "000000" for e in events))
        self.assertTrue(self.evidence["confidence_limits"]
                        ["native_generated_function_scope_not_exact_instruction_pc"])

    def test_01dd_native_nmi_scope_is_not_claimed_as_original_writer(self):
        row = self.native["first_five_actual_write_attempts_per_address"]["7E:01DD"]
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0]["native_frame"], 5781)
        self.assertEqual(row[0]["native_scope"], "I_NMI_M1X1")
        self.assertEqual(row[0]["native_cpu_sp"], "01DD")
        self.assertEqual(row[0]["word_width"], 2)
        self.assertNotIn("7E:01DD", self.original["observed"]["target_address_change_counts"])
        self.assertTrue(self.evidence["confidence_limits"]
                        ["exact_source_original_native_5782_stack_pointer_pair_not_captured"])
        self.assertEqual(self.evidence["confidence_limits"]["total_usa_events"],45)


if __name__ == "__main__":
    unittest.main()

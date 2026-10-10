"""Source-verified Switcher restoration occurs at same host frame; zero release credit."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "analysis/data/switcher-original-native-restoration-same-host-20261010.json"


class SwitcherOriginalNativeRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(DOC.read_text(encoding="utf-8"))

    def test_real_artifact_provenance_and_strict_nonadmission(self):
        d = self.report
        self.assertEqual(d["schema"], "UR-QA01-SWITCHER-ORIGINAL-NATIVE-RESTORATION/1")
        self.assertEqual(d["provenance"]["original_native_run_id"], 38073881560)
        self.assertEqual(d["provenance"]["original_native_artifact_id"], 11678416824)
        self.assertEqual(
            d["provenance"]["artifact_zip_sha256"],
            "a6e40d7fc26e89ebced6e46e243eb6582d1edea7b77f6ed21b9cb1e78a3510af")
        self.assertEqual(
            d["provenance"]["contained_switcher_report_sha256"],
            "d8ea314f560b6bbec0548d5b65bb171ccac08975f73f02a65084634d1e7b60f3")
        self.assertTrue(d["provenance"]["one_shot_pr_closed_unmerged"])
        self.assertEqual(d["acceptance"]["release_usa_courses_accepted"], 0)
        self.assertEqual(d["acceptance"]["total_usa_courses"], 45)
        self.assertTrue(d["acceptance"]["do_not_shift_source_input"])
        self.assertFalse(d["acceptance"]["guest_relative_terminal_matched"])

    def test_restore_host_identity_but_distinct_guest_age(self):
        d = self.report["observed"]
        restore = d["restore_transition"]
        self.assertEqual(d["original_guest_entry_host"], 1079)
        self.assertEqual(d["native_guest_entry_host"], 1081)
        self.assertEqual(restore["reference_last_stage_relative"], 4698)
        self.assertEqual(restore["reference_first_restored_relative"], 4699)
        self.assertEqual(restore["native_last_stage_relative"], 4696)
        self.assertEqual(restore["native_first_restored_relative"], 4697)
        self.assertEqual(d["original_guest_entry_host"]
                         + restore["reference_first_restored_relative"], 5778)
        self.assertEqual(d["native_guest_entry_host"]
                         + restore["native_first_restored_relative"], 5778)
        self.assertEqual(restore["restored_course_track"], 3)
        self.assertEqual(restore["restored_menu"], 22)
        self.assertEqual(
            restore["reference_native_same_absolute_host_frames_with_all_sampled_fields_identical"],
            [5778, 5779, 5780])
        for row in restore["cross_guest_same_host_pairs"]:
            self.assertEqual(
                d["original_guest_entry_host"] + row["original_relative"],
                row["host"])
            self.assertEqual(
                d["native_guest_entry_host"] + row["native_relative"],
                row["host"])
        self.assertEqual(
            [r["host"] for r in restore["cross_guest_same_host_pairs"]],
            [5778, 5779, 5780])
        self.assertEqual(d["actual_observed_guest_relative_samples"], 46)

    def test_first_menu_handoff_has_real_one_host_frame_offset(self):
        d = self.report["observed"]
        first = d["first_transition"]
        self.assertEqual(first["reference_first_stage_relative"], 4665)
        self.assertEqual(first["native_first_stage_relative"], 4664)
        self.assertEqual(
            d["original_guest_entry_host"] + first["reference_first_stage_relative"],
            5744)
        self.assertEqual(
            d["native_guest_entry_host"] + first["native_first_stage_relative"],
            5745)

    def test_relative_end_state_is_not_same_host_comparison(self):
        d = self.report["observed"]
        last = d["final_boundary"]
        self.assertEqual(last["relative_frame"], 4701)
        self.assertEqual(last["reference_in_race"], 1)
        self.assertEqual(last["native_in_race"], 0)
        self.assertEqual(last["reference_host_frame"], 5780)
        self.assertEqual(last["native_host_frame"], 5782)
        self.assertNotEqual(last["reference_host_frame"], last["native_host_frame"])
        self.assertEqual(
            d["original_result_host"],
            d["native_result_host"])
        self.assertEqual(d["original_result_host"], 5783)
        self.assertEqual(d["player_one_time"], "1:08.81")
        self.assertTrue(d["original_native_settled_result_text_equal"])
        self.assertFalse(self.report["acceptance"]["guest_relative_terminal_matched"])


if __name__ == "__main__":
    unittest.main()

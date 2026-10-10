"""Pin the executed original/native Switcher Race B result, not a release pass."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OBSERVED = (ROOT / "analysis/data/"
            "switcher-original-baldosa-paired-race-b-result-20261010.json")


class OriginalNativeSwitcherResultEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(OBSERVED.read_text(encoding="utf-8"))

    def test_actual_run_fingerprints_and_zero_course_admission(self):
        d = self.doc
        self.assertEqual(
            d["schema"], "UR-QA01-ORIGINAL-BALDOSA-SWITCHER-RACE-B-RESULT/1")
        self.assertEqual(d["execution"]["workflow_run_id"], 38064406315)
        self.assertEqual(d["execution"]["artifact_id"], 11674751560)
        self.assertEqual(
            d["execution"]["artifact_zip_sha256"],
            "1a1a8a67fd5809255f5606028821325ea515c942759cca50fb960d28e53780bc")
        self.assertEqual(
            d["execution"]["report_sha256"],
            "1c33ca0d4ac3415a33e06cf2d73cc880bffed5806014fde35cc348b705dbaa20")
        self.assertEqual(d["execution"]["job_conclusion"], "failure")
        self.assertFalse(d["execution"]["source_pr_merged"])
        self.assertTrue(d["execution"]["source_pr_closed"])
        self.assertEqual(d["provenance"]["course_id"], "course:04")
        self.assertEqual(d["release"], {
            "usa_accepted_events": 0, "usa_total_events": 45, "qa_credit": 0})

    def test_guest_relative_two_frame_gap_and_identical_absolute_result_onset(self):
        x = self.doc["independently_observed_replay"]
        self.assertEqual(x["reference_entry_absolute_host_frame"], 1079)
        self.assertEqual(x["native_entry_absolute_host_frame"], 1081)
        self.assertEqual(x["reference_result_guest_relative_frame"], 4704)
        self.assertEqual(x["native_result_guest_relative_frame"], 4702)
        self.assertEqual(
            x["reference_entry_absolute_host_frame"] +
            x["reference_result_guest_relative_frame"], 5783)
        self.assertEqual(
            x["native_entry_absolute_host_frame"] +
            x["native_result_guest_relative_frame"], 5783)
        self.assertTrue(x["terminal_absolute_host_result_frame_matched"])
        self.assertFalse(x["terminal_guest_relative_result_frame_matched"])
        self.assertFalse(x["full_event_parity_admitted"])

    def test_real_scored_p1_finish_and_sparse_samples_do_not_launder_parity(self):
        x = self.doc["independently_observed_replay"]
        self.assertEqual(x["player_one_time"], "1:08.81")
        self.assertEqual(
            x["identical_result_screen_text_stable"],
            ["SWITCHER", "COMPLETE", "PLAYER     TIME", "MIKE",
             "1:08.81", "SOMEONE", "NO TIME", "SOMEONE", "NO TIME",
             "SOMEONE", "NO TIME"])
        self.assertEqual(x["identical_result_screen_text_onset"], ["T"])
        self.assertEqual(x["original_final_guest"], x["native_final_guest"])
        self.assertEqual(x["original_final_guest"]["p1_laps"], 0)
        self.assertEqual(x["original_final_guest"]["p1_finish_gate"], 1)
        self.assertEqual(x["active_sample_count"], 28)
        self.assertEqual(x["active_latest_relative_frame"], 2400)
        self.assertTrue(x["sampled_active_semantic_fields_equal"])
        self.assertIsNone(x["first_sample_disagreement"])
        self.assertLess(
            x["active_latest_relative_frame"],
            x["native_result_guest_relative_frame"] - 2000)
        self.assertFalse(x["full_event_parity_admitted"])

    def test_original_source_exception_remains_origin_only(self):
        d = self.doc
        self.assertEqual(d["original_source"]["original_movie_course_entry_frame"],
                         12327)
        self.assertEqual(d["original_source"]["original_movie_result_frame"],
                         17030)
        self.assertEqual(
            d["original_source"]["original_only_terminal_prelude"],
            "switcher_34_frame_track0_terminal_prelude")
        self.assertEqual(
            d["independently_observed_replay"]["reference_result_stable_absolute_host_frame"],
            d["independently_observed_replay"]["native_result_stable_absolute_host_frame"])
        self.assertEqual(d["release"]["qa_credit"], 0)


if __name__ == "__main__":
    unittest.main()

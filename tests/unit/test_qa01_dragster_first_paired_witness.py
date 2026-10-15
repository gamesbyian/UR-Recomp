"""Source-bound original/native Dragster result proof, never release approval.

The real pinned GitHub CI artifact is separately SHA-bound in the JSON.
These tests check recorded identities, source-screen congruence, first
scientific mismatch and the still-unmodified 45-USA census.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "analysis/data/qa01-dragster-2014-original-baldosa-first-pair-20261014.json"


class OriginalNativeDragsterWitnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(DATA.read_text(encoding="utf-8"))

    def test_exact_executed_source_and_artifact_are_pinned(self):
        r = self.report
        self.assertEqual(r["schema"],
                         "UR-QA01-2014-DRAGSTER-ORIGINAL-BALDOSA-FIRST-PAIR/1")
        src = r["source"]
        self.assertEqual(src["run_id"], 38665417679)
        self.assertEqual(src["job_id"], 116196139737)
        self.assertEqual(src["github_pr"], 1617)
        self.assertEqual(src["actual_job_conclusion"], "success")
        self.assertEqual(src["producer_exit_code"], 1)
        for name in ("artifact_zip_sha256", "member_sha256",
                     "source_event_diagnostic_member_sha256",
                     "reference_log_member_sha256",
                     "native_log_member_sha256"):
            self.assertRegex(src[name], r"^[0-9a-f]{64}$")
        for key, value in r["identities"].items():
            if key.endswith("_sha256"):
                self.assertRegex(value, r"^[0-9a-f]{64}$")
        self.assertFalse(r["identities"]["rf015_dram_refresh_correction_applied"])

    def test_actual_original_movie_and_fresh_entry_frames_are_distinct(self):
        t = self.report["event"]
        self.assertEqual((t["course_id"], t["family"]), ("course:01", "race-a"))
        self.assertEqual((t["original_source_movie_entry"],
                          t["original_source_movie_result"]), (794, 2874))
        self.assertEqual(t["original_source_elapsed_to_result"], 2874 - 794)
        self.assertEqual(t["source_original_foreign_active_runs_before_result"], 0)
        self.assertEqual((t["fresh_reference_entry_host"],
                          t["fresh_native_entry_host"]), (945, 945))
        self.assertEqual(t["calibrated_native_minus_reference_shift"], 0)
        self.assertEqual(t["fresh_reference_result_relative"], 2081)
        self.assertEqual(t["fresh_native_result_relative"], 2079)
        self.assertEqual(t["fresh_reference_result_host"], 945 + 2081)
        self.assertEqual(t["fresh_native_result_host"], 945 + 2079)
        self.assertEqual(t["native_result_onset_lead_in_guest_frames"], 2)
        self.assertFalse(t["result_onset_guest_relative_frame_equal"])
        self.assertFalse(t["strict_paired_event_candidate"])

    def test_real_original_screen_and_dense_semantic_result_both_match(self):
        movie_result = json.loads((ROOT / "analysis/generated/result-screens-probe.json")
                                  .read_text(encoding="utf-8"))
        source = next(z for z in movie_result["result_runs"]
                      if z["start"] == 2874)
        self.assertEqual(source["menu"], "0x99")
        self.assertEqual(source["state"], "RESULT_RACE")
        self.assertEqual(source["dump_frame"], 2883)
        self.assertIn("DRAGSTER", source["texts"])
        self.assertIn("MIKE", source["texts"])
        self.assertIn("0:25.08", source["texts"])
        case = self.report["event"]
        self.assertEqual(case["source_result_menu_hex"], "99")
        self.assertEqual(case["active_semantic_samples_per_guest"], 22)
        self.assertTrue(case["active_semantic_samples_all_equal"])
        self.assertTrue(case["fresh_original_source_entry_equivalent"])
        self.assertTrue(case["fresh_original_native_entry_equivalent"])
        self.assertTrue(case["reference_and_native_settled_result_ppu_text_equal"])
        self.assertEqual(case["settled_p1_total"], "0:25.08")
        self.assertEqual((case["p1_laps_remaining_at_result"],
                          case["p1_checkpoint_at_result"],
                          case["p1_finish_gate_at_result"]), (0, 1, 1))
        self.assertFalse(case["strict_paired_event_candidate"])
        self.assertTrue(case["postresult_menu_progression_and_battery_persistence_unverified"])

    def test_qa01_45_event_release_authority_does_not_change(self):
        official = json.loads((ROOT / "analysis/data/course-event-runtime-evidence.json")
                              .read_text(encoding="utf-8"))
        observations = [o for o in official["observations"]
                        if o["rom"] == "usa-retail"]
        dragster = next(o for o in observations if o["course_id"] == "course:01")
        self.assertEqual(dragster["status"], "partial")
        self.assertFalse(any(o["status"] == "passed" for o in observations))
        release = self.report["release"]
        self.assertEqual(release["accepted_primary_usa_events_before_and_after"], 0)
        self.assertEqual(release["primary_usa_denominator"], 45)
        self.assertEqual((release["official_partial_usa_events"],
                          release["official_unverified_usa_events"]), (4, 41))
        self.assertEqual(release["independent_completed_event_credit"], 0)


if __name__ == "__main__":
    unittest.main()

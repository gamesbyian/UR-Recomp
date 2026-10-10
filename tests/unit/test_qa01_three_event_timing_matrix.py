"""Cross-event original/native result timing identity, with zero USA release credit."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "analysis/data/qa01-three-event-original-baldosa-timing-matrix-20261010.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ThreeOriginalNativeEventTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = read(DOC)
        cls.items = {x["course_id"]: x for x in cls.matrix["entries"]}

    def test_three_distinct_original_native_events_never_launder_qa_admission(self):
        self.assertEqual(set(self.items), {"course:02", "course:03", "course:04"})
        self.assertEqual(self.matrix["schema"], "UR-QA01-THREE-EVENT-TIMING-MATRIX/1")
        self.assertEqual(self.matrix["acceptance"], {
            "complete_event_usa_accepted": 0, "denominator": 45,
            "release_credit_derived": 0})
        self.assertTrue(all(x["result_text_equal"] for x in self.items.values()))

    def test_every_record_has_consistent_independently_observed_host_result(self):
        for entry in self.matrix["entries"]:
            with self.subTest(course=entry["course_id"]):
                self.assertEqual(entry["original_entry_host"]
                                 + entry["original_result_guest_relative"],
                                 entry["original_result_host"])
                self.assertEqual(entry["native_entry_host"]
                                 + entry["native_result_guest_relative"],
                                 entry["native_result_host"])
                self.assertEqual(
                    entry["entry_delta_native_minus_original"]
                    + entry["terminal_guest_relative_delta_native_minus_original"],
                    entry["terminal_absolute_host_delta_native_minus_original"])
                self.assertGreater(
                    entry["entry_delta_native_minus_original"], 0)
                self.assertLess(
                    entry["terminal_guest_relative_delta_native_minus_original"], 0)
                self.assertTrue(entry["evidence_limitation"])

    def test_original_zoo_result_observations_match_pinned_actual_source(self):
        item = self.items["course:02"]
        source = read(ROOT / item["source_witness"])
        self.assertEqual(source["source"]["workflow_run"], item["original_event_run"])
        self.assertEqual(source["source"]["scene_entry_original_frame"],
                         item["original_entry_host"])
        self.assertEqual(source["source"]["scene_entry_native_frame"],
                         item["native_entry_host"])
        observed = source["observed_original_native_event"]
        self.assertEqual(observed["result_menu_0xBC_first_observed_relative_frame"],
                         {"original": item["original_result_guest_relative"],
                          "native": item["native_result_guest_relative"]})
        self.assertTrue(observed["both_settled_original_native_result_ppu_text_identical"])
        self.assertEqual(source["complete_event_qa_credit"], 0)

    def test_original_bowl_result_observations_match_pinned_actual_source(self):
        item = self.items["course:03"]
        source = read(ROOT / item["source_witness"])
        self.assertEqual(source["source"]["run_id"], item["original_event_run"])
        self.assertEqual(source["source"]["artifact_id"], item["artifact_id"])
        w = source["scored_stunt"]
        for k in ("reference_entry", "native_entry", "reference_relative_result",
                  "native_relative_result"):
            mapped = {
                "reference_entry": "original_entry_host",
                "native_entry": "native_entry_host",
                "reference_relative_result": "original_result_guest_relative",
                "native_relative_result": "native_result_guest_relative",
            }[k]
            self.assertEqual(w[k], item[mapped])
        self.assertEqual(w["source_result_host_frame"], item["original_result_host"])
        self.assertFalse(w["complete_event_frame_parity"])
        self.assertEqual(source["release_complete_usa_courses_credited"], 0)

    def test_original_switcher_real_paired_result_against_pinned_actual_source(self):
        item = self.items["course:04"]
        source = read(ROOT / item["source_witness"])
        self.assertEqual(source["execution"]["workflow_run_id"], item["original_event_run"])
        self.assertEqual(source["execution"]["artifact_id"], item["artifact_id"])
        o = source["independently_observed_replay"]
        self.assertEqual(o["reference_entry_absolute_host_frame"],
                         item["original_entry_host"])
        self.assertEqual(o["native_entry_absolute_host_frame"],
                         item["native_entry_host"])
        self.assertEqual(o["reference_result_guest_relative_frame"],
                         item["original_result_guest_relative"])
        self.assertEqual(o["native_result_guest_relative_frame"],
                         item["native_result_guest_relative"])
        self.assertEqual(o["reference_result_onset_absolute_host_frame"],
                         item["original_result_host"])
        self.assertEqual(o["native_result_onset_absolute_host_frame"],
                         item["native_result_host"])
        self.assertTrue(o["rendered_result_and_score_text_matched"]
                        if "rendered_result_and_score_text_matched" in o
                        else o["identical_result_screen_text_stable"][4] == "1:08.81")
        terminal = read(ROOT / item["terminal_source_witness"])
        self.assertEqual(terminal["provenance"]["original_native_run_id"],
                         item["terminal_probe_run"])
        self.assertEqual(terminal["provenance"]["artifact_id"],
                         item["terminal_artifact_id"])
        self.assertEqual(terminal["strict_acceptance"]["release_credit"], 0)
        self.assertFalse(o["full_event_parity_admitted"])


if __name__ == "__main__":
    unittest.main()

"""Independent original Dragster first-race result: no same-input native parity."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from correlate_dragster_finish_spatial_event import surface_slot
from probe_course_checkpoint_placements import ROM, USA_SHA256
from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1

ORIGINAL = ROOT / "analysis/data/dragster-original-2014-race-result.json"
NATIVE = ROOT / "analysis/data/dragster-finish-contact-transition.json"
CATALOG = ROOT / "analysis/data/course-corpus.json"


class OriginalDragsterResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.native = json.loads(NATIVE.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_source_and_complete_original_menu_path_only(self):
        r = self.reference
        self.assertEqual(r["course"]["id"], "course:01")
        self.assertEqual(r["provenance"]["workflow_run_id"], 37184022134)
        self.assertEqual(r["provenance"]["artifact_id"], 11296685866)
        self.assertEqual(r["provenance"]["raw_trace_record_count"], 669690)
        self.assertEqual(r["provenance"]["raw_trace_sha256"],
                         "5fc0e88c89d2dc35b945a2c1f37f522fe8ba3090ea64a0efe50e1748b39f93ab")
        self.assertEqual(r["reference_first_active"]["frame"], 794)
        self.assertEqual(r["result_screen_entered_frame"], 2874)
        self.assertEqual(r["original_result_transition"], [
            {"frame": 2835, "field": "menu", "from": 0, "to": 132},
            {"frame": 2869, "field": "menu", "from": 132, "to": 22},
            {"frame": 2873, "field": "in_race", "from": 1, "to": 0},
            {"frame": 2874, "field": "menu", "from": 22, "to": 153},
        ])
        self.assertFalse(r["native_comparison"]["same_input_run_or_scene_aligned"])

    def test_original_start_matches_header_x_not_completely_identical_y(self):
        first = self.reference["reference_first_active"]
        header = self.catalog["courses"][0]["header"]["spawn_or_landmark_a"]
        self.assertEqual(first["p1_xy"], [1088, 801])
        self.assertEqual([v * 16 for v in header], [1088, 800])
        self.assertEqual(first["laps_remaining"], 2)

    def test_original_three_transitions_and_no_lap_award_at_intermediate_checkpoint(self):
        events = self.reference["original_events"]
        self.assertEqual([r["frame"] for r in events], [1031, 1772, 2505])
        self.assertEqual([r["before"] for r in events],
                         [[0, 0, 2], [1, 1, 1], [3, 0, 1]])
        self.assertEqual([r["after"] for r in events],
                         [[1, 1, 1], [3, 0, 1], [1, 1, 0]])
        self.assertEqual(events[0]["timer_raw"], [0, 0, 0, 5, 2])
        self.assertEqual(events[-1]["timer_raw"], [0, 2, 5, 1, 0])
        self.assertEqual(
            [x["frame"] for x in events if x["before"][2] != x["after"][2]],
            [1031, 2505],
        )
        self.assertEqual(events[-1]["frame"] - events[0]["frame"], 1474)
        addresses = ["0EF1", "1199", "119D"]
        for row in events:
            self.assertEqual(
                row["writes"],
                [[k, before, after] for k, before, after
                 in zip(addresses, [row["before"][2], row["before"][0], row["before"][1]],
                        [row["after"][2], row["after"][0], row["after"][1]])
                 if before != after],
            )
            self.assertIsInstance(surface_slot(int(row["prior_postframe_p1_contact_hex"], 16)),
                                  (int, type(None)))

    def test_native_dragster_transition_is_only_a_same_shape_comparison(self):
        reference_last = self.reference["original_events"][-1]
        native_events = self.native["samples"]
        native_prior = next(x for x in native_events if x["frame"] == 2902)
        native_after = next(x for x in native_events if x["frame"] == 2903)
        native_before = [native_prior[x] for x in
                         ("checkpoint", "finish_gate", "laps_remaining")]
        native_after_state = [native_after[x] for x in
                              ("checkpoint", "finish_gate", "laps_remaining")]
        self.assertEqual(reference_last["before"], native_before)
        self.assertEqual(reference_last["after"], native_after_state)
        self.assertNotEqual(reference_last["frame"], native_after["frame"])
        self.assertFalse(self.reference["native_comparison"]["same_input_run_or_scene_aligned"])
        self.assertFalse(self.reference.get("native_reference_same_input_parity", False))
        self.assertNotEqual(
            int(reference_last["prior_postframe_p1_contact_hex"], 16),
            native_prior["collision_word"],
        )


if __name__ == "__main__":
    unittest.main()

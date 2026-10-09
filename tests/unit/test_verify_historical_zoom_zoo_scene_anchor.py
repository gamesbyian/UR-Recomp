"""Negative-source guards for archived 2014 original Zoom Zoo phase anchor."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_historical_zoom_zoo_scene_anchor as mod


class ZoomZooHistoricalAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads(mod.METADATA.read_text(encoding="utf-8"))
        cls.reference = json.loads(mod.REFERENCE.read_text(encoding="utf-8"))
        cls.replay = json.loads(mod.REPLAY.read_text(encoding="utf-8"))

    def test_recovered_original_second_race_is_track_one_not_native_frame_parity(self):
        result = mod.build(self.meta, self.reference, self.replay)
        ref = result["reference_only"]
        self.assertEqual(ref["second_race_entry_candidate"], 3190)
        self.assertEqual(ref["first_race_results"], 2874)
        self.assertEqual(ref["verified_track_id"], 1)
        self.assertEqual(ref["course_id"], "course:02")
        self.assertEqual(ref["subsequent_track_verified_at_frames"],
                         [3400, 3800, 4200, 4600, 5000])
        self.assertFalse(
            result["prior_absolute_native_alignment"]["valid_for_guest_physics_parity"]
        )
        self.assertEqual(
            result["prior_absolute_native_alignment"]["same_movie_frame_3400_reference_in_race_track"],
            [1, 1],
        )
        self.assertIn("No complete race", result["scope"])

    def test_change_original_entry_boundary_fails_closed(self):
        ref = copy.deepcopy(self.reference)
        ref["in_race_transitions"][-1]["frame"] = 3189
        with self.assertRaisesRegex(mod.SceneAnchorError, "entries"):
            mod.build(self.meta, ref, self.replay)

    def test_other_course_and_missing_samples_cannot_be_promoted(self):
        replay = copy.deepcopy(self.replay)
        row = next(x for x in replay["sampled_mismatches"] if x["frame"] == 3400)
        row["reference"][2] = 0
        with self.assertRaisesRegex(mod.SceneAnchorError, "Zoom Zoo"):
            mod.build(self.meta, self.reference, replay)
        replay = copy.deepcopy(self.replay)
        replay["sampled_mismatches"] = [
            x for x in replay["sampled_mismatches"] if x["frame"] != 3800
        ]
        with self.assertRaisesRegex(mod.SceneAnchorError, "incomplete"):
            mod.build(self.meta, self.reference, replay)

    def test_mismatched_metadata_or_reference_source_is_rejected(self):
        meta = dict(self.meta, uid=12)
        with self.assertRaisesRegex(mod.SceneAnchorError, "identity"):
            mod.build(meta, self.reference, self.replay)
        ref = dict(self.reference, source_movie="unrelated.smv")
        with self.assertRaisesRegex(mod.SceneAnchorError, "source"):
            mod.build(self.meta, ref, self.replay)


if __name__ == "__main__":
    unittest.main()

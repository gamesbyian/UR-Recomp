"""ROM-free provenance and negative-control tests for authored ride-grid motion."""
import copy
import unittest

from tools.art.study_original_racer_continuous_ride_motion import (
    SOURCE_RIG_SHA, TIMES, validate_sample_receipt,
    summarize_candidate, original_edges,
)


class RideSourceMotionTests(unittest.TestCase):
    def fixture(self):
        sha = "4c2ecc8f3a226486d363d5987a08f79bbbbf5606ab12de85a719c52cf35e6eac"
        qualified = {
            "schema": "UR-ART4K-REAL-CONTINUOUS-SOURCE-GLB-RECEIPT/1",
            "rig_pose": "ride", "rig_time": 0.25,
            "model_source_sha256": SOURCE_RIG_SHA,
            "part_parent_count": 5,
            "part_material_mesh_count": 16,
            "source_owned_pivots_validated_against_real_GLB": True,
            "authored_continuous_source_kinematics_recomputed": True,
            "1994_source_cadence_or_pose_paired": False,
            "1994_source_camera_or_rig_recovered": False,
            "owner_character_likeness_approved": False,
            "shipping_art_approved": False,
            "GLB_sha256": sha,
        }
        current = {
            "attempt_id": "abc",
            "source_sha256": SOURCE_RIG_SHA, "rig_pose": "ride",
            "glb_sha256": sha,
            "glb_path": "attempts/abc/unicycle_articulated_blockout.glb",
        }
        last = {
            "attempt_id": "abc", "source_sha256": SOURCE_RIG_SHA,
            "status": "succeeded", "current_output_usable": True,
            "glb_sha256": sha,
        }
        return qualified, current, last

    def test_pinned_actual_source_and_artifact_contract(self):
        q, c, l = self.fixture()
        self.assertEqual(validate_sample_receipt(q, c, l, "0.25"),
                         "attempts/abc/unicycle_articulated_blockout.glb")
        self.assertEqual(TIMES, ("0.0", "0.25", "0.5", "0.75", "1.0"))

    def test_wrong_sample_provenance_rejected(self):
        for obj, field, invalid in (
            ("q", "rig_pose", "stunt_cycle"),
            ("q", "rig_time", 0.5),
            ("q", "model_source_sha256", "0" * 64),
            ("q", "part_parent_count", 4),
            ("q", "part_material_mesh_count", 17),
            ("q", "1994_source_cadence_or_pose_paired", True),
            ("q", "shipping_art_approved", True),
            ("q", "GLB_sha256", "0" * 64),
            ("c", "glb_path", "../foreign.glb"),
            ("c", "glb_path", "attempts/alien/model.glb"),
            ("c", "attempt_id", "alien"),
            ("c", "source_sha256", "0" * 64),
            ("l", "status", "failed"),
            ("l", "current_output_usable", False),
        ):
            q, c, l = self.fixture()
            mapping = {"q": q, "c": c, "l": l}
            mapping[obj][field] = invalid
            with self.subTest(key=(obj, field)), self.assertRaises(ValueError):
                validate_sample_receipt(q, c, l, "0.25")

    def test_unexpected_sample_time_fails(self):
        q, c, l = self.fixture()
        with self.assertRaises(ValueError):
            validate_sample_receipt(q, c, l, "0.6")

    def test_original_source_frames_never_join_across_missing_guest_frames(self):
        # This is an executable negative check of the core ordering rules,
        # though a deliberately small fixture must reject the 109-edge census.
        corpus = {
            "source_representations": {
                "a": {"player": "p1", "source_binary_mask_sha256": "a"},
                "b": {"player": "p2", "source_binary_mask_sha256": "b"},
            },
            "source_temporal_frame_observations": [
                {"window": "first", "guest_frame": 1205,
                 "representations": {"p1": "a", "p2": "b"}},
                {"window": "first", "guest_frame": 1207,
                 "representations": {"p1": "a", "p2": "b"}},
            ],
        }
        with self.assertRaises(ValueError):
            original_edges(corpus, {"a": None, "b": None})

    def test_source_hold_false_motion_cannot_disappear_from_metrics(self):
        rows = []
        for i in range(109):
            moving = i < 19
            count = (85 if i < 18 else 101) if moving else 0
            rows.append({
                "original_source_binary_silhouette_changed": moving,
                "source_changed_pixel_count": count,
                "model_pose_only_changed_pixel_count": 10 if moving else 2,
                "source_changed_pixels_overlapping_pose_only_model_change":
                    33 if i == 0 else 0,
                "model_placed_changed_pixel_count": 20,
                "source_changed_pixels_explained_by_placed_model":
                    33 if i == 0 else 0,
                "model_pose_only_raster_changed": True,
                "model_placed_raster_changed": True,
            })
        report = summarize_candidate(rows)
        self.assertEqual(report["source_changed_pixels"], 1631)
        self.assertEqual(report["source_held_edges"], 90)
        self.assertEqual(report["model_pose_only_matching_source_changed_pixels"], 33)
        self.assertEqual(report["source_held_edges_with_spurious_pose_change"], 90)
        self.assertEqual(report["source_held_edges_with_spurious_placed_change"], 90)
        self.assertEqual(report["pose_only_source_changed_pixel_recall"], .02023299)
        bad = copy.deepcopy(rows)
        bad.pop()
        with self.assertRaises(ValueError):
            summarize_candidate(bad)


if __name__ == "__main__":
    unittest.main()

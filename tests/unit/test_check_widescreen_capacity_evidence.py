import unittest

from tools.check_widescreen_capacity_evidence import expected_depths, validate_capacity


class WidescreenCapacityEvidenceTest(unittest.TestCase):
    def test_depths_are_derived_from_margin(self):
        self.assertEqual(expected_depths(16), [1])
        self.assertEqual(expected_depths(32), [1, 2, 3])
        self.assertEqual(expected_depths(48), [1, 2, 3, 4, 5])

    def test_validates_parameterized_capacity(self):
        retained = {
            "authority": "analysis/widescreen-policy.yml",
            "fixture": "vs-first-race",
            "workflow_run_id": 1,
            "workflow_artifact_id": 2,
            "candidate_margin_pixels_per_side": 24,
            "control_frame_geometry": [256, 224],
            "protected_state_equal_at_all_checkpoints": True,
            "calibration": {
                "player1_events": 2, "player1_matches": 2, "player1_misses": 0,
                "player2_events": 1, "player2_matches": 1, "player2_misses": 0,
            },
            "host_shadow_depths": [1, 2],
            "host_shadow_events_per_depth": {"player1": 2, "player2": 1},
            "capacity_classification": "vs-plus24-live-course-capacity-proven",
            "guest_descriptor_promotion": False,
        }
        generated = {
            "capacity_classification": "vs-plus24-live-course-capacity-proven",
            "protected_state_equal_at_all_checkpoints": True,
            "control_frame_geometry": [256, 224],
            "plus24_frame_geometry": [304, 224],
        }
        log = "\n".join([
            "URWS_VS_MATERIALIZER margin=24 player=1 calibrated=1",
            "URWS_VS_MATERIALIZER margin=24 player=1 calibrated=1",
            "URWS_VS_MATERIALIZER margin=24 player=2 calibrated=1",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=1 depth=1",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=1 depth=1",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=1 depth=2",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=1 depth=2",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=2 depth=1",
            "URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player=2 depth=2",
        ])
        self.assertEqual(validate_capacity(retained, generated, log)["outcome"], "accepted")


if __name__ == "__main__":
    unittest.main()

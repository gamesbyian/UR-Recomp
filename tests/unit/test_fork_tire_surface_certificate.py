"""Adversarial ROM-free proof limits for the 2026 authored tire tubes."""
import importlib.util
import math
import unittest

AVAILABLE = importlib.util.find_spec("numpy") is not None
if AVAILABLE:
    import numpy as np
    from tools.art.fork_tire_surface_certificate import (
        certify_triangles_against_source_tori,
    )


@unittest.skipUnless(AVAILABLE, "optional numpy model-review dependency")
class ContinuousForkTubeTests(unittest.TestCase):
    def test_hidden_intersection_missed_by_sparse_samples(self):
        vertices = np.array([[4., 0, 0],
                             [-2., 0, 2 * math.sqrt(3)],
                             [-2., 0, -2 * math.sqrt(3)]])
        # Seven conventional probes all miss an interior intersection.
        sparse = np.vstack((vertices, vertices.mean(axis=0),
                            (vertices + np.roll(vertices, 1, axis=0)) / 2))
        radial = np.hypot(sparse[:, 0], sparse[:, 2])
        self.assertTrue(np.all(np.hypot(radial - .85, sparse[:, 1]) - .15 > 0))
        self.assertTrue(np.all(np.hypot(radial - .80, sparse[:, 1] + .15) - .028 > 0))
        report = certify_triangles_against_source_tori(vertices[None])
        self.assertEqual(report["status"], "penetration")
        self.assertFalse(report["continuous_fork_surface_cleared_against_ideal_tori"])

    def test_actual_028_glb_hidden_stripe_intersection(self):
        # Actual source-authored blue GLB face 161 from hosted run 42307831723.
        triangle = np.array([[[-.01999950, -.19076900, .05825230],
                              [-.09966600, -.17600299, .81185400],
                              [-.09954270, -.17598200, .81196702]]])
        v = triangle[0]
        probes = np.vstack((v, v.mean(axis=0),
                            (v + np.roll(v, 1, axis=0)) / 2))
        radial = np.hypot(probes[:, 0], probes[:, 2])
        self.assertGreater(float(np.min(
            np.hypot(radial - .80, probes[:, 1] + .15) - .028)), 0)
        report = certify_triangles_against_source_tori(triangle)
        self.assertEqual(report["status"], "penetration")
        self.assertLess(
            report["minimum_observed_center_signed_distance"]["near_sidewall_stripe"],
            -.001)

    def test_far_and_near_positive_surfaces_certified(self):
        for x, min_depth in ((2., 0), (1.005, 1)):
            patch = np.array([[[x, 0, 0], [x + .1, 0, 0], [x, 0, .1]]])
            result = certify_triangles_against_source_tori(patch)
            self.assertEqual(result["status"], "certified")
            self.assertGreaterEqual(result["depth_reached"], min_depth)
            self.assertGreater(
                result["certified_minimum_signed_distance_lower_bound"]["main_tire"], 0)
            self.assertFalse(result["continuous_actual_triangulated_tire_cleared"])
            self.assertFalse(result["stunt_pose_or_moving_clearance_proved"])

    def test_nearside_stripe_is_separate_collision_target(self):
        patch = np.array([[[.80, -.15, 0], [.805, -.15, 0],
                           [.80, -.148, .004]]])
        result = certify_triangles_against_source_tori(patch)
        self.assertEqual(result["status"], "penetration")
        self.assertGreater(result["minimum_observed_center_signed_distance"]["main_tire"], 0)
        self.assertLess(result["minimum_observed_center_signed_distance"]["near_sidewall_stripe"], 0)

    def test_rigid_transformation_preserves_result(self):
        source = np.array([[[2., 0, 0], [2.1, 0, 0], [2., .1, 0]]])
        rotation = np.array([[1., 0, 0], [0, 0, -1], [0, 1, 0]])
        frame = np.eye(4)
        frame[:3, :3], frame[:3, 3] = rotation, [2, -4, 3]
        transformed = source @ rotation.T + frame[:3, 3]
        self.assertEqual(
            certify_triangles_against_source_tori(transformed, frame)["status"],
            "certified")

    def test_exhausted_budget_never_becomes_approval(self):
        giant = np.array([[[4., 0, 0], [-2., 0, 2 * math.sqrt(3)],
                           [-2., 0, -2 * math.sqrt(3)]]])
        for budget in ({"max_depth": 0}, {"max_pending": 4}):
            result = certify_triangles_against_source_tori(giant, **budget)
            self.assertEqual(result["status"], "inconclusive")
            self.assertFalse(result["continuous_fork_surface_cleared_against_ideal_tori"])
            self.assertIsNone(result["certified_minimum_signed_distance_lower_bound"])

    def test_nonfinite_geometry_and_invalid_frame_fail_closed(self):
        triangle = np.zeros((1, 3, 3))
        for invalid in (triangle * float("nan"), np.zeros((3, 3)),
                        np.zeros((0, 3, 3))):
            with self.assertRaises(ValueError):
                certify_triangles_against_source_tori(invalid)
        shear = np.eye(4)
        shear[0, 1] = .25
        with self.assertRaisesRegex(ValueError, "rigid"):
            certify_triangles_against_source_tori(triangle, shear)
        with self.assertRaisesRegex(ValueError, "controls"):
            certify_triangles_against_source_tori(triangle, max_depth=-1)


if __name__ == "__main__":
    unittest.main()

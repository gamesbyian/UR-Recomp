"""Bounded source-owned 2026 ride grid: no inferred original 1994 cadence."""
import math
import unittest
from pathlib import Path

from tools.art.continuous_pose_recipe import continuous_pose_recipe


SOURCE = Path(__file__).resolve().parents[2] / "tools/art/candidates/unicycle_shared_rig.scad"
TIMES = (0.0, 0.25, 0.5, 0.75, 1.0)


class AuthoredRidePhaseGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_fixed_five_sample_times_recover_same_2026_authoring_contract(self):
        samples = [continuous_pose_recipe(self.source, "ride", t) for t in TIMES]
        self.assertEqual(len(samples), 5)
        for t, (pedal, lean, matrix, metadata) in zip(TIMES, samples):
            with self.subTest(phase=t):
                self.assertEqual(metadata["rig_time"], t)
                self.assertTrue(metadata["source_formula_validated"])
                self.assertEqual(metadata["continuous_pitch_degrees"], 0)
                self.assertTrue(math.isfinite(pedal))
                self.assertTrue(math.isfinite(lean))
                self.assertEqual(len(matrix), 4)
                self.assertTrue(all(len(row) == 4 and all(math.isfinite(x) for x in row)
                                    for row in matrix))

    def test_cycle_ends_at_equivalent_kinematic_controls(self):
        first = continuous_pose_recipe(self.source, "ride", TIMES[0])
        last = continuous_pose_recipe(self.source, "ride", TIMES[-1])
        self.assertAlmostEqual(first[0], last[0], places=10)
        self.assertAlmostEqual(first[1], last[1], places=10)
        self.assertEqual(last[3]["pedal_phase_unwrapped_degrees"]
                         - first[3]["pedal_phase_unwrapped_degrees"], 720)
        for row_a, row_b in zip(first[2], last[2]):
            for a, b in zip(row_a, row_b):
                self.assertAlmostEqual(a, b, places=9)

    def test_interior_samples_not_all_the_same_pose(self):
        samples = [continuous_pose_recipe(self.source, "ride", t) for t in TIMES]
        self.assertTrue(any(abs(samples[i][1] - samples[0][1]) > 1e-7
                            or any(abs(a - b) > 1e-7
                                   for ra, rb in zip(samples[i][2], samples[0][2])
                                   for a, b in zip(ra, rb))
                            for i in (1, 2, 3)))

    def test_wrong_pose_or_out_of_bounds_is_refused(self):
        for name, t in (("invented", 0.25), ("ride", -0.01),
                        ("ride", 1.01), ("ride", float("nan"))):
            with self.subTest(name=name, phase=t), self.assertRaises(ValueError):
                continuous_pose_recipe(self.source, name, t)


if __name__ == "__main__":
    unittest.main()

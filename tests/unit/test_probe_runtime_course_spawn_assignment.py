from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from probe_runtime_course_payload import rank_spawn_assignment_candidates


class CourseSpawnAssignmentTests(unittest.TestCase):
    @staticmethod
    def state(p1, p2):
        return {
            "slot1_x": p1[0], "slot1_y": p1[1],
            "slot2_x": p2[0], "slot2_y": p2[1],
        }

    def test_exact_A_to_P1_and_B_to_P2_from_unequal_pairs(self):
        result = rank_spawn_assignment_candidates(
            [99, 26], [99, 34], self.state((1584, 416), (1584, 544))
        )
        self.assertEqual(result["discriminator"], "exact_A_to_P1_B_to_P2")
        self.assertTrue(result["A_to_P1_B_to_P2"]["exact"])
        self.assertFalse(result["B_to_P1_A_to_P2"]["exact"])
        self.assertEqual(result["header_pair_world_units"]["A"], [1584, 416])

    def test_exact_swapped_assignment(self):
        result = rank_spawn_assignment_candidates(
            [99, 26], [99, 34], self.state((1584, 544), (1584, 416))
        )
        self.assertEqual(result["discriminator"], "exact_B_to_P1_A_to_P2")

    def test_identical_pairs_never_discriminate_even_if_both_match(self):
        result = rank_spawn_assignment_candidates(
            [68, 50], [68, 50], self.state((1088, 800), (1088, 800))
        )
        self.assertTrue(result["A_to_P1_B_to_P2"]["exact"])
        self.assertTrue(result["B_to_P1_A_to_P2"]["exact"])
        self.assertEqual(result["discriminator"], "uninformative_identical_header_pairs")

    def test_nonzero_race_motion_does_not_promote_nearest_mapping(self):
        result = rank_spawn_assignment_candidates(
            [99, 26], [99, 34], self.state((1585, 417), (1584, 544))
        )
        self.assertEqual(result["A_to_P1_B_to_P2"]["manhattan_error"], 2)
        self.assertEqual(result["discriminator"], "unresolved_single_snapshot")
        self.assertFalse(result["A_to_P1_B_to_P2"]["exact"])

    def test_mixed_coordinates_cannot_become_exact_by_x_match_alone(self):
        result = rank_spawn_assignment_candidates(
            [99, 26], [99, 34], self.state((1584, 544), (1584, 545))
        )
        self.assertEqual(result["discriminator"], "unresolved_single_snapshot")


if __name__ == "__main__":
    unittest.main()

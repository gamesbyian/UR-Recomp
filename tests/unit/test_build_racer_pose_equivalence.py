import unittest

from tools.build_racer_pose_equivalence import build_equivalence


class RacerPoseEquivalenceTest(unittest.TestCase):
    def test_collapses_identical_stock_pose_but_keeps_player_boundary(self):
        def rep(rid, player, stock_hash, authored=False):
            return {
                "representation_id": rid,
                "semantic_frame_id": "0x1",
                "player": player,
                "observed_frames_in_window": [1],
                "stock_evidence": {"rgba_sha256": stock_hash},
                "art_review": {
                    "authored_candidate": {"x": 1} if authored else None
                },
            }

        result = build_equivalence({
            "family": "f",
            "representations": [
                rep("a", "p1", "same", True),
                rep("b", "p1", "same"),
                rep("c", "p2", "same"),
            ],
        })
        self.assertEqual(result["semantic_representation_count"], 3)
        self.assertEqual(result["unique_stock_pose_count"], 2)
        self.assertEqual(
            result["pose_groups"][0]["reuse_candidates"],
            ["b"],
        )


if __name__ == "__main__":
    unittest.main()

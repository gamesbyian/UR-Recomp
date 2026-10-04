import unittest

from tools.build_racer_pose_equivalence import build_equivalence


class RacerPoseEquivalenceTest(unittest.TestCase):
    def test_collapses_identical_stock_pose_but_keeps_player_boundary(self):
        def rep(rid, player, stock_hash, authored_hash=None):
            return {
                "representation_id": rid,
                "semantic_frame_id": "0x1",
                "player": player,
                "observed_frames_in_window": [1],
                "stock_evidence": {"rgba_sha256": stock_hash},
                "art_review": {
                    "authored_candidate": (
                        {"rgba_sha256": authored_hash}
                        if authored_hash is not None else None
                    )
                },
            }

        result = build_equivalence({
            "family": "f",
            "representations": [
                rep("a", "p1", "same", "art-a"),
                rep("b", "p1", "same"),
                rep("c", "p2", "same"),
            ],
        })
        self.assertEqual(result["semantic_representation_count"], 3)
        self.assertEqual(result["unique_stock_pose_count"], 2)
        self.assertEqual(result["pose_groups"][0]["reuse_candidates"], ["b"])
        self.assertEqual(result["pose_groups"][0]["authored_asset_rgba_sha256"], "art-a")
        self.assertEqual(result["worklist"]["unauthored_pose_count"], 1)
        self.assertEqual(result["worklist"]["authored_pose_count"], 1)
        self.assertEqual(result["worklist"]["conflicting_authored_pose_count"], 0)

    def test_shared_authored_hash_is_one_asset_not_duplicate_work(self):
        def rep(rid, authored_hash):
            return {
                "representation_id": rid,
                "semantic_frame_id": "0x1",
                "player": "p1",
                "observed_frames_in_window": [1],
                "stock_evidence": {"rgba_sha256": "stock"},
                "art_review": {
                    "authored_candidate": {"rgba_sha256": authored_hash}
                },
            }

        result = build_equivalence({
            "family": "f",
            "representations": [
                rep("a", "shared"),
                rep("b", "shared"),
            ],
        })
        pose = result["pose_groups"][0]
        self.assertEqual(pose["authored_representation_ids"], ["a", "b"])
        self.assertEqual(pose["authored_asset_rgba_sha256"], "shared")
        self.assertFalse(pose["authored_asset_conflict"])
        self.assertEqual(result["worklist"]["conflicting_authored_pose_count"], 0)

    def test_different_authored_hashes_for_same_stock_pose_are_conflict(self):
        def rep(rid, authored_hash):
            return {
                "representation_id": rid,
                "semantic_frame_id": "0x1",
                "player": "p1",
                "observed_frames_in_window": [1],
                "stock_evidence": {"rgba_sha256": "stock"},
                "art_review": {
                    "authored_candidate": {"rgba_sha256": authored_hash}
                },
            }

        result = build_equivalence({
            "family": "f",
            "representations": [
                rep("a", "art-a"),
                rep("b", "art-b"),
            ],
        })
        pose = result["pose_groups"][0]
        self.assertIsNone(pose["authored_asset_rgba_sha256"])
        self.assertTrue(pose["authored_asset_conflict"])
        self.assertEqual(result["worklist"]["conflicting_authored_pose_count"], 1)


if __name__ == "__main__":
    unittest.main()

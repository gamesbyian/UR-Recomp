import unittest

from tools.build_racer_hd_shipping_readiness import build_shipping_readiness


class RacerHdShippingReadinessTest(unittest.TestCase):
    def equivalence(self):
        return {
            "family": "ordinary-racer",
            "source_temporal_window": {"start": 1, "end": 2},
            "pose_groups": [
                {
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "authored_source_representation_id": "a",
                    "authored_asset_rgba_sha256": "a" * 64,
                    "representation_ids": ["a", "b"],
                    "observed_frames": [1, 2],
                    "needs_authored_asset": False,
                    "authored_asset_conflict": False,
                },
                {
                    "pose_id": "p2-pose-002",
                    "player": "p2",
                    "authored_source_representation_id": "c",
                    "authored_asset_rgba_sha256": "c" * 64,
                    "representation_ids": ["c"],
                    "observed_frames": [2],
                    "needs_authored_asset": False,
                    "authored_asset_conflict": False,
                },
            ],
        }

    def decisions(self, a="needs-refinement", c="approved"):
        def row(source, status):
            return {
                "authored_source_representation_id": source,
                "reviewed_authored_rgba_sha256": source * 64,
                "status": status,
                "shipping_art_approved": status == "approved",
                "blocker_codes": ["coarse"] if status == "needs-refinement" else [],
            }
        return {
            "review_basis": {"artifact_id": 1},
            "family_blockers": [{"code": "coarse"}],
            "decisions": [row("a", a), row("c", c)],
        }

    def test_readiness_is_owned_per_unique_pose_not_guard(self):
        result = build_shipping_readiness(
            self.equivalence(),
            self.decisions(),
        )
        self.assertEqual(result["unique_pose_count"], 2)
        self.assertEqual(result["counts"]["approved"], 1)
        self.assertEqual(result["counts"]["needs_refinement"], 1)
        self.assertFalse(result["shipping_ready"])
        first = result["poses"][0]
        self.assertEqual(first["representation_ids"], ["a", "b"])
        self.assertEqual(first["review_status"], "needs-refinement")

    def test_all_unique_poses_must_be_approved(self):
        result = build_shipping_readiness(
            self.equivalence(),
            self.decisions(a="approved", c="approved"),
        )
        self.assertTrue(result["shipping_ready"])
        self.assertEqual(result["counts"]["approved"], 2)

    def test_unreviewed_pose_prevents_shipping(self):
        decisions = self.decisions()
        decisions["decisions"] = decisions["decisions"][:1]
        result = build_shipping_readiness(self.equivalence(), decisions)
        self.assertEqual(result["counts"]["unreviewed"], 1)
        self.assertFalse(result["shipping_ready"])

    def test_authored_change_invalidates_previous_review(self):
        equivalence = self.equivalence()
        equivalence["pose_groups"][0]["authored_asset_rgba_sha256"] = "d" * 64
        result = build_shipping_readiness(equivalence, self.decisions())
        self.assertEqual(result["poses"][0]["review_status"], "changed-since-review")
        self.assertEqual(result["counts"]["changed_since_review"], 1)
        self.assertFalse(result["shipping_ready"])

    def test_conflicting_approval_boolean_is_rejected(self):
        decisions = self.decisions(a="approved")
        decisions["decisions"][0]["shipping_art_approved"] = False
        with self.assertRaisesRegex(ValueError, "disagrees with status"):
            build_shipping_readiness(self.equivalence(), decisions)

    def test_stale_extra_decision_is_rejected(self):
        decisions = self.decisions()
        decisions["decisions"].append({
            "authored_source_representation_id": "stale",
            "reviewed_authored_rgba_sha256": "f" * 64,
            "status": "needs-refinement",
            "shipping_art_approved": False,
            "blocker_codes": [],
        })
        with self.assertRaisesRegex(ValueError, "outside the current equivalence surface"):
            build_shipping_readiness(self.equivalence(), decisions)


if __name__ == "__main__":
    unittest.main()

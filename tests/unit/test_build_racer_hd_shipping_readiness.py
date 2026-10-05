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

    def decisions(
        self,
        a="needs-refinement",
        c="approved",
        family_blockers=None,
    ):
        def row(source, status):
            return {
                "authored_source_representation_id": source,
                "reviewed_authored_rgba_sha256": source * 64,
                "status": status,
                "shipping_art_approved": status == "approved",
                "blocker_codes": ["coarse"] if status == "needs-refinement" else [],
            }
        return {
            "family": "ordinary-racer",
            "review_basis": {
                "artifact_id": 1,
                "temporal_window": [1, 2],
            },
            "family_blockers": (
                [{"code": "coarse"}]
                if family_blockers is None and a == "needs-refinement"
                else (family_blockers or [])
            ),
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

    def test_family_blocker_prevents_shipping_even_when_every_pose_is_approved(self):
        result = build_shipping_readiness(
            self.equivalence(),
            self.decisions(
                a="approved",
                c="approved",
                family_blockers=[{"code": "shared-structure"}],
            ),
        )
        self.assertEqual(result["counts"]["approved"], 2)
        self.assertEqual(result["family_blockers"], [{"code": "shared-structure"}])
        self.assertFalse(result["shipping_ready"])

    def test_approval_family_must_match_equivalence_family(self):
        decisions = self.decisions()
        decisions["family"] = "other-family"
        with self.assertRaisesRegex(ValueError, "does not match equivalence family"):
            build_shipping_readiness(self.equivalence(), decisions)

    def test_approval_temporal_window_must_match_equivalence_window(self):
        decisions = self.decisions()
        decisions["review_basis"]["temporal_window"] = [1, 3]
        with self.assertRaisesRegex(ValueError, "does not match equivalence window"):
            build_shipping_readiness(self.equivalence(), decisions)

    def test_missing_approval_temporal_window_fails_closed(self):
        decisions = self.decisions()
        del decisions["review_basis"]["temporal_window"]
        with self.assertRaisesRegex(ValueError, "does not match equivalence window"):
            build_shipping_readiness(self.equivalence(), decisions)

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

    def test_approved_pose_cannot_retain_blocker_codes(self):
        decisions = self.decisions(a="approved", c="approved")
        decisions["decisions"][0]["blocker_codes"] = ["stale-blocker"]
        with self.assertRaisesRegex(ValueError, "approved but still carries blocker"):
            build_shipping_readiness(self.equivalence(), decisions)

    def test_reviewed_hash_must_be_lowercase_sha256_hex(self):
        decisions = self.decisions()
        decisions["decisions"][0]["reviewed_authored_rgba_sha256"] = "G" * 64
        with self.assertRaisesRegex(ValueError, "lowercase hexadecimal"):
            build_shipping_readiness(self.equivalence(), decisions)

    def test_blocker_codes_must_be_a_list(self):
        decisions = self.decisions()
        decisions["decisions"][0]["blocker_codes"] = "coarse"
        with self.assertRaisesRegex(ValueError, "blocker_codes must be a list"):
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

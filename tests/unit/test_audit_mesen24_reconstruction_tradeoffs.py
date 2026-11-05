"""Independent stdlib tests of authentic-source multiobjective ART-4K audit."""
import copy
import unittest

from tools.art.audit_mesen24_reconstruction_tradeoffs import audit, SCHEMA


def example():
    source = {k: "a" * 64 for k in (
        "original_source_USA_ROM_sha256",
        "original_Mesen24_archive_sha256",
        "original_pose_report_sha256",
        "original_axis_sha256",
        "provisional_camera_sha256",
        "current_2026_authored_SCAD_sha256")}
    source["original_1994_physical_3d_model_or_camera_recovered"] = False
    source["original_art_likeness_approved"] = False
    values = {
        "blue": [(0.82069294, 0.82528384, 0.09025788),
                 (0.50895141, 0.51233488, 0.02032520),
                 (0.55176933, 0.55443157, 0.01771117)],
        "red": [(0.82181906, 0.82604553, 0.10564399),
                (0.55119306, 0.55143555, 0.01780822),
                (0.58196450, 0.58231923, 0.01641587)],
    }
    arms = ("original_source_2d_rotation", "axle_root_saddle_neutral",
            "axle_root_saddle_plus15")
    keys = ("chronological_pooled_iou", "unique_shape_equal_vote_mean_iou",
            "real_23_tick_edge_change_pooled_iou")
    return {
        "schema": SCHEMA,
        "producer": source,
        "reported_per_role": {
            role: {
                arm: {"unique_shapes": 19 if role == "blue" else 23,
                      **dict(zip(keys, metrics))}
                for arm, metrics in zip(arms, rows)
            }
            for role, rows in values.items()
        },
    }


class ExactMesen24AuditTests(unittest.TestCase):
    def test_real_published_score_triplets_reveal_mixed_shape_and_motion(self):
        result = audit(example())
        plus = result["comparisons"]["axle_root_saddle_plus15"]
        self.assertTrue(plus["shape_gain_both_roles"])
        self.assertFalse(plus["chronological_motion_gain_both_roles"])
        self.assertFalse(plus["dominates_neutral_all_roles_and_metrics"])
        self.assertAlmostEqual(
            plus["delta_against_neutral_by_role"]["blue"]["real_23_tick_edge_change_pooled_iou"],
            -0.00261403)
        self.assertFalse(result["shipping_art_approved"])
        self.assertFalse(result["historical_3d_recovered"])

    def test_rejects_incomplete_provenance_and_one_role_cherry_pick(self):
        for edit in ("missing_sha", "bad_flags", "missing_role", "missing_arm",
                     "bad_shapes", "nan_metric", "bool_metric", "bad_schema"):
            data = example()
            if edit == "missing_sha":
                data["producer"]["original_pose_report_sha256"] = "abc"
            elif edit == "bad_flags":
                data["producer"]["original_art_likeness_approved"] = True
            elif edit == "missing_role":
                del data["reported_per_role"]["red"]
            elif edit == "missing_arm":
                del data["reported_per_role"]["red"]["axle_root_saddle_plus15"]
            elif edit == "bad_shapes":
                data["reported_per_role"]["blue"]["axle_root_saddle_neutral"]["unique_shapes"] = 24
            elif edit == "nan_metric":
                data["reported_per_role"]["red"]["axle_root_saddle_plus15"]["chronological_pooled_iou"] = float("nan")
            elif edit == "bool_metric":
                data["reported_per_role"]["red"]["axle_root_saddle_neutral"]["chronological_pooled_iou"] = True
            elif edit == "bad_schema":
                data["schema"] = "unknown"
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                audit(data)

    def test_true_uniform_improvement_is_distinguished(self):
        data = example()
        for role in ("blue", "red"):
            candidate = data["reported_per_role"][role]["axle_root_saddle_plus15"]
            neutral = data["reported_per_role"][role]["axle_root_saddle_neutral"]
            for metric in ("chronological_pooled_iou",
                           "unique_shape_equal_vote_mean_iou",
                           "real_23_tick_edge_change_pooled_iou"):
                candidate[metric] = neutral[metric] + 0.01
        result = audit(data)["comparisons"]["axle_root_saddle_plus15"]
        self.assertTrue(result["dominates_neutral_all_roles_and_metrics"])
        self.assertTrue(result["chronological_motion_gain_both_roles"])


if __name__ == "__main__":
    unittest.main()

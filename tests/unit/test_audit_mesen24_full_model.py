"""Regression checks for source-matched, multi-metric real GLB geometry decisions."""
import copy
import unittest

from tools.art.audit_mesen24_full_model import (
    compare, strict_scores, METRICS, ROLES, HASH_KEYS,
)
from tools.art.score_original_mesen24_full_saddle import SCHEMA, ARMS, TICKS


def synthetic_report():
    evidence = {
        "schema": SCHEMA,
        **{key: "a" * 64 for key in HASH_KEYS},
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered": False,
        "owner_2026_character_art_likeness_approved": False,
        "source_each_player_has_all_24_consecutive_original_PPU_images": True,
        "source_unique_binary_silhouettes_grouped_without_duplicate_vote_weight": True,
        "original_source_fixed_y_band_temporal_edges_partition_exactly": True,
        "source_viewpoint_families_are_known_NOT_prospective_blind": True,
        "source_original_timeline_ticks": [1601, 1624],
        "original_source_per_role": {},
    }
    for role in ROLES:
        evidence["original_source_per_role"][role] = {
            "original_24_tick_samples": {str(t): {} for t in TICKS},
            "arms": {
                arm: {
                    "original_chronological_source_frame_count": 24,
                    "source_actual_timeline_edge_count": 23,
                    "original_unique_64px_binary_shape_count": 19 if role == "blue" else 23,
                    "per_original_chronological_edge": [{}] * 23,
                    **{name: .5 for name, _ in METRICS},
                }
                for arm in ARMS
            },
        }
    return evidence


class FullModelParetoAuditTest(unittest.TestCase):
    def test_identical_variants_never_win_a_sculpture_claim(self):
        result = compare(synthetic_report())
        self.assertEqual(result["comparison_count"], 12)
        self.assertTrue(all(not row["strictly_dominates_all_six"]
                            for row in result["same_control_variant_comparisons"]))
        self.assertFalse(result["shipping_art_approved"])

    def test_worsening_temporal_motion_is_not_hidden_by_static_gain(self):
        data = synthetic_report()
        candidate = "axle_root_saddle_span110_fixed_tick_24deg"
        for role in ROLES:
            item = data["original_source_per_role"][role]["arms"][candidate]
            item["source_unique_shape_equal_vote_mean_alpha_iou"] = .6
            item["source_frame_pooled_alpha_iou"] = .6
            item["source_actual_23_consecutive_edge_change_pooled_iou"] = .4
        result = compare(data)
        finding = next(row for row in result["same_control_variant_comparisons"]
                       if row["arm"] == candidate)
        self.assertTrue(finding["shape_better_both"])
        self.assertFalse(finding["motion_better_both"])
        self.assertTrue(finding["mixed_tradeoff"])
        self.assertFalse(finding["strictly_dominates_all_six"])
        self.assertEqual(finding["baseline_same_wheel_drive_and_saddle_attitude"],
                         "axle_root_saddle_world_level_fixed_tick_24deg")

    def test_source_hashes_and_original_roles_fail_closed(self):
        for mutation in ("missing_hash", "wrong_schema", "one_role", "missing_tick",
                         "missing_arm", "bad_shape_count", "faked_approval", "nan",
                         "missing_edge", "not_blind"):
            data = synthetic_report()
            arm = ARMS[0]
            blue = data["original_source_per_role"]["blue"]
            if mutation == "missing_hash":
                data[HASH_KEYS[0]] = ""
            elif mutation == "wrong_schema":
                data["schema"] = "unrelated"
            elif mutation == "one_role":
                del data["original_source_per_role"]["red"]
            elif mutation == "missing_tick":
                del blue["original_24_tick_samples"]["1601"]
            elif mutation == "missing_arm":
                del blue["arms"][arm]
            elif mutation == "bad_shape_count":
                blue["arms"][arm]["original_unique_64px_binary_shape_count"] = 24
            elif mutation == "faked_approval":
                data["owner_2026_character_art_likeness_approved"] = True
            elif mutation == "nan":
                blue["arms"][arm][METRICS[0][0]] = float("nan")
            elif mutation == "missing_edge":
                blue["arms"][arm]["per_original_chronological_edge"] = []
            elif mutation == "not_blind":
                data["source_viewpoint_families_are_known_NOT_prospective_blind"] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                strict_scores(data)


if __name__ == "__main__":
    unittest.main()

"""Verify original Mesen24 physical hub kinematic experiment is preserved as research."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"analysis/data/racer-art4k-mesen24-hub-attachment-qualified-20261105.json"
PRIOR=ROOT/"analysis/data/racer-art4k-mesen24-hub-cover-qualified-20261105.json"
HISTORY=ROOT/"analysis/data/racer-art4k-mesen24-fork-crown-qualified-20261105.json"
METRICS=("source_frame_pooled_alpha_iou","source_unique_shape_equal_vote_mean_alpha_iou",
         "source_actual_23_consecutive_edge_change_pooled_iou")
ROLES=("blue","red")
MODES=("rom_phase_15deg","fixed_tick_24deg")


class OriginalSourceHubJointQualificationTests(unittest.TestCase):
    def test_both_original_racers_two_drives_and_exact_kinematic_controls(self):
        record=json.loads(SRC.read_text())
        previous=json.loads(PRIOR.read_text())
        historic=json.loads(HISTORY.read_text())
        self.assertEqual(record["schema"],
            "UR-ART4K-ORIGINAL-MESEN24-2026-HUB-ATTACHMENT-QUALIFIED-SCORES/1")
        self.assertEqual((record["same_source_per_original_racer_frames"],
                          record["same_source_per_original_racer_true_adjacent_edges"]),(24,23))
        self.assertEqual(record["source_original_player_roles"],list(ROLES))
        self.assertEqual(record["combined_real_2026_model_arms"],31)
        self.assertEqual(record["source_retained_historical_real_GLB_arms"],27)
        self.assertEqual(len(record["combined_strict_six_objective_unweighted_nondominated_arms"]),19)
        self.assertEqual(record["source_full_report_sha256"],
            "c55cc93cfb8d97bff37a0a8524fa29a4584c517359b61f070672765e1bce0c32")
        self.assertEqual(record["source_artifact_outer_zip_sha256"],
            "920e94ca4569d8e72ea545ae3a1df2d49094c4f47bc049c3d2ce72f07f5f2c43")
        self.assertEqual(record["source_original_USA_ROM_sha256"],
                         historic["source_USA_ROM_sha256"])
        self.assertEqual(record["source_original_Mesen24_no_skip_archive_sha256"],
                         historic["source_original_Mesen24_zip_sha256"])
        self.assertEqual(record["source_unchanged_provisional_7_6_camera_sha256"],
                         historic["source_provisional_7_6_camera_sha256"])
        self.assertEqual(record["source_2026_authored_SCAD_sha256"],
                         historic["source_2026_SCAD_sha256"])
        for role in ROLES:
            for mode in MODES:
                row=record["source_2026_model_physical_hub_attachment_score"][role][mode]
                self.assertEqual(row["source_original_true_adjacent_motion_edges"],23)
                self.assertEqual(row["source_original_unique_64px_binary_shapes"],
                                 19 if role=="blue" else 23)
                old=previous["measured_original_source_role_results"][role]["modes"][mode]
                for group,earlier in (
                    ("rotating","physical_dark_hub_candidate"),
                    ("hubless","unchanged_glb_control"),
                ):
                    for key in METRICS:
                        self.assertEqual(row["per_2026_physical_hub_joint"][group][key],
                                         old[earlier][key])
                for key in METRICS:
                    a=row["per_2026_physical_hub_joint"]["axle_locked"][key]
                    b=row["per_2026_physical_hub_joint"]["rotating"][key]
                    self.assertEqual(row["axle_locked_minus_rotating"][key],
                                     round(a-b,8))
                self.assertLess(row["axle_locked_minus_rotating"][METRICS[2]],0)
                if role=="blue":
                    self.assertLess(row["axle_locked_minus_rotating"][METRICS[0]],0)
                else:
                    self.assertGreater(row["axle_locked_minus_rotating"][METRICS[0]],0)

    def test_no_original_1994_3d_or_shipping_art_promotion(self):
        record=json.loads(SRC.read_text())
        for key in (
            "original_1994_source_3D_mesh_camera_or_joint_recovered",
            "owner_2026_character_likeness_approved","shipping_art_approved",
        ):
            self.assertIs(record[key],False)
        self.assertIs(record["retrospective_same_source_observations_not_prospective_blind_holdout"],True)
        self.assertIs(record["source_model_contains_two_unfused_closed_dark_hub_solids"],True)
        self.assertTrue(record["all_four_hub_arms_remain_nondominated_in_six_objective_retrospective_comparison"])
        arms=record["combined_strict_six_objective_unweighted_nondominated_arms"]
        for mode in MODES:
            self.assertIn("axle_root_hub_cover_axle_locked_"+mode,arms)
            self.assertIn("axle_root_hub_cover_"+mode,arms)


if __name__=="__main__":
    unittest.main()

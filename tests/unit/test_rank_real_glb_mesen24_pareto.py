"""Six-objective conservation, role fairness and original source provenance."""
import copy
import unittest

from tools.art.rank_real_glb_mesen24_pareto import (
    analyze,dominates,SOURCE_PINS,SOURCE_SCHEMA,SCHEMA,OBJECTIVES,
)

def arm(shape,unique,motion,tp,fp,fn):
    counts={"tp":tp,"fp":fp,"fn":fn}
    assert round(tp/(tp+fp+fn),8)==motion
    return {
        "original_chronological_source_frame_count":24,
        "source_actual_timeline_edge_count":23,
        "original_unique_64px_binary_shape_count":19,
        "source_frame_pooled_alpha_iou":shape,
        "source_unique_shape_equal_vote_mean_alpha_iou":unique,
        "source_actual_23_consecutive_edge_change_pooled_iou":motion,
        "source_actual_23_consecutive_edge_change_tp_fp_fn":counts,
        "source_actual_23_consecutive_edge_change_fixed_y_bands":{
            "upper_y0_14":{
                "tp_fp_fn":counts,"source_chronological_edge_count":23},
            "middle_y15_26":{
                "tp_fp_fn":{"tp":0,"fp":0,"fn":0},
                "source_chronological_edge_count":23},
            "lower_y27_63":{
                "tp_fp_fn":{"tp":0,"fp":0,"fn":0},
                "source_chronological_edge_count":23},
        },
    }

def fake():
    # The 2D control is not eligible as real geometry even if its metrics
    # dominate everything. B improves blue but harms red vs A, so no
    # post-hoc per-role winner. C loses to A on all six axes.
    a=arm(.6,.6,.5,1,1,0)
    b=arm(.7,.7,.5,1,1,0)
    c=arm(.5,.5,.33333333,1,1,1)
    d=arm(.9,.9,.66666667,2,1,0)
    blue={"original_source_2d_rotation":d,
          "axle_root_a":a,"axle_root_b":b,"axle_root_c":c}
    red={"original_source_2d_rotation":d,
         "axle_root_a":a,"axle_root_b":c,"axle_root_c":c}
    return {
        "schema":SOURCE_SCHEMA,
        **SOURCE_PINS,
        "source_original_timeline_ticks":[1601,1624],
        "source_each_player_has_all_24_consecutive_original_PPU_images":True,
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered":False,
        "owner_2026_character_art_likeness_approved":False,
        "original_source_per_role":{
            role:{"original_24_tick_samples":{
                str(t):{} for t in range(1601,1625)
            },"arms":data}
            for role,data in (("blue",blue),("red",red))
        }
    }

class RealGLBMesenParetoTests(unittest.TestCase):
    def test_nondominance_preserves_both_players_and_original_2d_null(self):
        result=analyze(fake())
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["candidate_2026_GLB_arm_count"],3)
        self.assertEqual(result["pareto_nondominated_2026_GLB_arms"],
                         ["axle_root_a","axle_root_b"])
        self.assertEqual(result["per_2026_GLB_arm"]["axle_root_c"][
                         "strictly_dominated_by_2026_GLB_arms"],
                         ["axle_root_a","axle_root_b"])
        self.assertEqual(len(result["objectives_all_maximize"]),6)
        self.assertEqual(result["objectives_all_maximize"],list(OBJECTIVES))
        self.assertTrue(result["separate_original_source_2D_rotation_null_six_objective_values"][0]>.8)
        self.assertFalse(result["original_1994_3D_camera_mesh_or_joint_recovered"])
        self.assertFalse(result["owner_art_likeness_approved"])

    def test_invalid_source_and_broken_chronology_never_rank(self):
        original=fake()
        for change in ("rom","camera","art","no_red","missing_tick",
                       "missing_band","fake_counts","missing_control"):
            data=copy.deepcopy(original)
            if change=="rom":
                data["source_exact_original_USA_ROM_sha256"]="0"*64
            elif change=="camera":
                data["source_unchanged_7_6_camera_sha256"]="0"*64
            elif change=="art":
                data["owner_2026_character_art_likeness_approved"]=True
            elif change=="no_red":
                del data["original_source_per_role"]["red"]
            elif change=="missing_tick":
                del data["original_source_per_role"]["blue"]["original_24_tick_samples"]["1602"]
            elif change=="missing_band":
                del data["original_source_per_role"]["red"]["arms"]["axle_root_a"][
                    "source_actual_23_consecutive_edge_change_fixed_y_bands"]["lower_y27_63"]
            elif change=="fake_counts":
                data["original_source_per_role"]["blue"]["arms"]["axle_root_a"][
                    "source_actual_23_consecutive_edge_change_tp_fp_fn"]["fp"]+=1
            elif change=="missing_control":
                del data["original_source_per_role"]["red"]["arms"]["original_source_2d_rotation"]
            with self.subTest(change=change),self.assertRaises(ValueError):
                analyze(data)

    def test_matched_saddle_mesh_delta_isolated_from_other_drive_laws(self):
        data=fake()
        blue=data["original_source_per_role"]["blue"]["arms"]
        red=data["original_source_per_role"]["red"]["arms"]
        control="axle_root_saddle_world_level_fixed_tick_24deg"
        candidate="axle_root_saddle_span110_fixed_tick_24deg"
        other_control="axle_root_saddle_world_level_rom_phase_15deg"
        for role_arms in (blue,red):
            role_arms[control]=arm(.6,.6,.5,1,1,0)
            role_arms[other_control]=arm(.4,.4,.33333333,1,1,1)
            role_arms[candidate]=arm(.7,.7,.33333333,1,1,1)
        result=analyze(data)
        matched=result["matched_geometry_only_deltas"][candidate]
        self.assertEqual(matched["same_wheel_drive_and_saddle_attitude_control"],control)
        self.assertEqual(matched["signed_six_objective_delta"],[.1,.1,-.16666667]*2)
        self.assertTrue(matched["shape_improves_both_original_racers"])
        self.assertFalse(matched["chronological_motion_improves_both_original_racers"])
        self.assertTrue(matched["mixed_shape_or_motion_tradeoff"])
        self.assertFalse(matched["strictly_dominates_own_matched_control"])
        self.assertNotIn("axle_root_b",result["matched_geometry_only_deltas"])

    def test_dominance_is_strict_and_six_dimensional(self):
        a=(.5,)*6
        self.assertFalse(dominates(a,a))
        self.assertTrue(dominates((.6,)*6,a))
        self.assertFalse(dominates((.6,.6,.6,.6,.6,.4),a))
        with self.assertRaises(ValueError):
            dominates((1.,),a)

if __name__=="__main__":
    unittest.main()

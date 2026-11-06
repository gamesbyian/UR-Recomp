"""ROM-free conservation and leave-one-edge-out checks for genuine PPU chronology."""
import copy
import hashlib
import json
import unittest

from tools.art.audit_model_pose_edge_sensitivity import (
    analyze,pooled,tally,SCHEMA,TICKS,
)
from tools.art.rank_real_glb_mesen24_pareto import SOURCE_SCHEMA,SOURCE_PINS

ARM_A="axle_root_hub_cover_fixed_tick_24deg"
ARM_B="axle_root_saddle_world_level_fixed_tick_24deg"


def fixture():
    # Entire source event source-changed population is always three pixels;
    # only the model's actual changed prediction differs.
    good={"tp":2,"fp":1,"fn":1,"iou":.5}
    poor={"tp":1,"fp":1,"fn":2,"iou":.25}
    frame={"tp":2,"fp":1,"fn":2,"iou":.4}
    baseline={"tp":1,"fp":1,"fn":3,"iou":.2}
    role_record={}
    for role in ("blue","red"):
        samples={
            str(t):{
                "source_true_original_Mesen_tick":t,
                "source_opaque_64px_pixels":4,
                "source_2D_alpha_sha256":"a"*64,
                "source_actual_and_candidate_full_alpha":{
                    ARM_A:frame,ARM_B:baseline
                },
            } for t in TICKS}
        rows={
            name:{
                "original_chronological_source_frame_count":24,
                "source_actual_timeline_edge_count":23,
                "per_original_chronological_edge":[
                    {"source_ticks":[t,t+1],**(good if name==ARM_A else poor)}
                    for t in TICKS[:-1]
                ],
                "source_actual_23_consecutive_edge_change_tp_fp_fn":
                    {"tp":46 if name==ARM_A else 23,"fp":23,
                     "fn":23 if name==ARM_A else 46},
                "source_actual_23_consecutive_edge_change_pooled_iou":
                    .5 if name==ARM_A else .25,
            } for name in (ARM_A,ARM_B)}
        role_record[role]={"arms":rows,"original_24_tick_samples":samples}
    return {
        "schema":SOURCE_SCHEMA,
        **SOURCE_PINS,
        "source_original_timeline_ticks":[1601,1624],
        "source_each_player_has_all_24_consecutive_original_PPU_images":True,
        "original_1994_3D_mesh_camera_joint_or_source_materials_recovered":False,
        "owner_2026_character_art_likeness_approved":False,
        "original_source_per_role":role_record,
    }


def raw_and_sha(data):
    raw=json.dumps(data,sort_keys=True).encode()
    return raw,hashlib.sha256(raw).hexdigest()


class SourceModelMotionEdgeSensitivityTests(unittest.TestCase):
    def test_perfect_source_conservation_and_one_vote_per_original_frame(self):
        raw,sha=raw_and_sha(fixture())
        result=analyze(raw,sha,((ARM_A,ARM_B),))
        self.assertEqual(result["schema"],SCHEMA)
        self.assertFalse(result["original_1994_3D_mesh_camera_or_joint_recovered"])
        for role in ("blue","red"):
            rows=result["role_matched_source_edge_diagnostics"][role]
            entry=rows[ARM_A+"::"+ARM_B]
            self.assertEqual(len(entry["all_23_original_consecutive_edge_deltas"]),23)
            self.assertEqual(len(entry["all_24_original_static_frame_deltas"]),24)
            self.assertEqual(entry["pooled_motion_iou_candidate_minus_control"],.25)
            self.assertEqual(entry["per_original_frame_static_iou_wins"],24)
            self.assertEqual(entry["per_actual_original_temporal_edge_iou_wins"],23)
            self.assertEqual(entry["per_actual_original_temporal_edge_iou_losses"],0)
            self.assertEqual(entry["largest_negative_influence_original_edges"][0][
                "this_edge_influence_on_pooled_delta"],0)
            self.assertEqual(entry["all_23_original_consecutive_edge_deltas"][0][
                "candidate_minus_control_tp_fp_fn"],{"tp":1,"fp":0,"fn":-1})
        self.assertEqual(pooled([{"tp":2,"fp":1,"fn":1}]),.5)
        self.assertEqual(tally({"tp":2,"fp":1,"fn":1}),(2,1,1))
        for invalid in ({"tp":1,"fp":-1,"fn":1},{"tp":True,"fp":0,"fn":0}):
            with self.assertRaises(ValueError):tally(invalid)

    def test_source_sha_provenance_and_edge_integrity_fail_closed(self):
        original=fixture()
        raw,sha=raw_and_sha(original)
        with self.assertRaisesRegex(ValueError,"SHA256"):
            analyze(raw,"0"*64,((ARM_A,ARM_B),))
        for invalid_pairs in ((),((ARM_A,ARM_A),),((ARM_A,ARM_B),)*2,
                              (("surprise_model",ARM_B),)):
            with self.subTest(pairs=invalid_pairs),self.assertRaises(ValueError):
                analyze(raw,sha,invalid_pairs)
        for kind in ("missing_tick","wrong_sequence","different_source",
                     "motion_summary","wrong_static_pixels","fake_1994_model",
                     "bad_original_ROM","fake_source_iou"):
            data=copy.deepcopy(original)
            record=data["original_source_per_role"]["red"]
            a=record["arms"][ARM_A]
            if kind=="missing_tick":
                del record["original_24_tick_samples"]["1605"]
            elif kind=="wrong_sequence":
                a["per_original_chronological_edge"][0]["source_ticks"]=[1602,1603]
            elif kind=="different_source":
                a["per_original_chronological_edge"][0]["fn"]=2
                a["per_original_chronological_edge"][0]["iou"]=.4
                a["source_actual_23_consecutive_edge_change_tp_fp_fn"]["fn"]=24
                a["source_actual_23_consecutive_edge_change_pooled_iou"]=.49462366
            elif kind=="motion_summary":
                a["source_actual_23_consecutive_edge_change_tp_fp_fn"]["fp"]=24
            elif kind=="wrong_static_pixels":
                record["original_24_tick_samples"]["1602"][
                    "source_actual_and_candidate_full_alpha"][ARM_A]["fn"]=0
            elif kind=="fake_1994_model":
                data["original_1994_3D_mesh_camera_joint_or_source_materials_recovered"]=True
            elif kind=="bad_original_ROM":
                data["source_exact_original_USA_ROM_sha256"]="b"*64
            elif kind=="fake_source_iou":
                a["per_original_chronological_edge"][0]["iou"]=.91
            value,digest=raw_and_sha(data)
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                analyze(value,digest,((ARM_A,ARM_B),))


if __name__=="__main__":
    unittest.main()

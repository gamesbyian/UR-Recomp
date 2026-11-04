"""No ROM, NumPy or Trimesh required to re-audit material motion receipt."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"analysis/data/racer-original-mesen24-visible-material-motion-20261103.json"
RENDERER=ROOT/"tools/art/evaluate_original_mesen24_visible_material_motion.py"
REPORT_SHA="11e3956e433aca67673b397e66e7925578d6adc77223b29c29c12fff1a9d3541"
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
MODEL_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
EDGES=[[1602,1603],[1605,1606],[1609,1610]]
CONTROLS={"registered","null_x_plus8","null_x_minus8","null_y_plus8","null_y_minus8"}


class OriginalMaterialMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=REPORT.read_bytes()
        cls.report=json.loads(cls.raw)

    def test_exact_source_and_candidate_identity_without_historic_mapping(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),REPORT_SHA)
        self.assertNotIn(b"\r",self.raw)
        r=self.report
        self.assertEqual(r["schema"],"UR-ART4K-MESEN24-REAL-GLB-MOVING-MATERIAL-VS-ORIGINAL-INTERIOR/1")
        self.assertEqual(r["source_original_24tick_zip_sha256"],SOURCE_SHA)
        self.assertEqual(r["model_single_real_2026_upright_glb_sha256"],MODEL_SHA)
        self.assertEqual(r["one_provisional_7_6_camera_sha256"],CAMERA_SHA)
        self.assertEqual(r["original_selected_source_edges"],EDGES)
        self.assertEqual(r["illustrative_2026_direct_drive_step_deg_per_original_tick"],24)
        self.assertEqual(r["frame_pitch_deg"],0)
        self.assertTrue(r["no_per_frame_source_fit"])
        self.assertTrue(r["no_original_1994_palette_to_model_material_mapping"])
        self.assertFalse(r["source_original_camera_parts_and_3D_pose_recovered"])
        self.assertTrue(r["source_original_replay_24tick_is_already_inspected_not_blind"])
        self.assertTrue(r["exact_256px_neutral_material_silhouette_and_five_part_renderer_agreement"])
        self.assertTrue(r["all_six_poses_pixel_identical_alpha_to_independent_renderer"])

    def test_all_material_ids_coarsen_to_five_provisional_parent_parts(self):
        r=self.report
        nodes=r["model_original_sixteen_material_nodes"]
        mapping=r["candidate_material_id_to_five_parent"]
        self.assertEqual(len(nodes),16)
        self.assertEqual(len(set(nodes)),16)
        self.assertEqual(len(mapping),17)
        self.assertEqual(mapping[0],0)
        self.assertEqual(set(mapping[1:]),{1,2,3,4,5})
        self.assertEqual(set(r["per_original_OAM_source_player"]),{"blue","red"})
        self.assertEqual(r["per_original_OAM_source_player"]["blue"]["source_OAM_slot"],96)
        self.assertEqual(r["per_original_OAM_source_player"]["red"]["source_OAM_slot"],97)

    def test_source_pixel_arithmetic_and_material_changes_larger_than_parent_changes(self):
        r=self.report["per_original_OAM_source_player"]
        original={"blue":[176,24,33],"red":[26,192,31]}
        hit={"blue":[5,3,2],"red":[3,9,3]}
        part_hit={"blue":[3,2,2],"red":[2,4,2]}
        for player,player_result in r.items():
            events=player_result["event_controls"]
            self.assertEqual(len(events),3)
            for i,event in enumerate(events):
                self.assertEqual(event["actual_original_source_edge"],EDGES[i])
                self.assertEqual(event["source_original_index_change_in_opaque_intersection"],original[player][i])
                mats=event["visible_material_id_support"]
                parts=event["visible_five_parent_id_support"]
                self.assertEqual(set(mats),CONTROLS)
                self.assertEqual(set(parts),CONTROLS)
                self.assertEqual(mats["registered"]["model_label_change_pixels"],[9,16,12][i])
                self.assertEqual(parts["registered"]["model_label_change_pixels"],[7,8,6][i])
                self.assertEqual(mats["registered"]["spatial_intersection"],hit[player][i])
                self.assertEqual(parts["registered"]["spatial_intersection"],part_hit[player][i])
                for control in CONTROLS:
                    mat,part=mats[control],parts[control]
                    for row in (mat,part):
                        source=row["original_opaque_interior_index_changes"]
                        candidate=row["model_label_change_pixels"]
                        intersection=row["spatial_intersection"]
                        self.assertEqual(source,original[player][i])
                        self.assertLessEqual(intersection,min(source,candidate))
                        self.assertEqual(row["source_recall"],round(intersection/source,8))
                        self.assertEqual(row["model_precision"],
                                         round(intersection/candidate,8) if candidate else 0)
                        self.assertEqual(row["change_support_iou"],
                                         round(intersection/(source+candidate-intersection),8))
                    self.assertGreaterEqual(mat["model_label_change_pixels"],
                                            part["model_label_change_pixels"])
                    self.assertGreaterEqual(mat["spatial_intersection"],
                                            part["spatial_intersection"])

    def test_registered_control_limited_but_beats_coarse_offset_controls(self):
        for player,result in self.report["per_original_OAM_source_player"].items():
            for event in result["event_controls"]:
                base=event["visible_material_id_support"]["registered"]["change_support_iou"]
                self.assertGreater(base,0)
                self.assertLess(base,.10)
                for other in CONTROLS-{"registered"}:
                    self.assertGreater(base,event["visible_material_id_support"][other]["change_support_iou"])
            self.assertEqual(len(result["fixed_source_tick1601_alpha_anchor_x2y2"]),2)

    def test_offline_implementation_syntax_and_no_overwrite(self):
        source=RENDERER.read_text(encoding="utf-8")
        ast.parse(source,filename=str(RENDERER))
        for required in ("audit_mesen","apply_scene","raster_part_ids",
                         "render_mask","publish_text_once","np.maximum"):
            self.assertIn(required,source)


if __name__=="__main__":
    unittest.main()

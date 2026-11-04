"""ROM/GLB-free receipt review for bounded true-source/static 2026 part visibility."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"analysis/data/racer-original-mesen24-static-model-part-coverage-20261103.json"
TOOL=ROOT/"tools/art/audit_original_mesen24_static_model_part_visibility.py"
RECEIPT_SHA="4fec59233ee550bf435bfd802f58ace160edeccae582adf3fe2e3008ece8d97f"
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
MODEL_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
PARTS={"tire","rim_and_hub","fork_and_frame","pedals","saddle"}
CONTROLS={"registered","null_x_plus8","null_x_minus8","null_y_plus8","null_y_minus8"}


class SourcePartVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=REPORT.read_bytes()
        cls.report=json.loads(cls.raw)

    def test_source_model_camera_digest_and_observation_bounds(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),RECEIPT_SHA)
        self.assertNotIn(b"\r",self.raw)
        r=self.report
        self.assertEqual(r["schema"],"UR-ART4K-MESEN24-STATIC-2026-VISIBLE-PART-ID-SUPPORT/1")
        self.assertEqual(r["original_authentic_source_zip_sha256"],SOURCE_SHA)
        self.assertEqual(r["original_2026_real_upright_glb_sha256"],MODEL_SHA)
        self.assertEqual(r["fixed_7_6_provisional_camera_sha256"],CAMERA_SHA)
        self.assertEqual(len(r["candidate_GLB_part_id_raster_source64_sha256"]),64)
        self.assertEqual(len(r["candidate_GLB_part_id_raster_full256_sha256"]),64)
        self.assertTrue(r["whole_glb_256_silhouette_matches_depth_ID_raster_exactly"])
        self.assertTrue(r["one_lower_alpha_registration_at_tick1601_per_player"])
        self.assertTrue(r["one_static_candidate_projection_no_fitted_motion"])
        self.assertFalse(r["original_1994_part_to_GLB_identity_proven"])
        self.assertFalse(r["original_3d_motion_or_source_painted_material_recovered"])

    def test_all_source_interior_pixels_partition_into_visible_candidate_parts_or_outside(self):
        self.assertEqual(set(self.report["per_source_player"]),{"blue","red"})
        for name,record in self.report["per_source_player"].items():
            self.assertEqual(record["source_OAM_slot"],{"blue":96,"red":97}[name])
            self.assertEqual(record["actual_original_interior_change_instances"],
                             {"blue":717,"red":834}[name])
            self.assertEqual(record["actual_original_alpha_change_instances"],
                             {"blue":660,"red":659}[name])
            self.assertEqual(set(record["registered_2026_model_part_names"]),PARTS)
            self.assertEqual(set(record["comparison"]),CONTROLS)
            source=record["actual_original_interior_change_instances"]
            for control,v in record["comparison"].items():
                names=v["per_candidate_2026_part_interior_change_instances"]
                self.assertEqual(set(names),PARTS)
                self.assertTrue(all(type(q) is int and q>=0 for q in names.values()))
                self.assertEqual(sum(names.values()),
                                 v["original_interior_change_pixel_instances_on_candidate_model"])
                self.assertEqual(sum(names.values())+
                                 v["original_interior_change_outside_candidate_model"],source)
                self.assertEqual(v["interior_change_model_footprint_fraction"],
                                 round(sum(names.values())/source,8))
                self.assertGreaterEqual(v["original_tick1601_alpha_iou"],0)
                self.assertLessEqual(v["original_tick1601_alpha_iou"],1)
                self.assertLessEqual(sum(v["per_candidate_2026_part_alpha_boundary_change_instances"].values()),
                                     record["actual_original_alpha_change_instances"])
                self.assertGreater(v["model_visible_pixels"],0)
            self.assertEqual(record["comparison"]["registered"]["offset_source_logical_pixels"],[0,0])
            for key,offset in {
                "null_x_plus8":[8,0],"null_x_minus8":[-8,0],
                "null_y_plus8":[0,8],"null_y_minus8":[0,-8]}.items():
                self.assertEqual(record["comparison"][key]["offset_source_logical_pixels"],offset)

    def test_registered_candidate_coverage_beats_four_fixed_shifts_but_remains_incomplete(self):
        for name,data in self.report["per_source_player"].items():
            r=data["comparison"]["registered"]
            self.assertGreater(r["interior_change_model_footprint_fraction"],.60)
            self.assertLess(r["interior_change_model_footprint_fraction"],.62)
            for control in CONTROLS-{"registered"}:
                self.assertGreater(r["interior_change_model_footprint_fraction"],
                                   data["comparison"][control]["interior_change_model_footprint_fraction"])
            self.assertGreater(r["original_interior_change_outside_candidate_model"],0)
            wheel=("tire","rim_and_hub","pedals")
            self.assertEqual(sum(r["per_candidate_2026_part_interior_change_instances"][part]
                                 for part in wheel),
                             {"blue":355,"red":439}[name])
            self.assertEqual(r["per_candidate_2026_part_interior_change_instances"]["saddle"],
                             {"blue":14,"red":0}[name])

    def test_optional_glb_runner_is_syntax_valid_without_heavy_dependency_import(self):
        source=TOOL.read_text(encoding="utf-8")
        ast.parse(source,filename=str(TOOL))
        self.assertIn("publish_text_once",source)
        self.assertIn("audit_mesen",source)
        self.assertIn("raster_part_ids",source)


if __name__=="__main__":
    unittest.main()

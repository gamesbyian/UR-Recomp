"""Model-free and actual-color-depth numerical controls for ART-4K fork paint."""
import unittest
import math

from tools.art.audit_original_racer_painted_frame_depth import rasterize_depth, variant_painted_angle_selections

try:
    import numpy as np
except ImportError:
    np=None

CAMERA={
    "schema":"UR-RACER-FIXED-ORTHOGRAPHIC-CAMERA/1",
    "camera_calibration_status":"provisional",
    "source_pixel_aspect":"7:6",
    "right_world":[1,0,0],"up_world":[0,0,1],
    "origin_world":[0,0,0],
    "logical_pixels_per_model_unit_vertical":9.5,
    "source_anchor_x2_y2":[67,76],
}


@unittest.skipUnless(np is not None,"optional NumPy")
class DepthPaintedAxisTests(unittest.TestCase):
    def triangle(self,front):
        # Construct projected raster triangle with selected source pixel centres.
        def world(x,y):
            return [(x-33.5)/(9.5*6/7),float(front),(38-y)/9.5]
        return np.array([world(20,20),world(30,20),world(20,30)],dtype=float)

    def test_front_and_back_flip_actual_visible_material(self):
        blue=self.triangle(0)
        dark=self.triangle(1)
        tris=np.array([blue,dark])
        ids=np.array([0,1],dtype=np.int32)
        plus,tie,hits=rasterize_depth(tris,ids,CAMERA,1)
        minus,other_tie,other_hits=rasterize_depth(tris,ids,CAMERA,-1)
        self.assertEqual(int(plus[22,22]),1)
        self.assertEqual(int(minus[22,22]),0)
        self.assertFalse(tie[22,22])
        self.assertFalse(other_tie[22,22])
        self.assertEqual(int(hits[22,22]),2)
        self.assertEqual(int(other_hits[22,22]),2)
        # Triangle winding must not change transparent-looking visibility.
        reverse=np.array([blue[[0,2,1]],dark[[0,2,1]]])
        rewound,_,_=rasterize_depth(reverse,ids,CAMERA,1)
        self.assertEqual(int(rewound[22,22]),1)

    def test_coplanar_distinct_material_marks_unknown_visibility(self):
        t=self.triangle(0)
        ownership,tied,_=rasterize_depth(
            np.stack([t,t]),np.array([0,1],dtype=np.int32),CAMERA)
        self.assertTrue(tied[22,22])
        self.assertIn(int(ownership[22,22]),(0,1))
        # Identical triangles of the SAME material are not ambiguous.
        _,same,_=rasterize_depth(
            np.stack([t,t]),np.array([0,0],dtype=np.int32),CAMERA)
        self.assertFalse(same[22,22])

    def test_nearer_third_material_resolves_prior_tie(self):
        t=self.triangle(0)
        close=self.triangle(2)
        ids=np.array([0,1,2],dtype=np.int32)
        owners,ties,_=rasterize_depth(
            np.stack([t,t,close]),ids,CAMERA,1)
        self.assertEqual(int(owners[22,22]),2)
        self.assertFalse(ties[22,22])

    def test_rejects_unsupported_projections_and_malformed_geometry(self):
        t=self.triangle(0)
        ids=np.array([0],dtype=np.int32)
        for sign in (0,2,True,"1"):
            with self.subTest(sign=sign),self.assertRaises(ValueError):
                rasterize_depth(np.stack([t]),ids,CAMERA,sign)
        with self.assertRaises(ValueError):
            rasterize_depth(np.stack([t]),np.array([0,1]),CAMERA)
        bad={**CAMERA,"source_anchor_x2_y2":[120,120]}
        with self.assertRaisesRegex(ValueError,"crop"):
            rasterize_depth(np.stack([t]),ids,bad)

    def test_source_rgb_variants_retain_different_5_degree_pose_hypotheses(self):
        from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import ANGLES
        predictions={"camera_from_plus_world_y":{a:float(-a) for a in ANGLES}}
        def variant(angle, suffix):
            return {"player":"p1","rgba_sha256":suffix*64,
                    "measurement":{"signed_axis_angle_from_image_vertical_deg":angle}}
        result=variant_painted_angle_selections(
            {"source_colour_variants":[variant(5.,"a"),variant(10.,"b")]},
            predictions)
        self.assertEqual(
            result["source_variant_pose_ambiguity"]["camera_from_plus_world_y"]["possible_hinge_degrees"],
            [-10,-5])
        self.assertTrue(result["source_variant_pose_ambiguity"]["camera_from_plus_world_y"]["variant_disagreement"])
        self.assertEqual(len(result["authenticated_source_rgba_variants"]),2)
        with self.assertRaisesRegex(ValueError,"source original colour variants absent"):
            variant_painted_angle_selections({"source_colour_variants":[]},predictions)
        with self.assertRaisesRegex(ValueError,"source original painted axis must be finite"):
            variant_painted_angle_selections(
                {"source_colour_variants":[variant(float("nan"),"a")]},predictions)

    def test_original_source_axis_selector_is_separate_from_iou(self):
        from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
            ANGLES,source_selected_angle)
        predictions={a:float(-a) for a in ANGLES}
        self.assertEqual(source_selected_angle(35.,predictions),-35)
        self.assertEqual(source_selected_angle(-30.,predictions),30)


if __name__=="__main__":
    unittest.main()

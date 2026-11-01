"""Source-bound whole-racer root-lean raster study: ROM-free negative contract."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
script=ROOT/"tools/art/evaluate_original_racer_lean_silhouettes.py"
spec=importlib.util.spec_from_file_location("real_rom_full_lean_study",script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    import numpy as np
except ImportError:
    np=None


def fake_scores(iou):
    return {
        label:{
            "mask_iou":float(iou[i]),
            "mask_xor_pixels":100+i,
            "boundary_chamfer_mean_physical_px":float(i),
            "lowest_alpha_delta_x2_y2":[0,0],
        } for i,label in enumerate(module.ANGLE_LABEL.values())
    }


def row(sharp, angles=(0.,-35.,10.,15.,30.)):
    return {
        "root_angle_degrees":{v:k for k,v in module.ANGLE_LABEL.items()},
        "unpaired_study_scores":fake_scores(sharp),
    }


class OriginalWholeSilhouetteLeanContract(unittest.TestCase):
    def test_exact_frozen_root_lean_studies(self):
        self.assertEqual(module.ANGLES,(0.,-35.,10.,15.,30.))
        self.assertEqual(set(module.ANGLE_LABEL),set(module.ANGLES))
        self.assertEqual(len(set(module.ANGLE_LABEL.values())),5)

    def test_summary_original_shape_one_vote_without_held_frame_multiplication(self):
        data={
            "a"*64:row((.50,.40,.60,.55,.42)),
            "b"*64:row((.30,.60,.30,.20,.30)),
            "c"*64:row((.45,.45,.45,.45,.45)),
        }
        output=module.summarize_per_mask(data)
        self.assertEqual(output["original_unique_binary_masks"],3)
        self.assertEqual(output["mean_full_silhouette_iou_per_fixed_source_root_pose"]
                         ["unchanged"],round((.50+.30+.45)/3,8))
        self.assertEqual(output["mean_iou_delta_relative_to_unmodified_upright"]
                         ["root-minus-35"],round((.40+.60+.45-.50-.30-.45)/3,8))
        self.assertTrue(output["source_frames_not_counted_as_independent"])
        self.assertFalse(output["original_frames_paired_to_1994_3d_pose"])

    def test_missing_duplicate_source_pose_or_nonfinite_score_rejected(self):
        data={"a"*64:row((.5,.6,.7,.8,.9))}
        bad=row((.5,.6,.7,.8,.9))
        del bad["unpaired_study_scores"]["root-plus-15"]
        with self.assertRaisesRegex(ValueError,"missing original"):
            module.summarize_per_mask({"a"*64:bad})
        with self.assertRaises(ValueError):
            module.summarize_per_mask({"wrong-hash":data["a"*64]})
        bad=row((.5,.6,.7,.8,.9))
        bad["unpaired_study_scores"]["root-plus-10"]["mask_iou"]=math.nan
        with self.assertRaises(ValueError):
            module.summarize_per_mask({"b"*64:bad})
        bad=row((.5,.6,.7,.8,.9))
        bad["unpaired_study_scores"]["root-plus-10"]["mask_iou"]=1.01
        with self.assertRaises(ValueError):
            module.summarize_per_mask({"b"*64:bad})

    @unittest.skipIf(np is None,"NumPy is optional offline art dependency")
    def test_actual_3d_root_rotation_and_tire_height_no_mesh_mutation(self):
        # This validates the SAME algebra used on actual SHA-locked GLB vertices
        # in the source-ROM producer, without requiring OpenSCAD in the unit job.
        vertices=np.asarray(((0,0,0),(1,0,0),(0,0,3.0)),dtype=float)
        tire=np.asarray(((0,0,0),(-.25,0,.25),(.25,0,.25)),dtype=float)
        original=vertices.copy()
        fixed=module.rotate_y_with_contact(vertices,tire,0.)
        np.testing.assert_allclose(fixed[0],original,atol=1e-12)
        for deg in module.ANGLES:
            turned,meta=module.rotate_y_with_contact(vertices,tire,deg)
            np.testing.assert_allclose(vertices,original,atol=1e-12)
            self.assertAlmostEqual(meta["preserved_original_tire_min_source_z"],0.)
            self.assertFalse(meta["original_1994_contact_physics_recovered"])
            self.assertEqual(turned.shape,vertices.shape)
            self.assertTrue(np.isfinite(turned).all())
        for invalid in (42.,float("nan"),float("inf"),"-35",None):
            with self.subTest(angle=invalid),self.assertRaises(ValueError):
                module.rotate_y_with_contact(vertices,tire,invalid)
        with self.assertRaises(ValueError):
            module.rotate_y_with_contact(vertices,np.zeros((0,3)),0.)
        with self.assertRaises(ValueError):
            module.rotate_y_with_contact(np.asarray(((0,0,float("nan")),)),tire,0.)


if __name__=="__main__":
    unittest.main()

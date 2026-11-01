"""Cheap source-bound 2026 root-lean grid coverage and anti-overclaim tests."""
import importlib.util
from pathlib import Path
import unittest
import math

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "art4k_root_lean_grid",ROOT/"tools/art/study_original_racer_root_lean_grid.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def inputs():
    originals=[
        {"source_binary_mask_sha256":f"{i:064x}",
         "source_image_space_angle_deg":float(a)}
        for i,a in enumerate((-29,-16,-8,1,15,43))
    ]
    baseline={
        "upright":6.9,"pedal":6.9,"wheelie":33.8,
        "stunt":-43.2,"bank":9.2,
    }
    return originals,baseline


class LeanGridTests(unittest.TestCase):
    def test_fixed_bounded_including_original_zero(self):
        self.assertEqual(mod.ANGLES[0],-45.0)
        self.assertEqual(mod.ANGLES[-1],50.0)
        self.assertEqual(len(mod.ANGLES),20)
        self.assertIn(0.0,mod.ANGLES)
        self.assertEqual(len(set(mod.ANGLES)),20)
        self.assertEqual(mod.PIVOT_WORLD_XYZ,(0.0,0.0,0.0))

    def test_more_source_directions_cannot_worsen_best_nearest_gap(self):
        original,baseline=inputs()
        a=mod.coverage(original,baseline,[])
        b=mod.coverage(original,baseline,[-14.4,40.5])
        self.assertLess(b["mean_nearest_projected_axis_gap_deg"],
                        a["mean_nearest_projected_axis_gap_deg"])
        self.assertLessEqual(b["source_masks_gap_above_10deg"],
                             a["source_masks_gap_above_10deg"])
        self.assertEqual(b["source_original_unique_binary_masks"],6)
        self.assertTrue(b["one_original_mask_one_vote"])

    def test_duplicate_mask_fake_angle_missing_pose_refused(self):
        original,baseline=inputs()
        duplicates=[dict(x) for x in original]
        duplicates[1]["source_binary_mask_sha256"]=duplicates[0]["source_binary_mask_sha256"]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            mod.coverage(duplicates,baseline,[])
        fake=[dict(x) for x in original]
        fake[0]["source_image_space_angle_deg"]=float("nan")
        with self.assertRaises(ValueError):
            mod.coverage(fake,baseline,[])
        bad=dict(baseline);del bad["bank"]
        with self.assertRaises(ValueError):
            mod.coverage(original,bad,[])
        with self.assertRaises(ValueError):
            mod.coverage(original,baseline,[91.])
        with self.assertRaises(ValueError):
            mod.coverage(original,baseline,[math.inf])


if __name__=="__main__":
    unittest.main()

"""Unapproved one-rig saddle source fidelity and bounded shape studies."""
import math
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.art import render_shared_unicycle_review as still
from tools.art import render_shared_unicycle_motion as motion

class BoundedSourceCharacter(unittest.TestCase):
    def test_default_source_painter_keeps_original_geometry_expression(self):
        source=(ROOT/"tools/art/candidates/unicycle_shared_rig.scad").read_text(encoding="utf8")
        self.assertIn("rig_saddle_cup=is_undef(rig_saddle_cup)?1:rig_saddle_cup;",source)
        self.assertIn("rig_saddle_depth=is_undef(rig_saddle_depth)?1:rig_saddle_depth;",source)
        self.assertIn("if (rig_saddle_cup==1 && rig_saddle_depth==1)",source)
        self.assertIn("translate([x,0,h])scale([rx,ry,rz])sphere(1,$fn=40);",source)
        self.assertIn("translate([x,0,h*rig_saddle_cup])scale([rx,ry,rz*rig_saddle_depth])sphere(1,$fn=40);",source)
        self.assertEqual(source.count("module shared_rig("),1)
        self.assertEqual(source.count("rig(rig_pose);"),1)
        self.assertNotIn("shipping_art_approved=true",source)

    def test_cupped_shape_is_bounded_not_inferred_source_geometry(self):
        self.assertEqual(still.SADDLE_CUP_CHOICES,(1.0,1.7,2.25))
        self.assertEqual(still.SADDLE_DEPTH_CHOICES,(1.0,1.45,1.65))
        self.assertEqual(still.validate_cupped_saddle(1.7,1.45),(1.7,1.45))
        for bad in [(0.0,1.0),(1.0,2.0),(1.5,1.45),(True,1.0),
                    (math.nan,1.0),(1.0,math.inf),("1.7",1.45)]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                still.validate_cupped_saddle(*bad)

    def test_motion_camera_never_autofits_per_frame(self):
        self.assertEqual(motion.MOTION_CAMERAS[12.5],motion.CAMERA)
        self.assertEqual(len(motion.MOTION_CAMERAS),2)
        source=(ROOT/"tools/art/render_shared_unicycle_motion.py").read_text()
        for term in ('f"--camera={camera}"','"motion_fixed_camera_distance": camera_distance',
                     '"review_saddle_cup": saddle_cup','"review_saddle_depth": saddle_depth',
                     'common_pose_crop([row["silhouette_bbox"] for row in actual]'):
            self.assertIn(term,source)
        self.assertNotIn("--viewall",source)
        self.assertNotIn("--autocenter",source)
        self.assertIn('"owner_visual_approval": False',source)
        self.assertIn('"shipping_art_approved": False',source)
        self.assertEqual(len(motion.samples(8)),18)

    def test_both_scripts_still_operate_as_direct_standalone_cli(self):
        for script in ("render_shared_unicycle_review.py",
                       "render_shared_unicycle_motion.py"):
            proc=subprocess.run([sys.executable,str(ROOT/"tools/art"/script),"--help"],
                                text=True,capture_output=True,timeout=10)
            with self.subTest(script=script):
                self.assertEqual(proc.returncode,0,proc.stderr)
                self.assertIn("--saddle-cup",proc.stdout)
                self.assertIn("--saddle-depth",proc.stdout)
                if "motion" in script:
                    self.assertIn("--camera-distance",proc.stdout)

    def test_static_reviewer_is_review_only(self):
        source=(ROOT/"tools/art/render_shared_unicycle_review.py").read_text()
        self.assertIn('f"rig_saddle_cup={saddle_cup}"',source)
        self.assertIn('f"rig_saddle_depth={saddle_depth}"',source)
        self.assertIn('"human_visual_approval":False',source)
        self.assertIn('"asset_runtime_integration":False',source)
        self.assertIn('"release_gate":False',source)
if __name__=="__main__":
    unittest.main()

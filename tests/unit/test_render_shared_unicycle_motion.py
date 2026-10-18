"""One-model continuous animation review, without renderer/Pillow dependency.

Actual OpenSCAD/Pillow images are checked by the optional offline authoring
tool, not product CI or any original 2014 PPU source raster acceptance.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.art import render_shared_unicycle_motion as motion


class SharedRigMotionContract(unittest.TestCase):
    def setUp(self):
        self.rig=ROOT/"tools/art/candidates/unicycle_shared_rig.scad"
        self.source=self.rig.read_text(encoding="utf-8")
        self.reviewer=(ROOT/"tools/art/render_shared_unicycle_motion.py").read_text(
            encoding="utf-8")

    def test_two_complete_cycles_share_one_canonical_character(self):
        frames=motion.samples()
        self.assertEqual(len(frames),18)
        self.assertEqual([x[1] for x in frames[:9]],list(range(9)))
        self.assertEqual([x[1] for x in frames[9:]],list(range(9)))
        self.assertEqual(frames[0],("ride",0,0.0))
        self.assertEqual(frames[8],("ride",8,1.0))
        self.assertEqual(frames[9],("stunt_cycle",0,0.0))
        self.assertEqual(frames[-1],("stunt_cycle",8,1.0))
        dense = motion.samples(16)
        self.assertEqual(len(dense),34)
        self.assertEqual(dense[0],("ride",0,0.0))
        self.assertEqual(dense[16],("ride",16,1.0))
        self.assertEqual(dense[17],("stunt_cycle",0,0.0))
        self.assertEqual(dense[-1],("stunt_cycle",16,1.0))
        with self.assertRaises(ValueError):
            motion.samples(7)
        with self.assertRaises(ValueError):
            motion.samples(17)
        self.assertEqual(self.source.count("module continuous_rig("),1)
        self.assertEqual(self.source.count("shared_rig(pedal=18+720*u"),1)
        self.assertEqual(self.source.count('else if(p=="ride")'),1)
        self.assertEqual(self.source.count('else if(p=="stunt_cycle")'),1)
        self.assertEqual(self.source.count("rig(rig_pose);"),1)
        self.assertIn("360*ease_time(u)",self.source)
        self.assertIn("rotate([0,-pitch,0])",self.source)
        self.assertIn("function unit_time(t)",self.source)

    def test_camera_is_one_fixed_source_across_all_samples(self):
        self.assertEqual(motion.CAMERA,"0,0,1.6,90,0,0,12.5")
        self.assertEqual(motion.RENDER_SIZE,320)
        self.assertEqual(motion.MIN_BORDER_PIXELS,4)
        self.assertIn('f"--camera={CAMERA}"',self.reviewer)
        self.assertNotIn("--viewall",self.reviewer)
        self.assertNotIn("--autocenter",self.reviewer)
        self.assertIn("model clipped at fixed-camera viewport boundary",self.reviewer)
        self.assertIn('"all_source_model_unclipped": True',self.reviewer)
        self.assertIn('"source_animation_frame_count": count',self.reviewer)
        self.assertIn('"two_continuous_motion_loops_pixel_exact_at_endpoints": True',self.reviewer)
        self.assertIn("animated rig loop has discontinuous rendered endpoints",self.reviewer)

    def test_full_pixel_border_guard_blocks_real_crop_not_just_corners(self):
        w=h=16
        data={(x,y):(248,248,248) for y in range(h) for x in range(w)}
        data[8,8]=(20,70,210)
        self.assertEqual(motion.require_clean_border(data,w,h),(248,248,248))
        for x,y in ((0,8),(1,8),(3,8),(8,3),(15,8),(8,15),(0,0)):
            sample=dict(data)
            sample[x,y]=(0,0,0)
            with self.subTest(x=x,y=y),self.assertRaises(ValueError):
                motion.require_clean_border(sample,w,h)
        with self.assertRaises(ValueError):
            motion.require_clean_border({(0,0):(255,255,255)},8,16)

    def test_no_shipping_or_fake_source_acceptance(self):
        for statement in (
            '"original_gameplay_stunt_kinematics_proven": False',
            '"gameplay_contact_and_pixel_aspect_registered": False',
            '"owner_visual_approval": False',
            '"shipping_art_approved": False',
            '"native_game_runtime_modified": False',
            '"release_accepted": False',
        ):
            self.assertIn(statement,self.reviewer)
        for unsafe in ("PpuSetOverlayOamRange","SNESRECOMP_DUMP_DIR",
                       "native/presentation/racer_hd_presenter.cpp"):
            self.assertNotIn(unsafe,self.reviewer)

    def test_unreviewable_modified_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            invalid=Path(td)/"altered.scad"
            invalid.write_text(self.source.replace("rig(rig_pose);",""),encoding="utf-8")
            with self.assertRaises(ValueError):
                motion.inspect_model(invalid)


if __name__=="__main__":
    unittest.main()

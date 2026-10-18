"""Bounded single-rig saddle-identity review, never pixel or art acceptance."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.art import render_unicycle_saddle_variants as study

class SaddleExperimentBoundaries(unittest.TestCase):
    def setUp(self):
        self.model=ROOT/"tools/art/candidates/unicycle_shared_rig.scad"
        self.text=self.model.read_text(encoding="utf-8")
        self.script=(ROOT/"tools/art/render_unicycle_saddle_variants.py").read_text()

    def test_one_canonical_rig_and_exactly_bounded_proposal_values(self):
        self.assertEqual(study.SPANS,(1.0,1.4,1.8,2.2))
        self.assertEqual(study.SPANS,study.SADDLE_CHOICES)
        self.assertEqual(study.FRAME_CHOICES,(1.0,1.4,1.8,2.0))
        self.assertEqual(study.CAMERA,"0,0,1.6,90,0,0,22")
        self.assertEqual(study.SIZE,400)
        self.assertIn("bbox=occupied_bounds(im)",self.script)
        self.assertIn("range(0,int(SIZE*0.42))",self.script)
        study.prove_parameters(self.text)
        self.assertEqual(self.text.count("scale([rig_saddle_span,1,1])"),1)
        self.assertEqual(self.text.count('rig(rig_pose);'),1)
        self.assertIn("is_undef(rig_saddle_span)?1:rig_saddle_span",self.text)
        self.assertIn("out-of-scope unreviewed saddle shape",self.text)
        self.assertIn("out-of-scope unreviewed fork mass",self.text)
        self.assertIn("is_undef(rig_frame_mass)?1:rig_frame_mass",self.text)
        self.assertIn("r1*rig_frame_mass",self.text)
        self.assertEqual(self.text.count("module frame_member("),1)
        self.assertEqual(self.text.count("frame_member("),6)
        self.assertIn('"bounded_frame_mass":frame_mass',self.script)
        self.assertIn('validate_variant(span, frame_mass)',self.script)


    def test_missing_or_unbounded_shared_parameter_is_rejected(self):
        for replacement in (
            self.text.replace("rig_saddle_span=is_undef","wrong=is_undef"),
            self.text.replace("rig_saddle_span <= 2.2","rig_saddle_span <= 99"),
            self.text.replace("rig_frame_mass <= 2","rig_frame_mass <= 99"),
            self.text.replace("scale([rig_saddle_span,1,1])","scale([1,1,1])"),
            self.text.replace('rig(rig_pose);','rig("upright");'),
        ):
            with self.subTest(s=replacement[:80]),self.assertRaises(ValueError):
                study.prove_parameters(replacement)

    def test_source_identity_and_no_false_3d_or_shipping_claims(self):
        for fragment in (
            '"original_title_wheel_top_unmeasurable_occluded":True',
            '"title_camera_perspective_unknown":True',
            '"original_source_3d_dimensions_inferred":False',
            '"owner_visual_approval":False',
            '"shipping_art_approved":False',
            '"release_accepted":False',
            'authentic_sources(source_zip)',
            'Image.Resampling.NEAREST',
        ):
            self.assertIn(fragment,self.script)
        self.assertNotIn("PpuSetOverlayOamRange",self.script)
        self.assertNotIn("native/presentation/racer_hd_presenter.cpp",self.script)
        with tempfile.TemporaryDirectory() as d:
            bad=Path(d)/"invalid-original.zip"
            bad.write_bytes(b"not real original 2014 source archive")
            from tools.art.render_shared_unicycle_review import authentic_sources
            with self.assertRaises(ValueError):
                authentic_sources(bad)

if __name__=="__main__":
    unittest.main()

"""Art-blockout authority: source identity, one rig, no accidental product admission.

No OpenSCAD, Pillow, archived pixels, network, GPU or packaging needed in CI.
An artist may additionally run the full fixed-camera offline review command.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.art import render_shared_unicycle_review as study


class SharedRigArtBoundary(unittest.TestCase):
    def setUp(self):
        self.model = ROOT / "tools/art/candidates/unicycle_shared_rig.scad"
        self.script = ROOT / "tools/art/render_shared_unicycle_review.py"

    def test_one_explicit_same_rig_in_all_five_poses(self):
        self.assertEqual(len(study.POSES), 5)
        self.assertEqual(len(study.CAMERAS), 2)
        self.assertEqual(len(set(study.CAMERAS.values())), 2)
        self.assertTrue(all(v.endswith(",22") for v in study.CAMERAS.values()))
        source = self.model.read_text(encoding="utf-8")
        self.assertEqual(source.count("rig(rig_pose);"), 1)
        self.assertTrue(study.inspect_model(self.model))
        for item in study.GEOMETRY_MODULES:
            self.assertEqual(source.count(item), 1)
        self.assertIn('else if(p=="stunt")', source)
        self.assertIn('translate([0,0,-1.80])', source)
        self.assertNotIn("PpuSetOverlayOamRange", source)

    def test_competing_or_missing_geometry_fails_closed(self):
        source = self.model.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            candidate = Path(td) / "alternate.scad"
            for text in (
                source.replace("module tire()", "module fake_tire()", 1),
                source.replace("rig(rig_pose);", "model();", 1),
                source.replace('p=="stunt"', 'p=="unknown"', 1),
                source + "\n// current_visual_approval=true\n",
            ):
                with self.subTest(sample=text[-60:]):
                    candidate.write_text(text, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        study.inspect_model(candidate)

    def test_reference_zip_sha_and_source_member_names_are_pinned(self):
        self.assertEqual(study.AOT_SHA,
            "6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431")
        self.assertEqual(list(study.SOURCES),
                         ["original_title", "original_gameplay", "visually_rejected_4x"])
        with tempfile.TemporaryDirectory() as td:
            fabricated = Path(td) / "fake-aot.zip"
            fabricated.write_bytes(b"not real original source")
            with self.assertRaisesRegex(ValueError, "source archive identity mismatch"):
                study.authentic_sources(fabricated)

    def test_review_is_offline_fixed_camera_and_no_shipping_claim(self):
        source = self.script.read_text(encoding="utf-8")
        self.assertIn("--camera=", source)
        self.assertIn("bounds = occupied_bounds(im)",source)
        self.assertIn('"all_static_source_model_frames_unclipped": True',source)
        self.assertNotIn("--viewall", source)
        self.assertNotIn("--autocenter", source)
        self.assertIn("round(src.width*7/6)",source)
        self.assertIn("Image.Resampling.NEAREST",source)
        self.assertIn('"shipping_ready":False', source)
        self.assertIn('"human_visual_approval":False', source)
        self.assertIn('"original_native_RGB5_PPU_equivalence":False', source)
        self.assertIn('"asset_runtime_integration":False', source)
        self.assertEqual(tuple(study.POSES),
            ("upright", "pedal", "wheelie", "stunt", "bank"))


if __name__ == "__main__":
    unittest.main()

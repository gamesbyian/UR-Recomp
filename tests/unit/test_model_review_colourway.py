"""Independent, reversible 2026 GLB colourway review, never 1994 albedo."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class ModelReviewIndependentColourwayTests(unittest.TestCase):
    def test_independent_p1_p2_model_control_is_source_sha_gated(self):
        text=(ROOT/"tools/art/model-review/index.html").read_text()
        for marker in (
            '<label for="modelColourway">',
            'id="modelColourwayStatus"',
            'id="modelColourway"',
            '<option value="p1">Provisional P1 red frame</option>',
            '<option value="p2">Original 2026 blue model</option>',
            'function restoreModelColourway()',
            'function captureModelColourway(origin)',
            'function applyModelColourway(choice)',
            'function updateModelColourwayStatus(origin',
            "if(!wheelDriveState||!origin.startsWith('published ')||",
            "manifest?.source_model_sha256!==SOURCE_SHA",
            "material.color.setRGB(211/255,43/255,47/255,THREE.SRGBColorSpace)",
            "modelColourway='p2';colourState=captureModelColourway(origin)",
            "restoreUpperShape();restorePaintMaterials();restoreModelColourway();",
            "status.dataset.modelColourState=",
            "status.dataset.modelColourWireframe=",
            "record.mesh.material=record.original",
            "temporary?.dispose()",
            "material.vertexColors=false",
            "material.wireframe=wireframe",
            "record.original.wireframe=wireframe",
            "modelColourway='p2';colourState=null",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,text)
        self.assertNotIn("mesh.geometry.setAttribute",text)
        self.assertNotIn("record.original.color.setRGB",text)

    def test_source_rgb_is_proposal_and_original_sprite_control_is_independent(self):
        text=(ROOT/"tools/art/model-review/index.html").read_text()
        self.assertIn("RGB 211/43/47",text)
        self.assertIn("not original 1994 material albedo",text)
        self.assertIn("never changes the original racer or sprite reference",text)
        self.assertIn("modelColourway='p2';colourState=null",text)
        self.assertIn("modelColourway='p2';colourState=captureModelColourway(origin)",text)
        self.assertNotIn("modelColourway=$('player').value",text)
        self.assertNotIn("$('player').value=modelColourway",text)

    def test_real_browser_qualification_covers_visual_restore_and_pose_switch(self):
        script=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text()
        for marker in (
            "model colourway touch target too small",
            "synthetic non-source model falsely enabled colourways",
            "real source GLB model colourway disabled",
            "model colourway not implemented",
            "model colourway changed GLB source identity",
            "model colourway persisted across named pose",
            "provisional red change did not alter actual GLB viewport pixels",
            "provisional red model pixels not exactly restored",
            "model-review-p1-red-412.png",
            "model-review-p2-blue-412.png",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,script)

if __name__=="__main__":
    unittest.main()

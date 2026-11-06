"""One-source GLB experimental material-allocation switch, ROM-free contracts."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class ModelReviewPaintHypothesesTests(unittest.TestCase):
    def test_one_pages_viewer_preserves_historical_model_source_gate(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text()
        for marker in (
            'id="paintHypothesis"',
            'id="paintStatus"',
            'min-height:44px;min-width:0;width:100%;max-width:100%',
            "manifest?.source_model_sha256!==SOURCE_SHA",
            "if(!wheelDriveState||!origin.startsWith('published ')",
            "function capturePaintMaterials(origin)",
            "function applyPaintHypothesis(choice)",
            "function restorePaintMaterials()",
            "paintState=capturePaintMaterials(origin)",
            "updatePaintHypothesisStatus(origin)",
        ):
            self.assertIn(marker,html)
        self.assertIn("function clear(){if(current){restoreHubFace();restoreBladeSpokes();restoreUpperShape();restorePaintMaterials();",html)
        self.assertIn("paintMode='original';paintState=null",html)
        self.assertIn("restoreHubFace();restoreBladeSpokes();restoreUpperShape();restorePaintMaterials();restoreModelColourway();scene.remove(current)",html)

    def test_recolor_only_clone_material_not_source_vertex_or_geometry(self):
        html=(ROOT/"tools/art/model-review/index.html").read_text()
        for marker in (
            "const material=record.original.clone()",
            "material.wireframe=wireframe",
            "record.original.wireframe=wireframe",
            "status.dataset.materialWireframe=paintState?",
            "if(new URLSearchParams(location.search).has('art4k-still'))",
            "renderer.setAnimationLoop(null)",
            "renderer.domElement.toDataURL('image/png')",
            "material.vertexColors=false",
            "material.color.setRGB(28/255,89/255,222/255,THREE.SRGBColorSpace)",
            "record.mesh.material=material",
            "record.mesh.material=record.original",
            "temporary?.dispose()",
            "PAINT_HYPOTHESES=Object.freeze",
            "PAINT_PARTS=Object.freeze",
            "original:Object.freeze([])",
            "area:Object.freeze(['rim_and_hub__material_1','pedals__material_1'])",
            "disc:Object.freeze(['rim_and_hub__material_2','pedals__material_1'])",
            "discPlus:Object.freeze(['rim_and_hub__material_2','pedals__material_0','pedals__material_1'])",
        ):
            self.assertIn(marker,html)
        self.assertNotIn("mesh.geometry.setAttribute",html)
        self.assertNotIn("original.material.color.setRGB",html)
        self.assertIn("No source geometry or release likeness approval",html)

    def test_existing_real_browser_harness_checks_all_three_size_variants(self):
        smoke=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text()
        for marker in (
            "paint hypothesis touch target too small",
            "synthetic non-source model falsely enabled paint hypotheses",
            "real source GLB paint hypothesis disabled",
            "paint material choice not implemented",
            "paint material not recoloured",
            "paint experiment failed exact original material restoration",
            "paint experiment changed source GLB identity or mesh census",
            "paint experiment persisted after changing actual published GLB",
            "paint experiment leaked across named pose roundtrip",
            "actual 3D paint hypothesis changed labels but not GLB viewport pixels",
            "stationary original 3D GLB paint pixels not exactly restored",
            "model-review-paint-disc-412.png",
            "paint transition lost active wireframe",
            "wireframe off did not restore solid material render",
            "source GLB still-frame capture hook/camera unavailable",
            "window.__urArt4kVisualReadback.snapshot()",
            "window.__urArt4kVisualReadback.resume()",
        ):
            self.assertIn(marker,smoke)
        self.assertIn("320",smoke)
        self.assertIn("412",smoke)
        self.assertIn("1440",smoke)


if __name__=="__main__":
    unittest.main()

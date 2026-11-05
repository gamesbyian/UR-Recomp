"""Reversible source-owned 2026 saddle/frame preview in sole Pages reviewer."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]

class AuthoredUpperShapeViewerTests(unittest.TestCase):
    def test_only_existing_model_review_route_and_nonshipping_source_gate(self):
        page=(ROOT/"tools/art/model-review/index.html").read_text()
        self.assertIn('id="upperShape"',page)
        self.assertIn('id="upperShapeStatus"',page)
        self.assertIn("authored_upper_shape_controls.mjs",page)
        self.assertIn('if(!current||!wheelDriveState||!origin.startsWith(\'published \'))return null',page)
        self.assertIn("frameHinge!==0",page)
        self.assertIn("restoreUpperShape();restorePaintMaterials();",page)
        self.assertIn("temporary?.dispose()",page)
        self.assertIn("clone.computeVertexNormals()",page)
        self.assertIn("Upper-shape preview unavailable:",page)
        self.assertIn("No original 1994 speed or saddle stroke law recovered.",page)
        self.assertIn("min-height:44px",page)
        self.assertIn("Original 1994 sprite",page)
        for marker in (
            '<option value="saddle-narrow">Saddle contour 10% narrower</option>',
            '<option value="saddle-wide">Saddle contour 10% wider</option>',
            "saddleMeshes.push({mesh,geometry:mesh.geometry})",
            "mesh.parent!==saddle",
            "const clone=geometry.clone(),pos=clone.getAttribute('position')",
            "pos.setX(i,pos.getX(i)*proposal.saddleSpan)",
            "status.dataset.saddleSpan=",
            "upperShapeState.fork,...upperShapeState.saddleMeshes",
            "No original 1994 speed, saddle stroke or saddle 3D contour recovered.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,page)
        smoke=(ROOT/"tools/art/model-review/browser-smoke.mjs").read_text()
        for marker in (
            "real saddle contour 0.90 shape changed original mount",
            "real saddle contour 1.10 shape changed original mount",
            "real saddle contour hypotheses failed to change source GLB viewport pixels",
            "saddle contour preview did not restore exact original GLB canvas pixels",
            "model-review-saddle-narrow-412.png",
            "model-review-saddle-wide-412.png",
        ):
            with self.subTest(smoke=marker):
                self.assertIn(marker,smoke)
        for filename in ("tools/windows_visual_atlas.py","tools/art/model-review/stage_pages.py"):
            source=(ROOT/filename).read_text()
            self.assertIn("authored_upper_shape_controls.mjs",source)

    @unittest.skipUnless(shutil.which("node"),"node not available")
    def test_frozen_source_authored_3d_interventions(self):
        proc=subprocess.run(["node","--test",
           "tools/art/model-review/test_authored_upper_shape_controls.mjs"],
           cwd=ROOT,text=True,capture_output=True,timeout=20)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

if __name__=="__main__":
    unittest.main()

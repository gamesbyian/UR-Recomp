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

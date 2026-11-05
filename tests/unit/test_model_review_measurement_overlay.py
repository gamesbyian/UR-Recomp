"""ROM-free Node tests for the existing Pages viewer's optional research overlay."""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ModelReviewMeasurementBrowserContract(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js not available in this build environment")
    def test_verified_source_overlay_contract_in_node(self):
        script = ROOT / "tools/art/model-review/test_measurement_overlay.mjs"
        result = subprocess.run(
            [shutil.which("node"), "--test", str(script)],
            cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=40, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout[-4000:])

    def test_viewer_opt_in_does_not_claim_original_pose_authenticity(self):
        index = (ROOT / "tools/art/model-review/index.html").read_text(encoding="utf-8")
        self.assertIn("measurement_overlay.mjs", index)
        self.assertIn("validateMeasurements(", index)
        self.assertIn("aria-expanded=\"false\"", index)
        self.assertIn("Unpaired 2D silhouette similarities, provisional camera.", index)
        self.assertIn("const res=await fetch('./model-measurements.json'", index)
        self.assertIn("measurements=null;$('measurements').hidden=true;", index)
        self.assertNotIn("sourcePoseToModelPose=", index)


if __name__ == "__main__":
    unittest.main()

"""Exact-source 2026 hub cover Pages integration, not original 1994 geometry."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
VIEW = ROOT / "tools/art/model-review/index.html"
HELPER = ROOT / "tools/art/model-review/source_hub_cover_view.mjs"


class HubCoverViewerTests(unittest.TestCase):
    def test_source_bound_existing_viewer_and_both_site_builders(self):
        html = VIEW.read_text(encoding="utf-8")
        for marker in (
            'id="hubFace"', 'id="hubFaceStatus"',
            "source_hub_cover_view.mjs",
            "SOURCE_2026_HUB_VERTICES", "SOURCE_2026_HUB_FACES",
            "manifest?.source_model_sha256!==SOURCE_SHA",
            "!origin.startsWith('published ')",
            "const {mesh,geometry}=hubFaceState",
            "function restoreHubFace()",
            "function applyHubFace(mode)",
            "clone.computeVertexNormals()",
            "mesh.geometry=clone;hubFaceMode=mode",
            "restoreHubFace();restoreBladeSpokes()",
            "temporary?.dispose()",
            "No game geometry or file is modified.",
            "original 1994",
            "min-height:44px",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertTrue(HELPER.is_file())
        for source_path in ("tools/windows_visual_atlas.py",
                            "tools/art/model-review/stage_pages.py"):
            source = (ROOT / source_path).read_text(encoding="utf-8")
            self.assertIn("source_hub_cover_view.mjs", source)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_js_real_closed_3d_geometry_contract(self):
        process = subprocess.run(
            ["node", "--test", "tools/art/model-review/test_source_hub_cover_view.mjs"],
            cwd=ROOT, text=True, capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0,
                         process.stdout + "\n" + process.stderr)


if __name__ == "__main__":
    unittest.main()

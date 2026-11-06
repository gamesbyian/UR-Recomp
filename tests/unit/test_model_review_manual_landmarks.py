"""Locally handled manual evidence reviewer, no source images into server or GLB."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
VIEWER=ROOT/"tools/art/model-review"

class LocalOriginalPrintedManualReviewerTests(unittest.TestCase):
    def test_source_strict_local_page_is_copied_by_both_pages_publication_paths(self):
        host=(VIEWER/"index.html").read_text(encoding="utf-8")
        form=(VIEWER/"manual-landmarks.html").read_text(encoding="utf-8")
        helper=(VIEWER/"manual_landmark_marking.mjs").read_text(encoding="utf-8")
        self.assertIn('id="manualFigureLink"',host)
        self.assertIn('href="./manual-landmarks.html"',host)
        for path in ("tools/windows_visual_atlas.py",
                     "tools/art/model-review/stage_pages.py"):
            with self.subTest(path=path):
                script=(ROOT/path).read_text(encoding="utf-8")
                self.assertIn('"manual-landmarks.html"',script)
                self.assertIn('"manual_landmark_marking.mjs"',script)
        for value in ("source-crops.json","sourceFiles","pointerdown",
                      "crypto.subtle.digest",
                      "showSaveFilePicker","application/json",
                      "manual_landmark_marking.mjs"):
            self.assertIn(value,form)
        for value in ("UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1",
                      "source_pdf_sha256","crop_png_sha256",
                      "observation","unmeasurable","No original 1994"):
            if value=="observation":
                self.assertIn("annotations:",helper)
            elif value=="No original 1994":
                self.assertIn("No original 1994 3D",form)
            else:
                self.assertIn(value,form+helper)
        self.assertNotIn("<script src=\"http",form)
        self.assertNotIn("fetch(",form)
        self.assertIn("No images are uploaded",form)
        for marker in ('id="partialSurface"','id="surfaceStart"',
                       'id="surfaceFinish"','id="surfaceDelete"',
                       'id="surfaceStatus"','source polygon'):
            if marker == "source polygon":
                self.assertIn("source polygon",form.lower()+helper.lower())
            else:
                self.assertIn(marker,form)
        self.assertIn("addVisibleSurfaceRegion",helper)
        self.assertIn("clearVisibleSurfaceRegions",helper)

    @unittest.skipUnless(shutil.which("node"),"Node.js not installed")
    def test_client_annotations_preserve_2d_only_and_reject_partial_sources(self):
        proc=subprocess.run(
            ["node","--test",
             "tools/art/model-review/test_manual_landmark_marking.mjs",
             "tools/art/model-review/test_manual_visible_surface_regions.mjs"],
            cwd=ROOT,text=True,capture_output=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)


if __name__=="__main__":
    unittest.main()

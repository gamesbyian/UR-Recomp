"""Manual-like Pages orbits never assert actual 1994 model/camera recovery."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
VIEW=ROOT/"tools/art/model-review/index.html"
SOURCE=ROOT/"tools/art/model-review/manual_view_directions.mjs"
SMOKE=ROOT/"tools/art/model-review/browser-smoke.mjs"

class OfficialPrint3DCameraViewTests(unittest.TestCase):
    def test_reversible_camera_only_same_published_glb_and_source_refs(self):
        html=VIEW.read_text(encoding="utf-8")
        helper=SOURCE.read_text(encoding="utf-8")
        smoke=SMOKE.read_text(encoding="utf-8")
        for value in ("print-fork","print-hub","Print fork","Print hub",
                      "printedPage:14","printedPage:15",
                      "camera_is_original_1994_rendering:false",
                      "model_mesh_geometry_unchanged:true"):
            self.assertIn(value,helper)
        for value in ("cameraViewDirection","manualViewStatus",
                      "source camera is uncalibrated","source GLB unchanged"):
            self.assertIn(value,html)
        for value in ("Print fork","Print hub","manualViewStatus",
                      "manual camera changed original reference image identity"):
            self.assertIn(value,smoke)
        self.assertIn("manual_view_directions.mjs",
                      ROOT.joinpath("tools/windows_visual_atlas.py").read_text(encoding="utf-8"))
        self.assertIn("manual_view_directions.mjs",
                      ROOT.joinpath("tools/art/model-review/stage_pages.py").read_text(encoding="utf-8"))
        self.assertNotIn("cameraViewDirection",ROOT.joinpath(
            "tools/art/model-review/original_mesen24_rail.mjs").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()

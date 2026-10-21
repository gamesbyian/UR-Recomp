"""ROM-free tests of suggested screenshot ROI; no physical render acceptance."""
import subprocess
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from qa06_raster_roi_reference import raster_roi, report


class ScreenshotROIPolicy(unittest.TestCase):
    def test_4k_original_exact(self):
        x = raster_roi(256, 224, 3840, 2160)
        self.assertEqual(x["roi_xywh"], [480, 0, 2880, 2160])
        self.assertEqual(x["pixel_margin_lr"], [480, 480])
        self.assertEqual(x["pixel_margin_tb"], [0, 0])

    def test_4k_wide_uses_all_source_rows(self):
        x = raster_roi(342, 224, 3840, 2160, horizontal_fit=F(512,513))
        self.assertEqual(x["roi_xywh"], [0, 0, 3840, 2160])
        self.assertEqual(x["full_source_interval"], [0, 342, 0, 224])
        self.assertEqual(x["pixel_margin_tb"], [0, 0])
        self.assertFalse(x["physical_acceptance"])

    def test_216_crop_is_not_the_original_reference(self):
        full = raster_roi(256, 224, 3840, 2160)
        cropped = raster_roi(256, 216, 3840, 2160)
        self.assertNotEqual(full["roi_xywh"], cropped["roi_xywh"])
        self.assertNotEqual(full["full_source_interval"], cropped["full_source_interval"])

    def test_five_host_roi_in_bounds_and_centered(self):
        for host, cases in report()["cases"].items():
            for mode, x in cases.items():
                with self.subTest(host=host, mode=mode):
                    l, t, w, h = x["roi_xywh"]
                    W, H = x["host"]
                    self.assertTrue(0 <= l and 0 <= t and l + w <= W and t + h <= H)
                    self.assertLessEqual(abs(x["pixel_margin_lr"][0] - x["pixel_margin_lr"][1]), 1)
                    self.assertLessEqual(abs(x["pixel_margin_tb"][0] - x["pixel_margin_tb"][1]), 1)
                    self.assertLess(F(x["max_aspect_error"]), F(1, 60))
                    self.assertEqual(x["full_source_interval"][3], 224)

    def test_wrong_square_pixel_policy_changes_roi(self):
        x = raster_roi(256, 224, 3840, 2160)
        wrong = raster_roi(256, 224, 3840, 2160, F(1))
        self.assertNotEqual(x["roi_xywh"], wrong["roi_xywh"])
        self.assertEqual(wrong["roi_xywh"], [685, 0, 2469, 2160])

    def test_cli_json_explicitly_withholds_credit(self):
        import json
        script = Path(__file__).resolve().parents[2] / "tools" / "qa06_raster_roi_reference.py"
        data = json.loads(subprocess.check_output([sys.executable, str(script)], text=True))
        self.assertFalse(data["render_observed"])
        self.assertEqual(data["release_gate_credit"], 0)


if __name__ == "__main__":
    unittest.main()

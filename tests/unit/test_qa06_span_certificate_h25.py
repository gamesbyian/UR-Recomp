"""H25 first-party synthetic QA06 span/coverage contract on current raster ROI.

Source geometry only: no GPU readback, original/native parity or art signoff.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa06_span_certificate as span


class NearestNeighbourSpanCertificateTests(unittest.TestCase):
    def test_original_640_by_480_has_7_to_6_matte_and_full_source(self):
        r = span.certify("original", 640, 480)
        self.assertEqual(r["source"], [256, 224])
        self.assertEqual(r["roi_xywh"], [80, 60, 480, 360])
        self.assertEqual(r["left_right_mattes"], [80, 80])
        self.assertEqual(r["top_bottom_mattes"], [60, 60])
        self.assertTrue(r["full_source_coverage"])
        self.assertTrue(r["all_224_rows_present"])

    def test_world342_source_is_real_wide_and_not_4_to_3_stretch(self):
        r = span.certify("world342", 1280, 720)
        self.assertEqual(r["source"], [342, 224])
        self.assertEqual(r["roi_xywh"], [0, 0, 1280, 720])
        self.assertEqual(r["source_columns_observed"], 342)
        self.assertTrue(r["full_source_coverage"])

    def test_4k_geometry_is_measured_without_awarding_gpu_acceptance(self):
        original = span.certify("original", 3840, 2160)
        world = span.certify("world342", 3840, 2160)
        self.assertEqual(original["roi_xywh"], [480, 0, 2880, 2160])
        self.assertEqual(world["roi_xywh"], [0, 0, 3840, 2160])
        for item in (original, world):
            self.assertTrue(item["full_source_coverage"])
            self.assertFalse(item["physical_gpu_accepted"])
            self.assertFalse(item["character_art_approved"])
            self.assertEqual(item["release_gate_credit"], 0)

    def test_small_surfaces_report_missing_source_coverage(self):
        for mode in ("original", "world342"):
            with self.subTest(mode=mode):
                r = span.certify(mode, 63, 63)
                self.assertFalse(r["full_source_coverage"])
                self.assertFalse(r["all_224_rows_present"])
                self.assertEqual(r["release_gate_credit"], 0)

    def test_invalid_dimensions_and_modes_fail_closed(self):
        for mode, width, height in (
            ("invented", 640, 480),
            ("original", True, 480),
            ("original", 0, 480),
            ("original", 640, 16385),
            ("world342", 640, 0),
        ):
            with self.subTest(mode=mode, width=width, height=height):
                with self.assertRaises(ValueError):
                    span.certify(mode, width, height)

    def test_broken_source_to_host_interval_is_rejected(self):
        original = span.source_pixel_host_span

        def broken(source_pixels, host_pixels, index):
            lo, hi = original(source_pixels, host_pixels, index)
            if index == 0:
                return lo + 1, hi
            return lo, hi

        with patch.object(span, "source_pixel_host_span", side_effect=broken):
            with self.assertRaisesRegex(ValueError, "gaps or overlap"):
                span.certify("original", 640, 480)


if __name__ == "__main__":
    unittest.main()

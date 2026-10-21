"""ROM-free controls for observed Modern menu versus gameplay ROI policy."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from qa06_modern_menu_surface_reference import (
    modern_menu_surface_reference, menu_source_pixel_at_host)


class ModernMenuReference(unittest.TestCase):
    def test_actual_compact_menu_fills_entire_4x3_drawable(self):
        r = modern_menu_surface_reference(1024, 768)
        self.assertEqual(r['roi_xywh'], [0, 0, 1024, 768])
        self.assertEqual((r['source_host_samples'], r['matte_samples']), (786432, 0))
        self.assertNotEqual(r['roi_xywh'], [128, 96, 768, 576])  # 16:9 gameplay resolver
        self.assertEqual(r['release_gate_credit'], 0)

    def test_actual_wide_menu_has_expected_side_mattes(self):
        r = modern_menu_surface_reference(1280, 720)
        self.assertEqual(r['roi_xywh'], [160, 0, 960, 720])
        self.assertEqual(r['matte_samples'], 230400)
        self.assertEqual(r['source_pixels'], 57344)
        self.assertEqual(r['roi_xywh'], [160, 0, 960, 720])  # 16:9 gameplay resolver
        self.assertFalse(r['independent_source_raster_parity'])

    def test_menu_source_pixel_centre_coverage(self):
        for w, h in ((1024, 768), (1280, 720)):
            got_x = {menu_source_pixel_at_host(w, h, x, h//2)[0]
                     for x in range(w) if menu_source_pixel_at_host(w, h, x, h//2) is not None}
            got_y = {menu_source_pixel_at_host(w, h, w//2, y)[1] for y in range(h)}
            self.assertEqual(got_x, set(range(256)))
            self.assertEqual(got_y, set(range(224)))

    def test_wide_mattes_are_not_source_pixels(self):
        self.assertIsNone(menu_source_pixel_at_host(1280, 720, 159, 360))
        self.assertIsNone(menu_source_pixel_at_host(1280, 720, 1120, 360))
        self.assertEqual(menu_source_pixel_at_host(1280, 720, 160, 0), (0, 0))
        self.assertEqual(menu_source_pixel_at_host(1280, 720, 1119, 719), (255, 223))

    def test_unknown_host_sizes_and_boolean_forgery_are_refused(self):
        for w, h in ((1920, 1080), (720, 1280), (0, 0), (True, 768), (1024, False)):
            with self.subTest(host=(w, h)), self.assertRaises(ValueError):
                modern_menu_surface_reference(w, h)
        with self.assertRaises(ValueError):
            menu_source_pixel_at_host(1024, 768, 1024, 0)
        with self.assertRaises(ValueError):
            menu_source_pixel_at_host(1024, 768, False, 0)


if __name__ == '__main__':
    unittest.main()

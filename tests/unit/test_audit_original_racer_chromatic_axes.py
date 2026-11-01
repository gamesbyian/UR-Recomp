"""ROM-free original racer source-chromatic-axis checks."""
import importlib.util
from pathlib import Path
import math
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/audit_original_racer_chromatic_axes.py"
spec = importlib.util.spec_from_file_location("chromatic_axis", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def frame(player="p1", slope=1):
    pix = bytearray(64 * 64 * 4)
    color = (210, 28, 30, 255) if player == "p1" else (28, 35, 210, 255)
    for y in range(5, 22):
        x = 23 + round(slope * (y - 5))
        pix[4*(y*64+x):4*(y*64+x)+4] = bytes(color)
    return bytes(pix)


class SourceChromaticAxisTests(unittest.TestCase):
    def test_source_red_and_blue_have_clear_projected_axes(self):
        for player in ("p1", "p2"):
            alpha, chroma, xy = mod.pixel_masks(frame(player), player)
            self.assertEqual(sum(alpha), 17)
            self.assertEqual(sum(chroma), 17)
            self.assertEqual(len(xy), 17)
            axis = mod.principal_axis(xy)
            self.assertAlmostEqual(axis["screen_axis_angle_from_down_y_degrees"],
                                   45.0, delta=0.5)
            self.assertGreater(axis["source_chroma_pca_major_variance_fraction"], .99)

    def test_negative_screen_axis_slope_and_pixel_neutrality(self):
        alpha, chroma, points = mod.pixel_masks(frame("p1", -1), "p1")
        self.assertEqual(sum(chroma), 17)
        self.assertAlmostEqual(
            mod.principal_axis(points)["screen_axis_angle_from_down_y_degrees"],
            -45.0, delta=.5)
        pix = bytearray(frame("p1"))
        pix[4*(12*64+15):4*(12*64+15)+4] = bytes((125, 125, 125, 255))
        _, modified, _ = mod.pixel_masks(bytes(pix), "p1")
        self.assertEqual(sum(modified), 17)

    def test_wrong_palette_and_nonbinary_alpha_refused(self):
        pix = bytearray(frame("p2"))
        with self.assertRaisesRegex(ValueError, "enough authentic"):
            mod.pixel_masks(bytes(pix), "p1")
        pix[3] = 127
        with self.assertRaisesRegex(ValueError, "nonbinary"):
            mod.pixel_masks(bytes(pix), "p2")
        with self.assertRaisesRegex(ValueError, "64x64"):
            mod.pixel_masks(b"", "p1")
        with self.assertRaises(ValueError):
            mod.pixel_masks(frame("p1"), "wrong")

    def test_no_fake_axis_from_degenerate_or_tampered_coordinates(self):
        for points in ([(1,1),(1,1),(1,1)],[(1,1),(float("inf"),2),(3,3)],[(1,1)]):
            with self.subTest(points=points), self.assertRaises(ValueError):
                mod.principal_axis(points)

    def test_same_external_source_envelope_independent_of_internal_holes(self):
        a = bytearray(4096)
        b = bytearray(4096)
        for y in range(10, 20):
            for x in (20, 21, 27, 28):
                a[y*64+x] = 1
            for x in (20, 22, 26, 28):
                b[y*64+x] = 1
        self.assertNotEqual(bytes(a), bytes(b))
        self.assertEqual(mod.row_envelope_sha(bytes(a)),
                         mod.row_envelope_sha(bytes(b)))
        with self.assertRaises(ValueError):
            mod.row_envelope_sha(b"bad")

    def test_original_rom_and_report_claims_are_fixed(self):
        self.assertEqual(mod.CANONICAL_ROM_SHA,
                         "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478")
        self.assertIn("CHROMATIC", mod.SCHEMA)


if __name__ == "__main__":
    unittest.main()

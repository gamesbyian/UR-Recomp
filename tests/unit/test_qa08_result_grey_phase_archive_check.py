"""Fail-closed source colour-order, scene periodicity, and ZIP provenance tests."""
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_result_grey_phase_archive_check as c


class GreyPhase(unittest.TestCase):
    def test_slots_exact(self):
        self.assertEqual(len(c.RESULTS), 91)
        self.assertEqual(sorted(c.PEAKS), list(range(4064, 5409, 112)))
        self.assertIn(4016, c.FIELDS)

    def test_original_BGRX_native_RGBA_and_future_probe(self):
        original = bytearray(c.PIXELS * 4)
        native = bytearray(c.PIXELS * 4)
        future = bytearray(c.PIXELS * 4)
        for i in range(3):
            original[i], native[i], future[i] = 160, 136, 136
        self.assertEqual(c.frame_large_counts(original, native, future), (1, 1, 1))
        for i in range(3):
            native[i] = 152
        self.assertEqual(c.frame_large_counts(original, native, future), (1, 0, 0))
        original[:3] = bytes((0, 8, 24))
        native[:3] = bytes((24, 8, 0))
        self.assertEqual(c.frame_large_counts(original, native), (0, 0, 0))

    def test_split_exact_rgb5_grey_phase_and_fixed_chromatic_coordinates(self):
        original = bytearray(c.PIXELS * 4)
        native = bytearray(c.PIXELS * 4)
        # BGRX original RGB5 20, Win32 RGBA RGB5 17. A real palette
        # phase mismatch, not a one-unit rounding difference.
        original[0:3] = bytes((160, 160, 160))
        native[0:3] = bytes((136, 136, 136))
        # Chromatic source pixel at logical (3,2) must preserve its exact
        # spatial index; do not hide moving OAM/OBJ regions with a palette.
        k = 4 * (2 * 256 + 3)
        original[k:k+3] = bytes((104, 208, 224))
        native[k:k+3] = bytes((224, 192, 72))
        palette, positions = c.result_large_colour_components(original, native)
        self.assertEqual(palette, {(17, 20): 1})
        self.assertEqual(positions, (2 * 256 + 3,))
        # A one-step discrepancy is not an extra large-error source.
        native[0:3] = bytes((152, 152, 152))
        palette, positions = c.result_large_colour_components(original, native)
        self.assertEqual(palette, {})
        self.assertEqual(positions, (2 * 256 + 3,))
        with self.assertRaisesRegex(ValueError, "cropped"):
            c.result_large_colour_components(original[:-4], native)

    def test_cross_epoch_medal_mask_provenance_fails_closed_on_unpinned_archive(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "three-source.zip"
            source.write_bytes(b"not an authenticated archive")
            with self.assertRaisesRegex(ValueError, "ZIP identity drift"):
                c.inspect_three_source_epoch_medal_mask(source, {}, {})
        self.assertEqual(c.MEDAL_ROW_BANDS, ((91, 105), (115, 129), (139, 153)))
        self.assertEqual(c.SAMPLED_OVERLAP_POINTS,
                         ((225, 96), (225, 120), (205, 115)))
        self.assertEqual(len(range(4032, 5185, 48)), 25)

    def test_reject_tampered_outer_archive_even_before_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            o, n = Path(d) / "original.zip", Path(d) / "native.zip"
            o.write_bytes(b"bad source")
            n.write_bytes(b"bad native")
            with self.assertRaisesRegex(ValueError, "source-epoch archive SHA"):
                c.loaded(o, n)


if __name__ == "__main__":
    unittest.main()

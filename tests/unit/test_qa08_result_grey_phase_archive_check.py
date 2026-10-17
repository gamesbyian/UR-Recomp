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

    def test_reject_tampered_outer_archive_even_before_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            o, n = Path(d) / "original.zip", Path(d) / "native.zip"
            o.write_bytes(b"bad source")
            n.write_bytes(b"bad native")
            with self.assertRaisesRegex(ValueError, "source-epoch archive SHA"):
                c.loaded(o, n)


if __name__ == "__main__":
    unittest.main()

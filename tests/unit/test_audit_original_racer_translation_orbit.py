"""ROM-free real-byte controls for source-mask retrospective shape alignment."""
import unittest
from tools.art.audit_original_racer_translation_orbit import analyze_pair, translate


def mask(*points):
    data = bytearray(4096)
    for x, y in points:
        data[64*y+x] = 1
    return bytes(data)


class TranslationOrbitTests(unittest.TestCase):
    def test_exact_shift(self):
        a = mask((21,22), (22,22), (21,23), (23,23))
        r = analyze_pair(a, translate(a, 2, -1))
        self.assertEqual(r["optimal_integer_shift_dx_dy"], [2,-1])
        self.assertEqual(r["optimal_residual_shape_pixels"], 0)
        self.assertEqual(r["original_changed_pixels"], 8)
        self.assertEqual(r["equally_optimal_shift_count"], 1)
        self.assertFalse(r["real_original_emulator_frame_timing_observed"])

    def test_shift_cannot_hide_new_shape(self):
        a = mask((19,20), (20,20), (20,21), (21,20))
        b = bytearray(translate(a, 1, 0))
        b[30*64+30] = 1
        r = analyze_pair(a, bytes(b))
        self.assertEqual(r["optimal_integer_shift_dx_dy"], [1,0])
        self.assertEqual(r["optimal_residual_shape_pixels"], 1)

    def test_unchanged_source_not_forced_to_move(self):
        a = mask((20,20), (23,20), (21,21))
        r = analyze_pair(a,a)
        self.assertEqual(r["optimal_integer_shift_dx_dy"], [0,0])
        self.assertEqual(r["original_changed_pixels"], 0)
        self.assertEqual(r["optimal_residual_shape_pixels"], 0)
        self.assertIsNone(r["posthoc_translation_change_recall"])

    def test_tied_oracle_discloses_ambiguity(self):
        r = analyze_pair(mask((20,20)), mask((35,35)))
        self.assertEqual(r["optimal_integer_shift_dx_dy"], [0,0])
        self.assertGreater(r["equally_optimal_shift_count"], 1)
        self.assertEqual(r["optimal_residual_shape_pixels"], 2)

    def test_disallow_clipping(self):
        a = mask((0,0),(22,22))
        self.assertIsNone(translate(a,-1,0))
        self.assertIsNone(translate(a,0,-1))
        self.assertIsNotNone(translate(a,0,0))
        self.assertEqual(analyze_pair(a,mask((0,0),(23,22)),1)
                         ["optimal_residual_shape_pixels"],2)

    def test_invalid_alpha_or_budgets(self):
        a = mask((20,20))
        for bad in (bytes(4096), bytes([2])+bytes(4095), b"x"):
            with self.subTest(bad=bad[:2]), self.assertRaises(ValueError):
                analyze_pair(a,bad)
        for radius in (-1,9,True,1.2):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                analyze_pair(a,a,radius)
        with self.assertRaises(ValueError):
            translate(a,True,0)


if __name__ == "__main__":
    unittest.main()

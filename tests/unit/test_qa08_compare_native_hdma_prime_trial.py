"""Adversarial full original-size P7 native counterfactual comparison."""
import unittest

from tools.qa08_compare_native_hdma_prime_trial import assess, HEADER, W, H


def image(*, dark_rows=(), changed_other=None):
    result = bytearray()
    for y in range(H):
        for x in range(W):
            rgb = (0, 0, 0) if y in dark_rows else (82, 90, 107)
            if changed_other == (x, y):
                rgb = (57, 11, 22)
            result.extend((*rgb, 255))
    return HEADER + bytes(result)


CRC = b"".join(f"{n:04d}: {n:08x}\n".encode() for n in range(2473))


class NativeHdmaPrimeRenderedPixelsTests(unittest.TestCase):
    def test_exact_two_row_relocation_would_be_supported_only_by_real_raster(self):
        baseline = image(dark_rows=(112, 113))
        corrected = image(dark_rows=(111, 112))
        result = assess(baseline, corrected, CRC, CRC,
                        enforce_accepted_baseline=False)
        self.assertEqual(result["changed_256wide_RGBA_pixels"], 512)
        self.assertEqual(result["changed_output_rows"],
                         [{"y": 111, "count": 256}, {"y": 113, "count": 256}])
        self.assertEqual(result["baseline_all_black_rows_110_to_114"], [112, 113])
        self.assertEqual(result["experiment_all_black_rows_110_to_114"], [111, 112])
        self.assertTrue(result["counterfactual_raster_matches_expected_original_split_band_placement"])
        self.assertFalse(result["original_Snes9x_RGB5_exact_equality_proven_by_this_pair"])
        self.assertFalse(result["physical_SNES_hardware_or_shipping_correction_approved"])

    def test_an_unrelated_changed_pixel_falsifies_even_with_correct_seam(self):
        baseline = image(dark_rows=(112, 113))
        altered = image(dark_rows=(111, 112), changed_other=(4, 180))
        r = assess(baseline, altered, CRC, CRC, enforce_accepted_baseline=False)
        self.assertEqual(r["changed_256wide_RGBA_pixels"], 513)
        self.assertFalse(r["counterfactual_raster_matches_expected_original_split_band_placement"])
        self.assertTrue(r["non_seam_native_RGBA_changes_observed"])

    def test_failed_to_move_real_dark_seam_is_valid_negative_evidence(self):
        baseline = image(dark_rows=(112, 113))
        r = assess(baseline, baseline, CRC, CRC,
                   enforce_accepted_baseline=False)
        self.assertEqual(r["classification"], "source_native_hypothesis_not_supported")
        self.assertEqual(r["changed_output_rows"], [])

    def test_reject_malformed_p7_alpha_and_edited_baseline(self):
        baseline = image(dark_rows=(112, 113))
        trial = image(dark_rows=(111, 112))
        with self.assertRaisesRegex(ValueError, "baseline unmodified"):
            assess(baseline, trial, CRC, CRC)
        for bad in (baseline[:-4], b"PNG" + baseline[3:],
                    b"P7\n" + baseline):
            with self.subTest(size=len(bad)):
                with self.assertRaisesRegex(ValueError, "256x224"):
                    assess(bad, trial, CRC, CRC, enforce_accepted_baseline=False)
        with self.assertRaisesRegex(ValueError, "CRC"):
            assess(baseline, trial, CRC, CRC[:-1],
                   enforce_accepted_baseline=False)
        with self.assertRaisesRegex(ValueError, "CRC"):
            assess(baseline, trial, b"x\n" * 2473, b"x\n" * 2473,
                   enforce_accepted_baseline=False)


if __name__ == "__main__":
    unittest.main()

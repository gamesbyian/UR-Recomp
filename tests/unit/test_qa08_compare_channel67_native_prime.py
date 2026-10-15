"""Adversarial full native/original four-scene ch6+7 raster counterfactual."""
import unittest

from tools.qa08_compare_channel67_native_prime import assess, KINDS, FRAMES
from tools.qa08_compare_channel7_native_prime import HEADER
from tools.qa08_accept_original_native_split_seam import W, H

PIX = bytes(W * H * 4)
CRC = b"0x00000000\n" * 2473


def fixtures():
    original = {fr: PIX for fr in FRAMES}
    native = {kind: {fr: HEADER + PIX for fr in FRAMES} for kind in KINDS}
    crc = {kind: CRC for kind in KINDS}
    return original, native, crc


class Channel67SourceComparisonTests(unittest.TestCase):
    def test_synthetic_exact_images_do_not_authorize_shipping(self):
        o, n, c = fixtures()
        res = assess(o, n, c, enforce_accepted_global=False)
        self.assertTrue(res["four_scenes_original_RGB5_exact_for_channel67"])
        self.assertFalse(res["production_HDMA_source_change_authorized"])
        self.assertEqual(len(res["original_source_observations"]), 4)

    def test_countdown_wrong_one_pixel_is_a_valid_reported_negative(self):
        o, n, c = fixtures()
        changed = bytearray(PIX)
        changed[4 * (98 * W + 40)] = 8
        n["channel67"][1856] = HEADER + changed
        res = assess(o, n, c, enforce_accepted_global=False)
        self.assertFalse(res["four_scenes_original_RGB5_exact_for_channel67"])
        self.assertEqual(res["status"], "experimental_ch67_genuine_original_source_negative")
        self.assertEqual(res["original_source_observations"][0][
            "candidate_ch67_differing_rows"], [{"row":98, "different":1}])

    def test_missing_real_pixels_or_changed_guest_refuses_acceptance(self):
        o, n, c = fixtures()
        del n["channel67"][2224]
        with self.assertRaisesRegex(ValueError, "five native"):
            assess(o, n, c, enforce_accepted_global=False)
        o, n, c = fixtures()
        c["channel67"] += b"0xABCD0000\n"
        with self.assertRaisesRegex(ValueError, "CRC"):
            assess(o, n, c, enforce_accepted_global=False)

    def test_prior_global_reference_drift_fails_even_if_candidate_matches(self):
        o, n, c = fixtures()
        shifted = bytearray(PIX)
        shifted[0] = 8
        n["global"][2208] = HEADER + shifted
        with self.assertRaisesRegex(ValueError, "global-prime pixel control"):
            assess(o, n, c, enforce_accepted_global=False)

    def test_production_source_requires_hash_qualified_global_reference(self):
        o, n, c = fixtures()
        with self.assertRaisesRegex(ValueError, "global-prime P7 changed"):
            assess(o, n, c)


if __name__ == "__main__":
    unittest.main()

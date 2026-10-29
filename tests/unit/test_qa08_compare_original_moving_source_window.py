"""ROM-free negative controls for genuine 37-frame native/original 2P pixel comparison."""
import unittest
from unittest import mock

from tools import qa08_compare_original_moving_source_window as cmp
from tools.qa08_compare_original_moving_source_window import (
    compare, check_crc, NATIVE_FRAMES, KINDS, WINDOW,
)
from tools.qa08_compare_channel7_native_prime import HEADER
from tools.qa08_accept_original_native_split_seam import W, H

PIXELS = W * H
CRC = b"0x00000000\n" * 2473
BLACK = bytes(PIXELS * 4)


def fixtures():
    original = {f: BLACK for f in WINDOW}
    native = {
        kind: {frame: HEADER + BLACK for frame in NATIVE_FRAMES}
        for kind in KINDS
    }
    return original, native, {k: CRC for k in KINDS}


class OriginalMovingSourceWindowTests(unittest.TestCase):
    def test_exact_synthetic_source_never_certifies_guest_phase_or_shipping(self):
        o, n, c = fixtures()
        report = compare(o, n, c, strict_original=False)
        self.assertEqual(len(report["new_actual_native_original_results"]), 2)
        self.assertFalse(report["source_CPU_OAM_camera_phase_equivalence_for_extra_frames_proven"])
        self.assertFalse(report["native_production_renderer_fix_authorized"])
        self.assertEqual(report["new_actual_native_original_results"][0][
            "four_real_source_dispositions"]["global"]["prespecified_wrong_RGB5_pixels"], 0)

    def test_duplicate_exact_sources_reuse_scores_without_weakening_controls(self):
        o, n, c = fixtures()
        # All synthetic callback/native frames are byte-identical. One exact
        # byte-pair suffices even when it occurs in the authentic control,
        # all 37 callbacks, four kinds and both candidate frames.
        matcher = cmp.rgb5_match
        with mock.patch.object(cmp, "rgb5_match", wraps=matcher) as actual:
            report = compare(o, n, c, strict_original=False)
        self.assertEqual(actual.call_count, 1)
        for item in report["new_actual_native_original_results"]:
            for disposition in item["four_real_source_dispositions"].values():
                self.assertEqual(disposition["prespecified_wrong_RGB5_pixels"], 0)
                self.assertTrue(disposition["prespecified_pair_has_pixel_parity"])

        # One changed exact frame must not inherit the cached score from a
        # previous input; even this single RGB5 pixel mismatch stays visible.
        o, n, c = fixtures()
        changed = bytearray(BLACK)
        changed[4 * (130 * W + 27)] = 8
        n["channel7"][2224] = HEADER + bytes(changed)
        with mock.patch.object(cmp, "rgb5_match", wraps=matcher) as actual:
            report = compare(o, n, c, strict_original=False)
        self.assertEqual(actual.call_count, 2)
        channel7 = report["new_actual_native_original_results"][1][
            "four_real_source_dispositions"]["channel7"]
        self.assertEqual(channel7["prespecified_wrong_RGB5_pixels"], 1)
        self.assertFalse(channel7["prespecified_pair_has_pixel_parity"])

    def test_native_pixel_mismatch_is_reported_not_masked(self):
        o, n, c = fixtures()
        changed = bytearray(BLACK)
        changed[4 * (130 * W + 27)] = 8
        n["channel7"][2224] = HEADER + bytes(changed)
        result = compare(o, n, c, strict_original=False)
        entry = result["new_actual_native_original_results"][1][
            "four_real_source_dispositions"]["channel7"]
        self.assertEqual(entry["prespecified_wrong_RGB5_pixels"], 1)
        self.assertFalse(entry["prespecified_pair_has_pixel_parity"])

    def test_missing_original_or_native_source_is_invalid(self):
        o, n, c = fixtures()
        del o[2191]
        with self.assertRaisesRegex(ValueError, "every original"):
            compare(o, n, c, strict_original=False)
        o, n, c = fixtures()
        del n["channel57"][2192]
        with self.assertRaisesRegex(ValueError, "three actual"):
            compare(o, n, c, strict_original=False)

    def test_source_archive_or_guest_crc_mutation_fails(self):
        o, n, c = fixtures()
        c["global"] = c["global"][:-11] + b"0x00000001\n"
        with self.assertRaisesRegex(ValueError, "disagree"):
            compare(o, n, c, strict_original=False)
        o, n, c = fixtures()
        n["global"][2208] = HEADER + (bytes([8]) + BLACK[1:])
        with self.assertRaisesRegex(ValueError, "postGO"):
            compare(o, n, c, strict_original=False)

    def test_crc_shape_not_just_equal_length(self):
        o, n, c = fixtures()
        c = {k: b"invalid\n" * 2473 for k in KINDS}
        with self.assertRaisesRegex(ValueError, "malformed"):
            check_crc(c)


if __name__ == "__main__":
    unittest.main()

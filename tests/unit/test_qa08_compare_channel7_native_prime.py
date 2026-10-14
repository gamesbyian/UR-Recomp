"""ROM-free falsification of the channel-7-only original/native source comparison."""
import unittest

from tools.qa08_compare_channel7_native_prime import (
    W, H, HEADER, compare, pixels_changed,
)

COUNT = W * H
CRC = b"0x00000000\n" * 2473


def p7(pixels: bytes) -> bytes:
    return HEADER + pixels


def black() -> bytes:
    return bytes(COUNT * 4)


def fixtures():
    same = black()
    native = {name: {frame: p7(same) for frame in (400, 1856, 2208)}
              for name in ("stock", "global", "channel7")}
    originals = {1856: same, 2208: same}
    crcs = {k: CRC for k in native}
    return native, originals, crcs


class Channel7SourceComparisonTests(unittest.TestCase):
    def test_all_true_exact_is_bounded_not_shipping_approval(self):
        n, o, c = fixtures()
        result = compare(n, o, c, strict_reference=False)
        self.assertEqual(result["status"], "experimental_channel7_three_scene_source_consistent")
        self.assertFalse(result["shipping_renderer_change_authorized"])
        self.assertFalse(result["line112_OAM_priority_and_final_sprite_ownership_proven"])

    def test_channel7_race_pixel_change_is_reported_negative(self):
        n, o, c = fixtures()
        changed = bytearray(black())
        changed[4 * (120 * W + 12)] = 8
        n["channel7"][2208] = p7(bytes(changed))
        result = compare(n, o, c, strict_reference=False)
        self.assertEqual(result["status"], "experimental_channel7_source_divergence_observed")
        scene = result["actual_source_dispositions"][-1]
        self.assertEqual(scene["global_to_channel7"]["changed_rows"], [{"y": 120, "count": 1}])
        self.assertEqual(scene["all_57344_RGB5_pixel_original_comparisons"]["channel7"]["different_pixels"], 1)

    def test_frontend_change_cannot_count_as_three_scene_consistency(self):
        n, o, c = fixtures()
        changed = bytearray(black())
        changed[3] = 255
        n["channel7"][400] = p7(bytes(changed))
        result = compare(n, o, c, strict_reference=False)
        self.assertFalse(result["frontend_unchanged_from_stock"])
        self.assertFalse(result["source_alpha_preserved_vs_stock"])

    def test_crc_mutation_fails_closed(self):
        n, o, c = fixtures()
        c["channel7"] = c["channel7"][:-11] + b"0x00000001\n"
        with self.assertRaisesRegex(ValueError, "CRC"):
            compare(n, o, c, strict_reference=False)

    def test_missing_real_frame_fails_closed(self):
        n, o, c = fixtures()
        del n["stock"][1856]
        with self.assertRaisesRegex(ValueError, "three actual frames"):
            compare(n, o, c, strict_reference=False)

    def test_reference_global_regression_is_invalid_control(self):
        n, o, c = fixtures()
        altered = bytearray(black())
        altered[0] = 8
        n["global"][1856] = p7(bytes(altered))
        with self.assertRaisesRegex(ValueError, "control regressed"):
            compare(n, o, c, strict_reference=False)

    def test_false_dimensions_and_archive_shape_reject(self):
        n, o, c = fixtures()
        n["channel7"][2208] = n["channel7"][2208][:-4]
        with self.assertRaisesRegex(ValueError, "source"):
            compare(n, o, c, strict_reference=False)
        with self.assertRaisesRegex(ValueError, "complete"):
            pixels_changed(bytes(4), bytes(4))


if __name__ == "__main__":
    unittest.main()

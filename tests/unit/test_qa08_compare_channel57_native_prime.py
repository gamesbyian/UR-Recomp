"""Fail-closed four-process combined ch5+7 real original-source comparator."""
import unittest

from tools.qa08_compare_channel57_native_prime import compare
from tests.unit.test_qa08_compare_channel7_native_prime import fixtures, p7, black, CRC, W


def fixture4():
    n, o, c = fixtures()
    n["channel57"] = dict(n["global"])
    c["channel57"] = CRC
    return n, o, c


class CombinedChannel57OriginalSourceTests(unittest.TestCase):
    def test_exact_source_still_refuses_shipping_authority(self):
        n, o, c = fixture4()
        result = compare(n, o, c, strict_reference=False)
        self.assertTrue(result["both_original_2P_scenes_exact_RGB5"])
        self.assertFalse(result["shipping_production_HDMA_correction_authorized"])
        self.assertFalse(result["executed_CPU_65816_HDMA_channels_fully_caused"])

    def test_fourth_persistent_colour_failure_is_scientific_negative(self):
        n, o, c = fixture4()
        pixels = bytearray(black())
        pixels[4 * (55 * W + 20)] = 8
        n["channel57"][1856] = p7(bytes(pixels))
        result = compare(n, o, c, strict_reference=False)
        self.assertFalse(result["both_original_2P_scenes_exact_RGB5"])
        self.assertEqual(result["status"], "experimental_ch57_real_source_divergence_observed")
        scene = result["authentic_source_scene_dispositions"][1]
        self.assertEqual(scene["original_Snes9x_RGB5_wrong_pixels"], 1)
        self.assertEqual(scene["original_Snes9x_mismatching_rows"], [{"row": 55, "different": 1}])

    def test_wrong_guest_or_missing_source_fails_closed(self):
        n, o, c = fixture4()
        c["channel57"] = c["channel57"][:-11] + b"0xFFFFFFFF\n"
        with self.assertRaisesRegex(ValueError, "CRC"):
            compare(n, o, c, strict_reference=False)
        n, o, c = fixture4()
        del n["channel57"][2208]
        with self.assertRaisesRegex(ValueError, "three real"):
            compare(n, o, c, strict_reference=False)

    def test_alpha_change_not_hidden_in_rgb_comparison(self):
        n, o, c = fixture4()
        p = bytearray(black())
        p[3] = 255
        n["channel57"][400] = p7(bytes(p))
        result = compare(n, o, c, strict_reference=False)
        self.assertFalse(result["all_observed_source_alpha_unchanged_from_global"])
        self.assertEqual(result["status"], "experimental_ch57_real_source_divergence_observed")


if __name__ == "__main__":
    unittest.main()

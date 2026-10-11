"""Adversarial genuine-native Original 2P post-GO front/text causal deltas."""
from __future__ import annotations
import unittest
from tools.check_baldosa_2p_postgo_front_text_causality import (
    analyze, WIDTH, HEIGHT,
)


class Original2PPostGoFrontRemovalTest(unittest.TestCase):
    def setUp(self):
        self.stock = bytearray(bytes((12, 20, 30, 0)) * WIDTH * HEIGHT)
        self.removed = bytearray(self.stock)
        self.front = bytearray(WIDTH * HEIGHT * 4)
        self.rear = bytearray(WIDTH * HEIGHT * 4)
        self.positions = {
            "front_only": (100, 50),
            "overlap_different": (101, 50),
            "overlap_same": (102, 50),
            "red_text_changed": (132, 47),
            "red_text_unchanged": (133, 47),
            "outside": (140, 55),
        }
        self.paint("front", "front_only", (30, 30, 30, 255))
        self.paint("stock", "front_only", (30, 30, 30, 0))
        self.paint("front", "overlap_different", (200, 100, 40, 255))
        self.paint("rear", "overlap_different", (20, 100, 40, 255))
        self.paint("stock", "overlap_different", (200, 100, 40, 0))
        self.paint("removed", "overlap_different", (20, 100, 40, 0))
        self.paint("front", "overlap_same", (49, 49, 49, 255))
        self.paint("rear", "overlap_same", (49, 49, 49, 255))
        self.paint("stock", "overlap_same", (49, 49, 49, 0))
        self.paint("removed", "overlap_same", (49, 49, 49, 0))
        for key in ("red_text_changed", "red_text_unchanged"):
            self.paint("front", key, (49, 49, 49, 255))
            self.paint("stock", key, (156, 49, 49, 0))
            self.paint("removed", key, (156, 49, 49, 0))
        self.paint("removed", "red_text_changed", (107, 0, 0, 0))

    def paint(self, which, name, rgba):
        x, y = self.positions[name]
        at = 4 * (y * WIDTH + x)
        getattr(self, which)[at:at + 4] = bytes(rgba)

    def measure(self):
        return analyze(self.stock, self.front, self.rear, self.removed)

    def test_observe_real_source_front_without_foreground_layer_claim(self):
        out = self.measure()
        c = out["counts"]
        self.assertEqual(c["front_emitted"], 5)
        self.assertEqual(c["rear_emitted"], 2)
        self.assertEqual(c["front_only"], 3)
        self.assertEqual(c["shared_different_source_rgb"], 1)
        self.assertEqual(c["shared_same_source_rgb"], 1)
        self.assertEqual(c["stock_rgb_different_front_on_emission"], 2)
        self.assertEqual(c["stock_exact_red_plus_107_over_front"], 2)
        self.assertEqual(c["native_final_changed_within_front_source"], 3)
        self.assertEqual(c["native_final_changed_at_red_text_source_positions"], 1)
        self.assertEqual(c["native_final_unchanged_at_red_text_source_positions"], 1)
        self.assertEqual(c["native_front_removal_reveals_rear_rgb_on_overlap"], 2)
        self.assertTrue(out["all_native_final_changed_pixels_within_front_alpha"])
        self.assertFalse(out["exact_BG_window_OBJ_text_colour_math_owner_known"])
        self.assertFalse(out["normal_renderer_may_delete_original_front_sprite"])

    def test_native_outside_original_front_source_delta_is_never_accepted(self):
        self.paint("removed", "outside", (33, 22, 11, 0))
        result = self.measure()
        self.assertEqual(result["counts"]["native_final_changed_outside_front_source"], 1)
        self.assertEqual(result["bounded_invalid_outside_source_delta_xy"],
                         [[140, 55]])
        self.assertFalse(result["all_native_final_changed_pixels_within_front_alpha"])

    def test_colour_effect_on_source_can_be_fully_foreground_masked(self):
        self.paint("removed", "red_text_changed", (156, 49, 49, 0))
        c = self.measure()["counts"]
        self.assertEqual(c["native_final_changed_at_red_text_source_positions"], 0)
        self.assertEqual(c["native_final_unchanged_at_red_text_source_positions"], 2)

    def test_changing_one_red_text_rgb_delta_does_not_forge_causal_winner(self):
        self.paint("stock", "red_text_changed", (155, 49, 49, 0))
        c = self.measure()["counts"]
        self.assertEqual(c["stock_exact_red_plus_107_over_front"], 1)
        self.assertEqual(c["stock_rgb_different_front_on_emission"], 2)

    def test_a_source_positive_pixel_matching_final_may_still_be_causally_invisible(self):
        self.paint("removed", "front_only", (30, 30, 30, 0))
        c = self.measure()["counts"]
        self.assertEqual(c["stock_rgb_equal_front_on_emission"], 3)
        self.assertEqual(c["native_final_changed_within_front_source"], 2)

    def test_bad_full_original_or_source_lengths_rejected(self):
        for idx in range(4):
            values = [self.stock, self.front, self.rear, self.removed]
            values[idx] = values[idx][:-4]
            with self.subTest(idx=idx), self.assertRaisesRegex(ValueError, "full native"):
                analyze(*values)

    def test_source_RGB_and_removed_RGBA_must_be_compared_independently(self):
        # P7 full-frame alpha remains zero even as OAM sources emit with
        # alpha=255. Do not compare source alpha to Original image alpha.
        self.paint("stock", "front_only", (30, 30, 30, 0))
        self.assertEqual(self.measure()["counts"]["stock_rgb_equal_front_on_emission"], 3)
        self.paint("removed", "front_only", (30, 30, 30, 255))
        self.assertEqual(self.measure()["counts"]["native_final_changed_within_front_source"], 3)


if __name__ == "__main__":
    unittest.main()

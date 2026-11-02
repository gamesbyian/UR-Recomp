"""ROM-free controls for source-derived 1px translation vs real shape change."""
import copy
import unittest
from tools.art.audit_original_racer_translation_only_control import (
    shift_original_mask, measure, summarize,
)


def mask(*coords):
    bits = bytearray(4096)
    for x, y in coords:
        bits[y*64+x] = 1
    return bytes(bits)


class OriginalTranslationControls(unittest.TestCase):
    def test_one_pixel_horizontal_shift_predicts_source_xor_but_no_3d_motion(self):
        before = mask((10, 10), (11, 10))
        after = mask((11, 10), (12, 10))
        row = measure(before, after, [21, 20], [23, 20])
        self.assertEqual(row["source_changed_pixels"], 2)
        self.assertEqual(row["translated_original_changed_pixels"], 2)
        self.assertEqual(row["matched_changed_pixels"], 2)
        self.assertEqual(row["actual_next_minus_shifted_previous_shape_pixels"], 0)
        self.assertTrue(row["original_next_raster_used_to_measure_translation"])
        self.assertFalse(row["physical_ground_contact_or_3d_motion_inferred"])

    def test_source_shape_change_with_fixed_anchor_is_unexplained(self):
        before, after = mask((10, 10), (11, 10)), mask((10, 10), (12, 10))
        row = measure(before, after, [21, 20], [21, 20])
        self.assertEqual(row["source_changed_pixels"], 2)
        self.assertEqual(row["matched_changed_pixels"], 0)
        self.assertEqual(row["actual_next_minus_shifted_previous_shape_pixels"], 2)
        self.assertFalse(row["source_visible_bottom_alpha_anchor_changed"])

    def test_actual_source_hold_has_no_artificial_translation(self):
        before = mask((10, 10))
        row = measure(before, before, [20, 20], [20, 20])
        self.assertFalse(row["source_raster_changed"])
        self.assertEqual(row["translated_original_changed_pixels"], 0)
        self.assertIsNone(row["change_pixel_recall"])

    def test_halfpixel_shift_refused_rather_than_quantized(self):
        with self.assertRaisesRegex(ValueError, "half-pixel"):
            shift_original_mask(mask((10, 10)), [20, 20], [21, 20])

    def test_visible_source_clip_refused(self):
        with self.assertRaisesRegex(ValueError, "clip"):
            shift_original_mask(mask((63, 10)), [126, 20], [128, 20])

    def test_invalid_masks_and_anchors_refused(self):
        for invalid in (bytes(4096), bytes(4095),
                        bytes([2]) + bytes(4095), [0]*4096):
            with self.subTest(len=len(invalid)), self.assertRaises(ValueError):
                measure(invalid, mask((10,10)), [20,20], [20,20])
        with self.assertRaises(ValueError):
            measure(mask((10,10)), mask((11,10)), [20,20], [20.0,20])

    def test_summary_preserves_source_lookahead_and_residual_census(self):
        original = [98,98,90,89,93,7,102,89,93,14,91,93,93,102,93,98,106,89,93]
        predicted = [104,104,104,104,106,0,104,104,104,0,106,104,106,104,106,104,104,104,104]
        overlap = [60,60,61,61,59,0,69,66,59,0,60,62,63,69,59,60,64,66,59]
        right = {0,6,7,8,13,15,16,17,18,}
        # Original exact moving-source delta is 10 right, 7 left, two fixed.
        # Give right list explicitly below to verify the shape census.
        right = {0,6,7,8,13,15,16,17,18,11}
        stationary = {5,9}
        rows = []
        for i in range(19):
            delta = [0,0] if i in stationary else [2,0] if i in right else [-2,0]
            rows.append({"pixels": {
                "source_changed_pixels": original[i],
                "translated_original_changed_pixels": predicted[i],
                "matched_changed_pixels": overlap[i],
                "actual_next_minus_shifted_previous_shape_pixels":
                    original[i]+predicted[i]-2*overlap[i],
                "source_raster_changed": True,
                "source_visible_anchor_delta_x2_y2": delta,
            }})
        for i in range(90):
            rows.append({"pixels": {
                "source_changed_pixels": 0,
                "translated_original_changed_pixels": 0,
                "matched_changed_pixels": 0,
                "actual_next_minus_shifted_previous_shape_pixels": 0,
                "source_raster_changed": False,
                "source_visible_anchor_delta_x2_y2": [0,0],
            }})
        self.assertEqual(sum(original), 1631)
        self.assertEqual(sum(predicted), 1776)
        self.assertEqual(sum(overlap), 1057)
        report = summarize(rows)
        self.assertEqual(report["source_translation_changed_pixel_recall"], .64806867)
        self.assertEqual(report["source_translation_changed_pixel_precision"], .59515766)
        self.assertEqual(report["next_original_shape_residual_after_shift_pixels"], 1293)
        self.assertEqual(report["source_anchor_right_one_logical_pixel_edges"], 10)
        self.assertEqual(report["source_anchor_left_one_logical_pixel_edges"], 7)
        self.assertEqual(report["source_shape_change_with_fixed_anchor_edges"], 2)
        wrong = copy.deepcopy(rows)
        wrong[0]["pixels"]["matched_changed_pixels"] += 1
        with self.assertRaises(ValueError):
            summarize(wrong)


if __name__ == "__main__":
    unittest.main()

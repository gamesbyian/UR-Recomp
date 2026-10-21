"""Original-racer source motion metrics: deterministic and explicitly non-authoritative."""
import unittest

from tools.qualify_modern_original_hero_temporal import (
    analyze_original_hero_temporal_clip, compare_visible_rasters,
)

WIDTH, HEIGHT = 4, 3


def pose(colour=100, visible_xs=(1, 2), y=2,
         hidden_colour=0, opacity=255):
    rgba = bytearray(WIDTH * HEIGHT * 4)
    for x in range(WIDTH):
        off = x * 4
        rgba[off:off + 4] = bytes((hidden_colour, 99, 88, 0))
    for x in visible_xs:
        off = (y * WIDTH + x) * 4
        rgba[off:off + 4] = bytes((colour, 0, 255, opacity))
    return bytes(rgba)


class OriginalHeroTemporalTests(unittest.TestCase):
    def test_static_and_one_pixel_visible_recolour(self):
        a = pose()
        b = pose(colour=101)
        static = compare_visible_rasters(a, a, width=WIDTH, height=HEIGHT)
        self.assertTrue(static["visually_static"])
        self.assertEqual(static["alpha_iou_basis_points"], 10000)
        self.assertEqual(static["contact_shift_x2_y2"], [0, 0])
        changed = compare_visible_rasters(a, b, width=WIDTH, height=HEIGHT)
        self.assertEqual(changed["visible_changed_pixels"], 2)
        self.assertEqual(changed["alpha_changed_pixels"], 0)
        self.assertEqual(changed["change_bbox_xyxy"], [1, 2, 2, 2])
        self.assertEqual(changed["alpha_iou_basis_points"], 10000)

    def test_invisible_rgb_does_not_create_false_motion(self):
        x = pose(hidden_colour=1)
        y = pose(hidden_colour=200)
        result = compare_visible_rasters(x, y, width=WIDTH, height=HEIGHT)
        self.assertEqual(result["visible_changed_pixels"], 0)
        self.assertEqual(result["change_bbox_xyxy"], None)
        self.assertEqual(result["alpha_changed_pixels"], 0)

    def test_alpha_and_footprint_contact_are_measured_not_smoothed(self):
        a = pose(visible_xs=(1,), y=2)
        b = pose(visible_xs=(2,), y=1)
        metric = compare_visible_rasters(a, b, width=WIDTH, height=HEIGHT)
        self.assertEqual(metric["visible_changed_pixels"], 2)
        self.assertEqual(metric["alpha_changed_pixels"], 2)
        self.assertEqual(metric["alpha_iou_basis_points"], 0)
        self.assertEqual(metric["contact_shift_x2_y2"], [2, -2])
        self.assertEqual(metric["change_bbox_xyxy"], [1, 1, 2, 2])
        semitransparent = pose(opacity=1)
        self.assertEqual(compare_visible_rasters(
            pose(), semitransparent, width=WIDTH, height=HEIGHT
        )["alpha_changed_pixels"], 2)

    def test_counterfactual_loop_is_report_only(self):
        a = pose()
        b = pose(colour=77)
        report = analyze_original_hero_temporal_clip(
            [a, a, b, a], [1205, 1206, 1207, 1208],
            width=WIDTH, height=HEIGHT)
        self.assertEqual(report["frame_count"], 4)
        self.assertEqual(report["observed_static_edges"], 1)
        self.assertEqual(report["observed_dynamic_edges"], 2)
        self.assertEqual(report["distinct_rgba_frames"], 2)
        self.assertEqual(report["max_observed_visible_change_pixels"], 2)
        self.assertEqual(report["counterfactual_last_to_first_edge"][
            "visible_changed_pixels"], 0)
        self.assertFalse(report["counterfactual_last_to_first_edge"][
            "is_observed_chronological_edge"])
        self.assertFalse(report["loop_certified"])
        self.assertFalse(report["source_guest_timing_independently_certified"])
        self.assertEqual(report["artistic_approval"], "pending")

    def test_loop_seam_can_exceed_observed_changes_without_authorizing_loop(self):
        a = pose(visible_xs=(1,))
        b = pose(visible_xs=(1, 2))
        c = pose(visible_xs=(2, 3))
        report = analyze_original_hero_temporal_clip(
            [a, b, c], [1230, 1231, 1232], width=WIDTH, height=HEIGHT)
        self.assertEqual(report["observed_dynamic_edges"], 2)
        self.assertEqual(report["counterfactual_last_to_first_edge"][
            "visible_changed_pixels"], 3)
        self.assertFalse(report["loop_certified"])

    def test_invalid_lengths_bad_labels_and_alpha_empty_fail_closed(self):
        a = pose()
        invalid = [
            ([], []), ([a], [5]), ([a, a], [5]),
            ([a, a], [5, 7]), ([a, a], [5, 5]),
            ([a, a], [True, 1]), ([a, a], [-1, 0]),
        ]
        for frames, labels in invalid:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                analyze_original_hero_temporal_clip(
                    frames, labels, width=WIDTH, height=HEIGHT)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            compare_visible_rasters(a, a[:-1], width=WIDTH, height=HEIGHT)
        with self.assertRaisesRegex(ValueError, "no visible pixels"):
            compare_visible_rasters(a, bytes(len(a)), width=WIDTH, height=HEIGHT)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            compare_visible_rasters(a, a, width=0, height=HEIGHT)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            compare_visible_rasters(a, a, width=2**32, height=HEIGHT)


if __name__ == "__main__":
    unittest.main()

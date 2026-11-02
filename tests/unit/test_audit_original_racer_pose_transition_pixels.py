"""ROM-free negative controls for original 2D versus model-pose pixel motion."""
import unittest

from tools.art.audit_original_racer_pose_transition_pixels import (
    pixel_change, summarize,
)


def mask(*points):
    result = bytearray(4096)
    for x, y in points:
        result[y * 64 + x] = 1
    return bytes(result)


class SourcePixelMotionTests(unittest.TestCase):
    def test_exact_source_and_model_motion(self):
        a, b = mask((1, 1), (2, 1)), mask((2, 1), (3, 1))
        row = pixel_change(a, b, a, b, b)
        self.assertEqual(row["source_changed_pixel_count"], 2)
        self.assertEqual(row["model_placed_changed_pixel_count"], 2)
        self.assertEqual(row["model_pose_only_changed_pixel_count"], 2)
        self.assertEqual(row["source_changed_pixels_overlapping_pose_only_model_change"], 2)
        self.assertEqual(row["pose_only_model_source_change_recall"], 1)
        self.assertEqual(row["pose_only_model_source_change_precision"], 1)
        self.assertEqual(row["source_changed_pixels_explained_by_placed_model"], 2)
        self.assertEqual(row["placed_model_change_iou"], 1)
        self.assertEqual(row["placed_model_source_change_recall"], 1)
        self.assertTrue(row["original_source_binary_silhouette_changed"])

    def test_stationary_source_and_stationary_model(self):
        a = mask((1, 1), (2, 1))
        row = pixel_change(a, a, a, a, a)
        self.assertEqual(row["source_changed_pixel_count"], 0)
        self.assertEqual(row["placed_model_change_iou"], 1)
        self.assertIsNone(row["placed_model_source_change_precision"])
        self.assertIsNone(row["placed_model_source_change_recall"])
        self.assertIsNone(row["pose_only_model_source_change_recall"])
        self.assertIsNone(row["pose_only_model_source_change_precision"])
        self.assertTrue(row["both_source_and_model_stationary"])

    def test_motion_from_visible_anchor_is_not_articulation(self):
        a = mask((1, 1))
        b = mask((2, 1))
        measured = pixel_change(a, b, a, b, a)
        self.assertEqual(measured["source_changed_pixel_count"], 2)
        self.assertEqual(measured["model_placed_changed_pixel_count"], 2)
        self.assertEqual(measured["model_pose_only_changed_pixel_count"], 0)
        self.assertEqual(measured["source_changed_pixels_overlapping_pose_only_model_change"], 0)
        self.assertEqual(measured["pose_only_model_source_change_recall"], 0)
        self.assertIsNone(measured["pose_only_model_source_change_precision"])
        self.assertTrue(measured["model_placed_raster_changed"])
        self.assertFalse(measured["model_pose_only_raster_changed"])

    def test_source_change_can_be_unexplained_by_same_pose(self):
        a, b = mask((1, 1)), mask((2, 1))
        measured = pixel_change(a, b, a, a, a)
        self.assertEqual(measured["source_changed_pixels_not_explained_by_placed_model"], 2)
        self.assertEqual(measured["placed_model_source_change_recall"], 0)
        self.assertFalse(measured["model_placed_raster_changed"])

    def test_spurious_motion_does_not_count_as_recall(self):
        source = mask((1, 1))
        a = mask((3, 3))
        b = mask((4, 3))
        row = pixel_change(source, source, a, b, b)
        self.assertEqual(row["source_changed_pixel_count"], 0)
        self.assertEqual(row["model_placed_changed_pixel_count"], 2)
        self.assertEqual(row["placed_model_change_iou"], 0)
        self.assertIsNone(row["placed_model_source_change_recall"])

    def test_nonbinary_empty_and_wrong_size_rejected(self):
        sample = mask((1, 1))
        for bad in (bytes(4096), bytes(4095), bytes([2]) + bytes(4095),
                    [0] * 4096):
            with self.subTest(bad=str(type(bad)) + str(len(bad))):
                with self.assertRaises(ValueError):
                    pixel_change(sample, sample, sample, sample, bad)

    def test_summary_distinguishes_source_and_model_edges(self):
        a = mask((1, 1))
        b = mask((2, 1))
        edge_a = {
            "model_pose_label_changed": False,
            "source_visible_alpha_anchor_changed": True,
            "motion": pixel_change(a, b, a, b, a),
        }
        edge_b = {
            "model_pose_label_changed": True,
            "source_visible_alpha_anchor_changed": False,
            "motion": pixel_change(a, a, a, b, b),
        }
        report = summarize([edge_a, edge_b])
        self.assertEqual(report["actually_consecutive_original_guest_frame_edges"], 2)
        self.assertEqual(report["original_binary_silhouette_changed_edges"], 1)
        self.assertEqual(report["original_binary_silhouette_held_edges"], 1)
        self.assertEqual(report["source_binary_changed_pixels_total"], 2)
        self.assertEqual(report["placed_model_overlapping_source_change_pixels"], 2)
        self.assertEqual(report["model_pose_label_transition_edges"], 1)
        self.assertEqual(report["pose_only_model_changed_pixel_count"], 2)
        self.assertEqual(report["pose_only_model_overlapping_source_changed_pixels"], 0)
        self.assertEqual(report["pose_only_model_changed_pixel_recall"], 0)
        self.assertEqual(report["pose_only_model_changed_pixel_precision"], 0)
        self.assertEqual(report["source_placement_anchor_changed_edges"], 1)
        self.assertEqual(report["source_moving_edges_with_no_pose_only_pixel_change"], 1)
        self.assertEqual(report["source_stationary_edges_with_spurious_model_pixel_change"], 1)

    def test_empty_edges_refused(self):
        with self.assertRaises(ValueError):
            summarize([])


if __name__ == "__main__":
    unittest.main()

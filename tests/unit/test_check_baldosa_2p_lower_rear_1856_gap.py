"""Real native 2P lower rear-source final visibility and priority tests."""
import unittest

from tools.check_baldosa_2p_lower_rear_1856_gap import (
    classify, verify_upper_original_rear_source_mirrors,
    check_candidate_preserves_rear_source_gaps,
    EXPECTED_MASKED_REAR_ONLY, WIDTH, HEIGHT
)


class Original2PLowerRearExceptionTest(unittest.TestCase):
    def setUp(self):
        self.stock = bytearray(bytes((57, 57, 255, 0)) * WIDTH * HEIGHT)
        self.removed = bytearray(self.stock)
        self.front = bytearray(WIDTH * HEIGHT * 4)
        self.rear = bytearray(WIDTH * HEIGHT * 4)
        self.positions = {
            "front_only": (110, 156),
            "rear_only": (111, 156),
            "masked_rear": (188, 156),
            "different_overlap": (112, 156),
            "equal_overlap": (113, 156),
            "background": (114, 156),
        }
        red = bytes((173, 33, 8, 255))
        green = bytes((24, 123, 16, 255))
        grey = bytes((74, 74, 74, 255))
        def paint(plane, key, pixel):
            x, y = self.positions[key]
            at = (y * WIDTH + x) * 4
            plane[at:at + 4] = pixel
        def finalpaint(plane, key, rgba):
            x, y = self.positions[key]
            at = (y * WIDTH + x) * 4
            plane[at:at + 4] = bytes((*rgba, 0))
        paint(self.front, "front_only", red)
        finalpaint(self.stock, "front_only", red[:3])
        # The original front is removed and the pre-existing blue remains.
        paint(self.rear, "rear_only", green)
        finalpaint(self.stock, "rear_only", green[:3])
        finalpaint(self.removed, "rear_only", green[:3])
        paint(self.rear, "masked_rear", grey)
        # Stock and removal intentionally remain Original blue at
        # this lower *rear-only* source pixel.
        paint(self.front, "different_overlap", red)
        paint(self.rear, "different_overlap", green)
        finalpaint(self.stock, "different_overlap", red[:3])
        finalpaint(self.removed, "different_overlap", green[:3])
        paint(self.front, "equal_overlap", grey)
        paint(self.rear, "equal_overlap", grey)
        finalpaint(self.stock, "equal_overlap", grey[:3])
        finalpaint(self.removed, "equal_overlap", grey[:3])

    def measure(self):
        return classify(self.stock, self.front, self.rear, self.removed)

    def test_true_visible_front_rear_and_three_way_partition(self):
        report = self.measure()
        c = report["counts"]
        self.assertEqual(report["source_raster_relationship_status"],
                         "source-and-native-front-removal-consistent")
        self.assertEqual(c["front_only"], 1)
        self.assertEqual(c["rear_only"], 2)
        self.assertEqual(c["overlap_different_rgb"], 1)
        self.assertEqual(c["overlap_equal_rgb"], 1)
        self.assertEqual(c["front_only_changed"], 1)
        self.assertEqual(c["front_overlap_different_changed"], 1)
        self.assertEqual(c["different_overlap_exact_rear_reveals"], 1)
        self.assertEqual(c["front_overlap_equal_unchanged"], 1)
        self.assertEqual(c["rear_only_original_rgb_matches"], 1)
        self.assertEqual(c["rear_only_original_rgb_differs"], 1)
        self.assertEqual(c["rear_only_unchanged_after_front_removal"], 2)
        self.assertEqual(c["final_changed_outside_front_source"], 0)
        self.assertEqual(c["unexpected_original_priority_pixels"], 0)
        self.assertEqual(report["rear_only_source_hidden_by_stock_rgb"], [
            {
                "xy": [188, 156],
                "isolated_rear_source_rgb": [74, 74, 74],
                "original_stock_rgb": [57, 57, 255],
                "removed_front_rgb": [57, 57, 255],
                "stock_rgba_alpha": 0,
            }
        ])
        self.assertFalse(report["safe_to_paint_rear_behind_front_in_hd"])

    def test_changed_outside_front_source_always_fails(self):
        x, y = self.positions["background"]
        at = (y * WIDTH + x) * 4
        self.removed[at] ^= 1
        out = self.measure()
        self.assertEqual(out["counts"]["final_changed_outside_front_source"], 1)
        self.assertEqual(out["source_raster_relationship_status"],
                         "source-and-native-front-removal-disagree")

    def test_different_overlap_must_reveal_real_rear_colour(self):
        x, y = self.positions["different_overlap"]
        at = (y * WIDTH + x) * 4
        self.removed[at] ^= 4
        out = self.measure()
        self.assertEqual(out["counts"]["different_overlap_exact_rear_reveals"], 0)
        self.assertGreater(out["counts"]["unexpected_original_priority_pixels"], 0)

    def test_equal_colour_overlap_cannot_change_final(self):
        x, y = self.positions["equal_overlap"]
        at = (y * WIDTH + x) * 4
        self.removed[at] ^= 2
        out = self.measure()
        self.assertEqual(out["counts"]["front_overlap_equal_unchanged"], 0)
        self.assertGreater(out["counts"]["unexpected_original_priority_pixels"], 0)

    def test_rear_only_absence_must_remain_unchanged_by_front_removal(self):
        x, y = self.positions["masked_rear"]
        at = (y * WIDTH + x) * 4
        self.removed[at:at + 3] = self.rear[at:at + 3]
        out = self.measure()
        self.assertEqual(out["counts"]["rear_only_unchanged_after_front_removal"], 1)
        self.assertEqual(out["source_raster_relationship_status"],
                         "source-and-native-front-removal-disagree")

    def test_invalid_size_is_not_a_valid_original_native_plane(self):
        with self.assertRaisesRegex(ValueError, "four exact complete"):
            classify(self.stock, self.front[:-4], self.rear, self.removed)

    def test_no_opaque_rear_cannot_fabricate_original_source_exception(self):
        x, y = self.positions["masked_rear"]
        at = (y * WIDTH + x) * 4
        self.rear[at + 3] = 0
        out = self.measure()
        self.assertEqual(out["counts"]["rear_only_original_rgb_differs"], 0)
        self.assertEqual(out["rear_only_source_hidden_by_stock_rgb"], [])

    def test_upper_mirror_colour_corroborates_lower_source_but_not_final(self):
        lower = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        self.assertEqual(len(lower), 1)
        x, y = lower[0]["xy"]
        upper_at = 4 * ((y - 113) * WIDTH + x)
        # Real PPU mirror: original top resolves rear source,
        # while the original lower output retained different blue.
        self.stock[upper_at:upper_at + 3] = bytes((74, 74, 74))
        mirrors = verify_upper_original_rear_source_mirrors(
            self.stock, lower)
        self.assertEqual(mirrors[0]["upper_mirror_xy"], [188, 43])
        self.assertEqual(mirrors[0]["upper_stock_original_rgb"], [74, 74, 74])
        self.assertEqual(mirrors[0]["lower_stock_original_rgb"], [57, 57, 255])

    def test_upper_mirror_wrong_colour_rejects_source_identity_claim(self):
        lower = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        with self.assertRaisesRegex(ValueError, "does not corroborate"):
            verify_upper_original_rear_source_mirrors(self.stock, lower)

    def test_malformed_upper_mirror_coordinate_is_rejected(self):
        lower = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        lower[0]["xy"][1] = 100
        with self.assertRaisesRegex(ValueError, "cannot have top mirror"):
            verify_upper_original_rear_source_mirrors(self.stock, lower)

    def test_hidden_lower_rear_gap_original_four_x_subpixels_all_protected(self):
        gaps = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        expanded = self.scale_original_stock_four_x()
        report = check_candidate_preserves_rear_source_gaps(
            self.stock, expanded, 4, gaps)
        self.assertEqual(report["status"],
                         "original-hidden-rear-source-gap-preserved")
        self.assertEqual(report["protected_density_subpixels"], 16)
        self.assertEqual(report["changed_protected_density_subpixels"], 0)
        self.assertFalse(report["approved_remastered_art"])

    def test_hidden_rear_gap_one_four_x_subpixel_overpaint_is_detected(self):
        gaps = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        expanded = bytearray(self.scale_original_stock_four_x())
        x, y = self.positions["masked_rear"]
        at = 4 * ((y * 4 + 3) * (WIDTH * 4) + x * 4 + 2)
        expanded[at] ^= 1
        report = check_candidate_preserves_rear_source_gaps(
            self.stock, expanded, 4, gaps)
        self.assertEqual(report["status"],
                         "original-rear-source-gap-overpaint")
        self.assertEqual(report["changed_protected_density_subpixels"], 1)
        self.assertEqual(report["bounded_changed_examples"], [[188, 156, 2, 3]])

    def test_guard_rejects_unknown_scale_and_cropped_candidate(self):
        gaps = self.measure()["rear_only_source_hidden_by_stock_rgb"]
        with self.assertRaisesRegex(ValueError, "1x..4x"):
            check_candidate_preserves_rear_source_gaps(
                self.stock, self.stock, 5, gaps)
        with self.assertRaisesRegex(ValueError, "complete 342-wide"):
            check_candidate_preserves_rear_source_gaps(
                self.stock, self.stock[:-4], 1, gaps)

    def scale_original_stock_four_x(self):
        # Exact Original density fallback, not an authored HD texture.
        out = bytearray()
        stock = memoryview(self.stock)
        for y in range(HEIGHT):
            start = y * WIDTH * 4
            row = stock[start:start + WIDTH * 4]
            wide = b"".join(row[4*x:4*x + 4].tobytes() * 4
                            for x in range(WIDTH))
            out.extend(wide * 4)
        return bytes(out)

    def test_real_native_witness_names_all_three_exact_coordinates(self):
        self.assertEqual(
            [(x, y) for x, y, _, _ in EXPECTED_MASKED_REAR_ONLY],
            [(188, 156), (189, 156), (189, 157)])
        self.assertEqual([source for _, _, source, _ in
                          EXPECTED_MASKED_REAR_ONLY],
                         [(49, 49, 49), (74, 74, 74), (16, 16, 8)])
        self.assertEqual({original for _, _, _, original in
                          EXPECTED_MASKED_REAR_ONLY}, {(57, 57, 255)})


if __name__ == "__main__":
    unittest.main()

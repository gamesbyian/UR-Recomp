"""Synthetic fixed-coordinate calibration and retained-source identity tests."""
import hashlib
import unittest
from pathlib import Path

from tools.art.score_racer_candidate import (
    mask_from_rgba, score, score_retained_original,
)
from tools.art.build_racer_source_pixel_corpus import STRIP


def mask(*points):
    result = [0] * (64 * 64)
    for x, y in points:
        result[y*64+x] = 1
    return tuple(result)


def render_rgba(points, density=1, centre_only=False):
    w = 64*density
    rgba = bytearray(w*w*4)
    for x, y in points:
        if centre_only:
            rgba[((y*density+density//2)*w +
                  (x*density+density//2))*4+3] = 255
        else:
            for sy in range(density):
                for sx in range(density):
                    rgba[((y*density+sy)*w+(x*density+sx))*4+3] = 255
    return bytes(rgba)


class RegisteredSilhouetteScoreTests(unittest.TestCase):
    def test_identical_alpha_has_zero_error(self):
        data = mask((9, 20), (10, 20), (11, 19))
        result = score(data, data)
        self.assertEqual(result["mask_iou"], 1)
        self.assertEqual(result["mask_xor_pixels"], 0)
        self.assertEqual(result["boundary_chamfer_mean_physical_px"], 0)
        self.assertEqual(result["lowest_alpha_delta_x2_y2"], [0, 0])
        self.assertFalse(result["owner_likeness_approved"])
        self.assertFalse(result["shipping_art_approved"])

    def test_one_pixel_translation_is_not_auto_registered(self):
        original = mask((10, 20), (11, 20))
        moved = mask((11, 20), (12, 20))
        result = score(original, moved)
        self.assertAlmostEqual(result["mask_iou"], 1/3, places=7)
        self.assertEqual(result["mask_xor_pixels"], 2)
        self.assertEqual(result["lowest_alpha_delta_x2_y2"], [2, 0])
        self.assertGreater(result["boundary_chamfer_mean_physical_px"], 0)
        self.assertFalse(result["auto_registration_performed"])

    def test_4x_source_centres_project_to_same_logical_pixels(self):
        points = {(9, 20), (11, 20), (11, 19)}
        original = mask_from_rgba(render_rgba(points, 1), 64, 64, 1)
        full_density = mask_from_rgba(render_rgba(points, 4), 256, 256, 4)
        centres = mask_from_rgba(render_rgba(points, 4, centre_only=True), 256, 256, 4)
        self.assertEqual(original, full_density)
        self.assertEqual(original, centres)
        self.assertEqual(score(original, centres)["mask_iou"], 1)

    def test_offcentre_4x_alpha_cannot_fake_source_coverage(self):
        image = bytearray(render_rgba({(10, 20)}, 4, centre_only=True))
        image[((20*4+2)*256+(10*4+2))*4+3] = 0
        image[((20*4)*256+(10*4))*4+3] = 255
        with self.assertRaisesRegex(ValueError, "empty"):
            score(mask((10, 20)), mask_from_rgba(bytes(image), 256, 256, 4))

    def test_missing_alpha_and_bad_canvas_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            score(mask((10, 20)), mask())
        with self.assertRaisesRegex(ValueError, "canvas"):
            mask_from_rgba(bytes(64*64*4), 64, 64, 4)
        with self.assertRaisesRegex(ValueError, "length"):
            mask_from_rgba(b"invalid", 64, 64, 1)

    def test_actual_retained_stock_as_candidate_is_trivially_perfect_but_unapproved(self):
        image = STRIP / "stock/p1-00.png"
        sha = hashlib.sha256(image.read_bytes()).hexdigest()
        result = score_retained_original("p1", 1205, image, sha, 1)
        self.assertEqual(result["mask_iou"], 1)
        self.assertTrue(result["candidate_is_identical_original_png"])
        self.assertFalse(result["candidate_mesh_identity_verified"])
        self.assertFalse(result["shipping_art_approved"])

    def test_candidate_hash_and_unknown_frame_rejected(self):
        image = STRIP / "stock/p1-00.png"
        with self.assertRaisesRegex(ValueError, "SHA256"):
            score_retained_original("p1", 1205, image, "invalid", 1)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            score_retained_original("p1", 2208, image, "0"*64, 1)
        with self.assertRaisesRegex(ValueError, "does not match"):
            score_retained_original("p1", 1205, image, "0"*64, 1)


if __name__ == "__main__":
    unittest.main()

import unittest

from tools.check_racer_hd_foreground_occlusion import (
    HEIGHT, WIDTH, PAM_HEADER, analyze, parse_obj_pam,
)


def ppm(data):
    return b"P6\n256 224\n255\n" + bytes(data)


def placements():
    return "\n".join(
        "UR_RACER_HD_DRAW PASS frame=1220 semantic=0541 "
        f"viewport={viewport} slot={slot} x=104 y={y} "
        "hflip=1 vflip=0 density=4 output_scale=1 guest_state_unchanged=1"
        for viewport, slot, y in [
            ("top", 98, 40), ("top", 99, 40),
            ("bottom", 97, 153), ("bottom", 96, 153),
        ]
    )


def set_rgb(data, x, y, rgb):
    i = (y * WIDTH + x) * 3
    data[i:i + 3] = bytes(rgb)


def set_rgba(data, x, y, rgba):
    i = (y * WIDTH + x) * 4
    data[i:i + 4] = bytes(rgba)


class RacerForegroundDepthTests(unittest.TestCase):
    def setUp(self):
        self.stock = bytearray(bytes([12, 18, 24]) * (WIDTH * HEIGHT))
        self.hd = bytearray(self.stock)
        self.obj = bytearray(WIDTH * HEIGHT * 4)

    def test_detects_potential_foreground_overpaint_with_direct_control(self):
        # One naturally visible OBJ pixel, one candidate occluded by a
        # green foreground pixel, one mismatch the host left unchanged.
        set_rgb(self.stock, 125, 42, [100, 10, 20])
        set_rgba(self.obj, 125, 42, [100, 10, 20, 255])
        set_rgb(self.stock, 126, 43, [0, 200, 0])
        set_rgba(self.obj, 126, 43, [100, 10, 20, 255])
        set_rgb(self.stock, 127, 45, [0, 200, 0])
        set_rgba(self.obj, 127, 45, [100, 10, 20, 255])
        self.hd[:] = self.stock
        set_rgb(self.hd, 125, 42, [200, 180, 90])
        set_rgb(self.hd, 126, 43, [200, 180, 90])
        output = analyze(
            ppm(self.stock), ppm(self.stock), ppm(self.hd),
            PAM_HEADER + self.obj, placements(), 1220
        )
        self.assertEqual(output["native_split_obj_opaque_pixels"], 3)
        self.assertEqual(output["stock_obj_matches_original_rgb_pixels"], 1)
        self.assertEqual(output["stock_obj_differs_from_original_rgb_pixels"], 2)
        self.assertEqual(output["hd_modifies_obj_pixels_that_match_original"], 1)
        self.assertEqual(output["potential_foreground_occlusion_overpaint_pixels"], 1)
        self.assertEqual(output["overpaint_pixel_examples"], [[126, 43]])
        self.assertTrue(output["review_required"])

    def test_unchanged_foreground_pixel_reports_no_overpaint(self):
        set_rgb(self.stock, 126, 43, [0, 200, 0])
        set_rgba(self.obj, 126, 43, [100, 10, 20, 255])
        self.hd[:] = self.stock
        output = analyze(
            ppm(self.stock), ppm(self.stock), ppm(self.hd),
            PAM_HEADER + self.obj, placements(), 1220
        )
        self.assertEqual(output["stock_obj_differs_from_original_rgb_pixels"], 1)
        self.assertEqual(output["potential_foreground_occlusion_overpaint_pixels"], 0)
        self.assertFalse(output["review_required"])

    def test_outside_live_racer_bounds_is_not_a_false_positive(self):
        set_rgb(self.stock, 10, 10, [0, 200, 0])
        set_rgba(self.obj, 10, 10, [100, 10, 20, 255])
        set_rgba(self.obj, 125, 42, [12, 18, 24, 255])
        self.hd[:] = self.stock
        set_rgb(self.hd, 10, 10, [200, 180, 90])
        out = analyze(
            ppm(self.stock), ppm(self.stock), ppm(self.hd),
            PAM_HEADER + self.obj, placements(), 1220
        )
        self.assertEqual(out["native_split_obj_opaque_pixels"], 1)
        self.assertEqual(out["potential_foreground_occlusion_overpaint_pixels"], 0)

    def test_independent_original_obj_only_ppm_works_without_overlay_api(self):
        isolated_stock = bytearray(WIDTH * HEIGHT * 3)
        set_rgb(self.stock, 125, 42, [100, 10, 20])
        set_rgb(isolated_stock, 125, 42, [100, 10, 20])
        # Original foreground obscures the stock OBJ-only pixel.
        set_rgb(self.stock, 126, 43, [0, 200, 0])
        set_rgb(isolated_stock, 126, 43, [100, 10, 20])
        # Black is indistinguishable from backdrop in P6 and must be excluded.
        self.hd[:] = self.stock
        set_rgb(self.hd, 125, 42, [200, 180, 90])
        set_rgb(self.hd, 126, 43, [200, 180, 90])
        got = analyze(
            ppm(self.stock), ppm(self.stock), ppm(self.hd),
            b"", placements(), 1220,
            obj_only_ppm=ppm(isolated_stock),
        )
        self.assertEqual(got["native_split_obj_opaque_pixels"], 2)
        self.assertEqual(got["potential_foreground_occlusion_overpaint_pixels"], 1)
        self.assertIn("lower-bound", got["source_layer_classification"])

    def test_colored_red_backdrop_is_not_falsely_treated_as_sprite(self):
        masked = bytearray(bytes((240, 0, 0)) * (WIDTH * HEIGHT))
        set_rgb(masked, 125, 42, [80, 120, 200])
        set_rgb(self.stock, 125, 42, [80, 120, 200])
        self.hd[:] = self.stock
        set_rgb(self.hd, 125, 42, [120, 160, 240])
        got = analyze(
            ppm(self.stock), ppm(self.stock), ppm(self.hd),
            b"", placements(), 1220,
            obj_only_ppm=ppm(masked)
        )
        self.assertEqual(got["excluded_backdrop_rgb"], [240, 0, 0])
        self.assertEqual(got["backdrop_pixel_count"], WIDTH * HEIGHT - 1)
        self.assertEqual(got["native_split_obj_opaque_pixels"], 1)
        self.assertEqual(got["stock_obj_differs_from_original_rgb_pixels"], 0)

    def test_nonuniform_obj_only_background_is_unsafe(self):
        alternating = bytearray(WIDTH * HEIGHT * 3)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                set_rgb(alternating, x, y, (255, 0, 0) if x % 2 else (0, 255, 0))
        with self.assertRaisesRegex(ValueError, "backdrop is not sufficiently uniform"):
            analyze(
                ppm(self.stock), ppm(self.stock), ppm(self.hd), b"",
                placements(), 1220, obj_only_ppm=ppm(alternating)
            )

    def test_empty_obj_only_frame_fails_instead_of_faking_zero_occlusion(self):
        with self.assertRaisesRegex(ValueError, "no opaque racer"):
            analyze(
                ppm(self.stock), ppm(self.stock), ppm(self.hd),
                b"", placements(), 1220,
                obj_only_ppm=ppm(bytearray(WIDTH * HEIGHT * 3)),
            )

    def test_missing_obj_pixels_and_bad_inputs_fail(self):
        with self.assertRaisesRegex(ValueError, "no opaque racer"):
            analyze(
                ppm(self.stock), ppm(self.stock), ppm(self.hd),
                PAM_HEADER + self.obj, placements(), 1220
            )
        with self.assertRaisesRegex(ValueError, "references differ"):
            analyze(
                ppm(self.stock), ppm(self.stock) + b"x", ppm(self.hd),
                PAM_HEADER + self.obj, placements(), 1220
            )
        with self.assertRaisesRegex(ValueError, "PAM header"):
            parse_obj_pam(b"P7\nBAD\n" + self.obj)
        with self.assertRaisesRegex(ValueError, "byte count mismatch"):
            parse_obj_pam(PAM_HEADER + b"x")
        with self.assertRaisesRegex(ValueError, "invalid anisotropic"):
            # A valid P6 width 257 is not a permitted integer HD expansion.
            anisotropic = b"P6\n257 224\n255\n" + bytes(257 * HEIGHT * 3)
            analyze(
                ppm(self.stock), ppm(self.stock), anisotropic,
                PAM_HEADER + self.obj, placements(), 1220
            )


if __name__ == "__main__":
    unittest.main()

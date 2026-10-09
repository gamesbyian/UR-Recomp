import unittest

from tools.check_racer_hd_pixel_confinement import (
    audit, allowed_logical_mask, live_placements, parse_ppm,
)

W, H = 256, 224


def ppm(w, h, pixels):
    return f"P6\n{w} {h}\n255\n".encode("ascii") + pixels


def frames(scale=4):
    base = bytes([20, 40, 60])
    return ppm(W, H, base * (W * H)), bytearray(ppm(W * scale, H * scale, base * (W * H * scale * scale)))


def paint(data, scale, x, y):
    header = len(f"P6\n{W * scale} {H * scale}\n255\n".encode())
    at = header + ((y * scale) * W * scale + x * scale) * 3
    data[at:at + 3] = bytes([220, 150, 25])


def draw_log(top_y=40, bottom_y=153):
    placements = [
        ("top", 98, top_y), ("top", 99, top_y),
        ("bottom", 97, bottom_y), ("bottom", 96, bottom_y),
    ]
    return "\n".join(
        f"UR_RACER_HD_DRAW PASS frame=1220 semantic=0541 viewport={vp} "
        f"slot={slot} x=104 y={y} hflip=1 vflip=0 "
        f"density=4 output_scale=4 guest_state_unchanged=1"
        for vp, slot, y in placements
    )


class RacerHdPixelConfinementTests(unittest.TestCase):
    def test_complete_4x_output_and_stock_control_untouched_outside_live_oam(self):
        stock, hd = frames()
        paint(hd, 4, 125, 42)
        paint(hd, 4, 125, 155)
        report = audit(stock, bytes(hd), draw_log(), 1220, second_original=stock)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["changed_output_density_pixels"], 2)
        self.assertEqual(report["top_changed_pixels"], 1)
        self.assertEqual(report["bottom_changed_pixels"], 1)
        self.assertEqual(len(report["actual_live_oam_slots"]), 4)
        self.assertTrue(report["original_controls_pixel_exact"])

    def test_single_pixel_hud_or_world_corruption_fails_even_at_4x(self):
        stock, hd = frames()
        paint(hd, 4, 125, 42)
        paint(hd, 4, 125, 155)
        paint(hd, 4, 10, 10)
        report = audit(stock, bytes(hd), draw_log(), 1220)
        self.assertFalse(report["ok"])
        self.assertEqual(report["outside_live_oam_pixel_samples"][0], [40, 40, 10, 10])

    def test_live_split_scanline_112_is_not_top_viewport(self):
        mask = allowed_logical_mask(live_placements(draw_log(top_y=110), 1220))
        self.assertEqual(mask[111 * W + 125], 1)
        self.assertEqual(mask[112 * W + 125], 0)

    def test_hardware_y_wrap_is_256_not_224(self):
        mask = allowed_logical_mask(live_placements(draw_log(top_y=250), 1220))
        self.assertEqual(mask[0 * W + 125], 1)
        self.assertEqual(mask[58 * W + 125], 0)

    def test_missing_or_duplicate_oam_slot_rejected(self):
        full = draw_log()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            live_placements(full + "\n" + full.splitlines()[0], 1220)
        with self.assertRaisesRegex(ValueError, "missing"):
            live_placements("\n".join(full.splitlines()[:-1]), 1220)

    def test_unstable_original_reference_and_wrong_geometry_rejected(self):
        original, hd = frames()
        with self.assertRaisesRegex(ValueError, "unstable screenshot"):
            audit(original, bytes(hd), draw_log(), 1220, second_original=original + b"X")
        with self.assertRaisesRegex(ValueError, "integer square-density"):
            audit(original, ppm(257, 224, bytes([0, 0, 0]) * (257 * 224)), draw_log(), 1220)
        with self.assertRaisesRegex(ValueError, "P6 payload length"):
            parse_ppm(b"P6\n256 224\n255\n" + b"x")

    def test_hd_that_changes_nothing_is_not_accepted(self):
        original, hd = frames()
        report = audit(original, bytes(hd), draw_log(), 1220)
        self.assertFalse(report["ok"])
        self.assertEqual(report["changed_output_density_pixels"], 0)


if __name__ == "__main__":
    unittest.main()

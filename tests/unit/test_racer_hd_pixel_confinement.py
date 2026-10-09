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

    def test_source_empty_lower_viewport_must_not_acquire_hd_rider(self):
        stock, hd = frames()
        pam = (
            b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
            b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
        )
        rgba = bytearray(256 * 224 * 4)
        rgba[(42 * W + 125) * 4 + 3] = 255
        paint(hd, 4, 125, 42)
        report = audit(
            stock, bytes(hd), draw_log(), 1220,
            second_original=stock, source_obj_layer=pam + rgba,
        )
        self.assertTrue(report["ok"], report)
        self.assertEqual(
            report["source_obj_opaque_by_viewport"], {"top": 1, "bottom": 0}
        )
        self.assertEqual(report["bottom_changed_pixels"], 0)
        self.assertFalse(report["hd_changes_without_source_obj"])
        # The formerly fabricated lower rider is independently detectable:
        paint(hd, 4, 125, 155)
        bad = audit(
            stock, bytes(hd), draw_log(), 1220,
            second_original=stock, source_obj_layer=pam + rgba,
        )
        self.assertFalse(bad["ok"])
        self.assertTrue(bad["hd_changes_without_source_obj"])
        # No valid PPU source cannot be promoted to a high-confidence pass.
        with self.assertRaisesRegex(ValueError, "entirely absent"):
            audit(
                stock, bytes(hd), draw_log(), 1220,
                source_obj_layer=pam + bytes(256 * 224 * 4)
            )
        with self.assertRaisesRegex(ValueError, "invalid original PPU"):
            audit(
                stock, bytes(hd), draw_log(), 1220,
                source_obj_layer=b"P7\\nBAD"
            )

    def test_disjoint_same_viewport_phantom_fails_real_obj_alpha_oracle(self):
        stock, hd = frames()
        pam = (
            b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
            b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
        )
        source = bytearray(W * H * 4)
        source[(42 * W + 125) * 4 + 3] = 255
        # Disjoint top racers: P1 at 104, P2 at 190. The isolated PPU
        # emitted source alpha only at P1. A viewport-wide guard says
        # top is nonempty, but must not license P2's new artwork.
        shifted = "\n".join(
            line.replace("slot=99 x=104", "slot=99 x=190")
            for line in draw_log().splitlines()
        )
        paint(hd, 4, 125, 42)
        ok = audit(
            stock, bytes(hd), shifted, 1220, second_original=stock,
            source_obj_layer=pam + source
        )
        self.assertTrue(ok["ok"], ok)
        self.assertEqual(
            {(d["slot"], d["source_opaque_in_footprint"])
             for d in ok["source_obj_opaque_by_oam_footprint"]
             if d["viewport"] == "top"},
            {(98, 1), (99, 0)}
        )
        self.assertEqual(ok["outside_source_visible_oam_pixel_samples"], [])
        paint(hd, 4, 192, 44)
        bad = audit(
            stock, bytes(hd), shifted, 1220, second_original=stock,
            source_obj_layer=pam + source
        )
        self.assertFalse(bad["ok"], bad)
        # The phantom is inside a registered OAM box; the old generic
        # confinement test would have accepted the exact same screen.
        self.assertEqual(bad["outside_live_oam_pixel_samples"], [])
        self.assertEqual(
            bad["outside_source_visible_oam_pixel_samples"], [[768, 176, 192, 44]]
        )

    def test_same_viewport_source_discriminator_handles_wrap_and_1x(self):
        stock, hd = frames(scale=1)
        pam = (
            b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
            b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
        )
        source = bytearray(W * H * 4)
        source[(2 * W + 125) * 4 + 3] = 255
        # Raw Y=250 wraps to screen Y=2. Keep P2's top bounding box
        # disjoint in X and make its purported HD rider fail at 1x too.
        lines = draw_log(top_y=250).splitlines()
        shifted = "\n".join(
            line.replace("slot=99 x=104", "slot=99 x=190") for line in lines
        )
        paint(hd, 1, 125, 2)
        self.assertTrue(audit(
            stock, bytes(hd), shifted, 1220, source_obj_layer=pam + source
        )["ok"])
        paint(hd, 1, 192, 3)
        result = audit(
            stock, bytes(hd), shifted, 1220, source_obj_layer=pam + source
        )
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["outside_source_visible_oam_pixel_samples"], [[192, 3, 192, 3]]
        )

    def test_single_pixel_hud_or_world_corruption_fails_even_at_4x(self):
        stock, hd = frames()
        paint(hd, 4, 125, 42)
        paint(hd, 4, 125, 155)
        paint(hd, 4, 10, 10)
        report = audit(stock, bytes(hd), draw_log(), 1220)
        self.assertFalse(report["ok"])
        self.assertEqual(report["outside_live_oam_pixel_samples"][0], [40, 40, 10, 10])

    def test_capture_only_allows_fully_occluded_original_bottom_racer(self):
        stock, only = frames()
        paint(only, 4, 125, 42)
        ordinary = audit(stock, bytes(only), draw_log(), 1220,
                         second_original=stock)
        self.assertFalse(ordinary["ok"])
        removal = audit(stock, bytes(only), draw_log(), 1220,
                        second_original=stock, capture_only=True)
        self.assertTrue(removal["ok"])
        self.assertEqual(removal["viewports_with_visible_changes"], ["top"])
        self.assertEqual(removal["bottom_changed_pixels"], 0)
        self.assertTrue(removal["diagnostic_capture_only"])

    def test_capture_only_does_not_accept_inert_or_outside_corruption(self):
        stock, only = frames()
        self.assertFalse(audit(stock, bytes(only), draw_log(), 1220,
                               capture_only=True)["ok"])
        paint(only, 4, 125, 42)
        paint(only, 4, 10, 10)
        result = audit(stock, bytes(only), draw_log(), 1220,
                       capture_only=True)
        self.assertFalse(result["ok"])
        self.assertTrue(result["outside_live_oam_pixel_samples"])

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

"""Independent proof that real P1 4x raster edits never leave live OAM slots."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_1p_hd_placement import assess, changed_pixels, in_original_slot


def pam(w, h, raw):
    return (
        f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\nENDHDR\n"
    ).encode() + raw


class OnePlayerHdPlacementTests(unittest.TestCase):
    def test_wrapped_source_slot_and_half_screen(self):
        self.assertTrue(in_original_slot(115, 120, (96, 96, 97), "bottom"))
        self.assertFalse(in_original_slot(25, 120, (96, 96, 97), "bottom"))
        self.assertFalse(in_original_slot(115, 70, (96, 96, 97), "bottom"))
        self.assertTrue(in_original_slot(50, 2, (40, 250, 98), "top"))
        self.assertFalse(in_original_slot(50, 200, (40, 250, 98), "top"))
        self.assertFalse(in_original_slot(0, 2, (-80, 250, 98), "top"))

    def test_real_pam_requires_source_local_placement_and_admitted_guest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = bytes((30, 80, 170, 255)) * (256 * 224)
            dense = bytearray(bytes((30, 80, 170, 255)) * (1024 * 896))
            y, x = 480, 460  # source (115,120), inside P1 bottom slot x96 y96
            dense[(y * 1024 + x) * 4] ^= 1
            (root / "ur-baldosa-hd-postcapture-underlay-001728.pam").write_bytes(
                pam(256, 224, raw))
            image = root / "ur-baldosa-frame-001728.pam"
            image.write_bytes(pam(1024, 896, bytes(dense)))
            common = (
                "UR_BALDOSA_HD_PPU_UNDERLAY frame=1728 saved=1 "
                "logical=256x224 type=post-obj-removal\n"
                "UR_RACER_HD_CENSUS frame=1728 phase=present "
                "status=hd reason=p1-only\n"
                "UR_RACER_HD_SOURCE_OBJ frame=1728 top_opaque=0 "
                "bottom_opaque=315 top_painted=0 bottom_painted=1\n"
                "UR_RACER_HD_P1_ONLY frame=1728 slots=97-98 p2_stock=1 "
                "bottom_nonoverlap=1\\n"
                "UR_RACER_HD_DRAW PASS frame=1728 semantic=0439 "
                "viewport=top slot=98 x=97 y=112 hflip=1 vflip=0 "
                "density=4 output_scale=4 guest_state_unchanged=1\n"
                "UR_RACER_HD_DRAW PASS frame=1728 semantic=0439 "
                "viewport=bottom slot=97 x=96 y=96 hflip=1 vflip=0 "
                "density=4 output_scale=4 guest_state_unchanged=1\n"
            )
            log = root / "log.txt"
            log.write_text(common +
                "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                "pitch=4096 top_changed=0 bottom_changed=1\n")
            cov = root / "coverage.json"
            cov.write_text(json.dumps({
                "native_guest_crc_equal": 5447,
                "unsafe_fixture_used": False,
                "widescreen_hd_approved": False,
                "verified_4x_p1_visible_image_frames": [1728],
            }))
            report = assess(root, log, cov)
            self.assertEqual(report["status"],
                             "native-fixed-1p-authored-source-footprint-contained")
            self.assertEqual(report["frames"][0]["actual_changed_top_bottom"], [0, 1])
            self.assertEqual(report["frames"][0]["changed_native_4x_bbox_bottom"],
                             [460, 480, 460, 480])
            self.assertFalse(report["original_final_bg_priority_accepted"])
            self.assertFalse(report["wide_hd_accepted"])

            # Same bottom viewport is not enough: a pixel beyond the
            # admitted 64x64 actual OAM rectangle is a compositing defect.
            dense[(y * 1024 + x) * 4] ^= 1
            x2 = 99
            dense[(y * 1024 + x2) * 4] ^= 1
            image.write_bytes(pam(1024, 896, bytes(dense)))
            with self.assertRaisesRegex(ValueError, "outside"):
                assess(root, log, cov)

            # Native source absence rejects a phantom, even when fake
            # OAM placement could geometrically cover its screen region.
            dense[(y * 1024 + x2) * 4] ^= 1
            dense[(10 * 1024 + 450) * 4] ^= 1
            image.write_bytes(pam(1024, 896, bytes(dense)))
            log.write_text(common.replace("top_opaque=0", "top_opaque=0") +
                "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                "pitch=4096 top_changed=1 bottom_changed=0\n")
            with self.assertRaisesRegex(ValueError, "source-empty"):
                assess(root, log, cov)

            log.write_text(common.replace("slot=97 x=96", "slot=97 x=64") +
                "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                "pitch=4096 top_changed=0 bottom_changed=1\n")
            image.write_bytes(pam(1024, 896, bytes(dense)))
            with self.assertRaisesRegex(ValueError, "source-empty"):
                assess(root, log, cov)

            log.write_text(common +
                "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                "pitch=4096 top_changed=0 bottom_changed=1\n")
            image.write_bytes(pam(1024, 896, bytes(dense[:])))
            cov.write_text(json.dumps({
                "native_guest_crc_equal": 5446,
                "unsafe_fixture_used": False,
                "widescreen_hd_approved": False,
                "verified_4x_p1_visible_image_frames": [1728],
            }))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(root, log, cov)


if __name__ == "__main__":
    unittest.main()

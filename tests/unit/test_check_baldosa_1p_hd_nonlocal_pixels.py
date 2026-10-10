"""Native 1P authored-raster proof must preserve empty PPU/OBJ source bands."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_1p_hd_nonlocal_pixels import assess, differing_bands


def pam(w, h, data):
    return (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n"
            f"TUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + data


class OnePlayerHdUnderlayTests(unittest.TestCase):
    def test_actual_4x_pixels_preserve_source_absent_half(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock = bytes((19, 42, 84, 0)) * (256 * 224)
            dense = bytearray(bytes((19, 42, 84, 0)) * (1024 * 896))
            changed = (600 * 1024 + 91) * 4
            dense[changed] ^= 1
            self.assertEqual(differing_bands(stock, bytes(dense)), (0, 1))
            base = root / "ur-baldosa-hd-postcapture-underlay-001728.pam"
            image = root / "ur-baldosa-frame-001728.pam"
            log = root / "guest.log"
            base.write_bytes(pam(256, 224, stock))
            image.write_bytes(pam(1024, 896, bytes(dense)))
            common = (
                "UR_BALDOSA_HD_PPU_UNDERLAY frame=1728 saved=1 "
                "logical=256x224 type=post-obj-removal\n"
                "UR_RACER_HD_CENSUS frame=1728 phase=present "
                "status=hd reason=p1-only\n"
                "UR_RACER_HD_SOURCE_OBJ frame=1728 top_opaque=0 "
                "bottom_opaque=315 top_painted=0 bottom_painted=1\n"
            )
            log.write_text(common +
                           "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                           "pitch=4096 top_changed=0 bottom_changed=1\n")
            result = assess(root, log)
            self.assertEqual(result["status"], "observed-guarded-1p-source-positive-hd")
            self.assertEqual(result["native_early_frame_pairs"][0]["bottom_hd_changed_pixels"], 1)
            self.assertFalse(result["authored_wide_hd_admitted"])
            self.assertFalse(result["original_stock_priority_proven"])
            dense[0] ^= 1
            image.write_bytes(pam(1024, 896, bytes(dense)))
            log.write_text(common +
                           "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                           "pitch=4096 top_changed=1 bottom_changed=1\n")
            with self.assertRaisesRegex(ValueError, "phantom"):
                assess(root, log)
            dense[0] ^= 1
            image.write_bytes(pam(1024, 896, bytes(dense)))
            log.write_text(common +
                           "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                           "pitch=4096 top_changed=2 bottom_changed=1\n")
            with self.assertRaisesRegex(ValueError, "differs"):
                assess(root, log)
            log.write_text(common.replace("saved=1", "saved=0") +
                           "UR_BALDOSA_NATIVE_PAINT frame=1728 raster=1024x896 "
                           "pitch=4096 top_changed=0 bottom_changed=1\n")
            with self.assertRaisesRegex(ValueError, "underlay"):
                assess(root, log)


if __name__ == "__main__":
    unittest.main()

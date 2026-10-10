"""Adversarial 256-center versus authentic 342-wide native PPU attribution."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_original_center_parity import assess


def pam(w, h, rgba):
    return (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n"
            "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + rgba


class BaldosaOriginalCenterParityTests(unittest.TestCase):
    def test_exact_center_both_players_and_adversarial_nonzero_hud(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixed = root / "ur-baldosa-original-source-001856.pam"
            wide = root / "ur-baldosa-ws342-001856.pam"
            original_crc = root / "fixed-crc.txt"
            expanded_crc = root / "wide-crc.txt"
            crc = b"01234567\n" * 2473
            original_crc.write_bytes(crc)
            expanded_crc.write_bytes(crc)
            stock = bytes((10, 20, 30, 0)) * (256 * 224)
            wide_pixels = bytearray(bytes((77, 88, 99, 0)) * (342 * 224))
            for y in range(224):
                a = (y * 342 + 43) * 4
                b = y * 256 * 4
                wide_pixels[a:a + 256 * 4] = stock[b:b + 256 * 4]
            fixed.write_bytes(pam(256, 224, stock))
            wide.write_bytes(pam(342, 224, wide_pixels))
            exact = assess(fixed, wide, original_crc, expanded_crc, 1856)
            self.assertEqual(exact["status"], "center-exact")
            self.assertEqual(exact["total_center_changed_pixels"], 0)
            self.assertTrue(exact["same_complete_guest_crc"])
            self.assertFalse(exact["release_hud_parity_admitted"])
            self.assertFalse(exact["hd_sprite_replacement_admitted"])

            # Newly exposed margin colours are irrelevant to the source
            # centre. One HUD-like upper-band and one lower-rider error
            # must appear independently in top/bottom telemetry.
            for x, y in ((30, 5), (152, 177)):
                wide_pixels[(y * 342 + x + 43) * 4] ^= 1
            wide.write_bytes(pam(342, 224, wide_pixels))
            changed = assess(fixed, wide, original_crc, expanded_crc, 1856)
            self.assertEqual(changed["status"], "center-delta-observed")
            self.assertEqual(changed["top_center_changed_pixels"], 1)
            self.assertEqual(changed["bottom_center_changed_pixels"], 1)
            self.assertEqual(changed["changed_rows"], {"5": 1, "177": 1})
            self.assertEqual(changed["bounded_pixel_examples"][0]["wide_xy"],
                             [73, 5])
            self.assertFalse(changed["release_hud_parity_admitted"])
            self.assertFalse(changed["hd_sprite_replacement_admitted"])

            # A convincing screenshot cannot substitute for exact
            # independent guest CRC or same-frame native provenance.
            expanded_crc.write_bytes(crc.replace(b"01234567", b"99999999", 1))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(fixed, wide, original_crc, expanded_crc, 1856)
            expanded_crc.write_bytes(crc)
            with self.assertRaisesRegex(ValueError, "guest frame"):
                assess(fixed, wide, original_crc, expanded_crc, 1872)
            wide.write_bytes(pam(341, 224, wide_pixels))
            with self.assertRaises(ValueError):
                assess(fixed, wide, original_crc, expanded_crc, 1856)

    def test_source_capture_stages_second_frame_without_a_new_guest_route(self):
        source = (Path(__file__).resolve().parents[2] /
                  "tools/baldosa_native_racer_presentation.cpp").read_text()
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/baldosa-core-spike.yml").read_text()
        self.assertIn('std::getenv("UR_BALDOSA_FIXED_ORIGINAL_SOURCE_EXTRA_FRAME")', source)
        self.assertIn('export UR_BALDOSA_FIXED_ORIGINAL_SOURCE_EXTRA_FRAME=1856', workflow)
        self.assertIn('check_baldosa_original_center_parity.py', workflow)
        self.assertIn("ws342_original_center_parity_1856.json", workflow)


if __name__ == "__main__":
    unittest.main()

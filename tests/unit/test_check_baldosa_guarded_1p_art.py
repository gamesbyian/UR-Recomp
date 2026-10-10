"""1P Remastered guest/present coverage must use authentic complete native controls."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_guarded_1p_art import assess


class GuardedOnePlayerTests(unittest.TestCase):
    def test_scope_real_host_and_native_fourfold_art_separately(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock, candidate = root / "stock.crc", root / "candidate.crc"
            log, frames = root / "native.log", root / "captures"
            stock.write_bytes(b"12345678\n" * 501)
            candidate.write_bytes(stock.read_bytes())
            frames.mkdir()
            gate = [
                "UR_RACER_HD_CENSUS frame={} phase=gate status={} reason={}\n".format(
                    f, "armed" if f == 330 else "original",
                    "p1-only" if f == 330 else "p1-selection-or-art")
                for f in range(101, 502)
            ]
            trace = (
                "script f=100 until 00E1F ok after 300 frames\n"
                + "".join(gate)
                + "UR_RACER_HD_CENSUS frame=330 phase=present status=hd reason=p1-only\n"
                "UR_RACER_HD_CENSUS frame=420 phase=present status=original reason=not-armed\n"
                "UR_RACER_HD_PIXEL_CHANGE frame=330 source_instances=2 changed_from_underlay=1\n"
                "UR_BALDOSA_NATIVE_PAINT frame=330 raster=1024x896 pitch=4096 top_changed=44 bottom_changed=0\n"
                "script f=501 dump end ok\n"
            )
            log.write_text(trace)
            screenshot = frames / "ur-baldosa-frame-000330.pam"
            pixels = bytes((18, 44, 140, 255)) * (1024 * 896)
            screenshot.write_bytes(
                b"P7\nWIDTH 1024\nHEIGHT 896\nDEPTH 4\nMAXVAL 255\n"
                b"TUPLTYPE RGB_ALPHA\nENDHDR\n" + pixels
            )
            report = assess(stock, candidate, log, frames)
            self.assertEqual(report["status"], "guarded-1p-real-art-observed")
            self.assertEqual(report["native_guest_crc_equal"], 501)
            self.assertEqual(report["race_host_presents_observed"], 2)
            self.assertEqual(report["verified_4x_p1_visible_image_frames"], [330])
            self.assertFalse(report["widescreen_hd_approved"])
            self.assertFalse(report["product_beta_approved"])
            screenshot.unlink()
            report = assess(stock, candidate, log, frames)
            self.assertEqual(report["status"], "guarded-1p-real-art-unproven")
            self.assertEqual(report["race_hd_host_presents"], 1)
            screenshot.write_bytes(
                b"P7\nWIDTH 1023\nHEIGHT 896\nDEPTH 4\nMAXVAL 255\n"
                b"TUPLTYPE RGB_ALPHA\nENDHDR\n" + pixels
            )
            with self.assertRaises(ValueError):
                assess(stock, candidate, log, frames)
            screenshot.unlink()
            candidate.write_bytes(stock.read_bytes().replace(b"12345678", b"87654321", 1))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(stock, candidate, log, frames)
            candidate.write_bytes(stock.read_bytes())
            log.write_text(trace + "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE enabled=1\n")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                assess(stock, candidate, log, frames)
            log.write_text(trace.replace("script f=501 dump end ok", ""))
            with self.assertRaisesRegex(ValueError, "terminal"):
                assess(stock, candidate, log, frames)


if __name__ == "__main__":
    unittest.main()

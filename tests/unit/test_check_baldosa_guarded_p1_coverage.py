"""Actual guarded 2P P1-only source-art evidence never borrows unsafe fixtures."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_guarded_p1_coverage import assess


class GuardedP1CoverageTests(unittest.TestCase):
    def test_sparse_host_art_must_be_native_4x_after_real_go(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock, trial, log, captures = (
                root / "stock.crc", root / "trial.crc",
                root / "trial.log", root / "captures",
            )
            stock.write_bytes(b"ABC12345\n" * 2473)
            trial.write_bytes(stock.read_bytes())
            captures.mkdir()
            gates = [
                f"UR_RACER_HD_CENSUS frame={f} phase=gate "
                f"status={'armed' if f == 2208 else 'original'} "
                f"reason={'p1-only' if f == 2208 else 'p2-pair-gate'}\n"
                for f in range(1, 2474)
            ]
            log.write_text(
                "script f=1989 dump go ok\n" + "".join(gates) +
                "UR_RACER_HD_CENSUS frame=2208 phase=present status=hd reason=p1-only\n"
                "UR_RACER_HD_PIXEL_CHANGE frame=2208 source_instances=2 changed_from_underlay=1\n"
                "UR_BALDOSA_NATIVE_PAINT frame=2208 raster=1024x896 pitch=4096 "
                "top_changed=27 bottom_changed=15\n"
            )
            image = captures / "ur-baldosa-frame-002208.pam"
            raw = (b"P7\nWIDTH 1024\nHEIGHT 896\nDEPTH 4\nMAXVAL 255\n"
                   b"TUPLTYPE RGB_ALPHA\nENDHDR\n" +
                   bytes((25, 120, 70, 255)) * (1024 * 896))
            image.write_bytes(raw)
            result = assess(stock, trial, log, captures)
            self.assertEqual(result["status"], "guarded-p1-host-art-observed")
            self.assertEqual(result["scripted_go_guest_frame"], 1989)
            self.assertEqual(result["post_go_p1_armed_guest_frames"], 1)
            self.assertEqual(result["post_go_p1_hd_presented_guest_frames"], 1)
            self.assertEqual(result["post_go_p1_host_pixel_change_witness_frames"], [2208])
            self.assertEqual(len(result["native_authored_4x_captures"]), 1)
            self.assertFalse(result["release_hd_admission"])
            self.assertFalse(result["production_player_appearance_accepted"])
            self.assertFalse(result["p2_stock_occlusion_parity_proven"])

            image.unlink()
            self.assertEqual(
                assess(stock, trial, log, captures)["status"],
                "guarded-p1-host-art-unproven",
            )
            image.write_bytes(raw)
            log.write_text(log.read_text() +
                           "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE enabled=1\n")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                assess(stock, trial, log, captures)
            log.write_text(log.read_text().replace(
                "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE enabled=1\n", ""))
            trial.write_bytes(stock.read_bytes().replace(b"ABC12345", b"ABC12346", 1))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(stock, trial, log, captures)
            trial.write_bytes(stock.read_bytes())
            image.write_bytes(raw.replace(b"WIDTH 1024", b"WIDTH 1023", 1))
            with self.assertRaises(ValueError):
                assess(stock, trial, log, captures)
            image.write_bytes(raw)
            log.write_text(log.read_text().replace(
                "script f=1989 dump go ok", "script f=1989 dump unknown ok"))
            with self.assertRaisesRegex(ValueError, "GO"):
                assess(stock, trial, log, captures)


if __name__ == "__main__":
    unittest.main()

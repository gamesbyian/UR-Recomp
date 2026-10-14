import tempfile
import unittest
from pathlib import Path

from tools.check_split_sprite_rip_margin import (
    OAM_HIGH, OAM_LOW, RIP_BYTE, check, scan_frame,
)


def wram(rip=0xA5, sprites=None) -> bytes:
    w = bytearray(0x20000)
    w[OAM_HIGH + RIP_BYTE] = rip
    for i in range(96, 100):
        w[OAM_LOW + i * 4] = 0
        w[OAM_LOW + i * 4 + 1] = 0xE0  # parked on lines 224-255: never visible
    for sprite, (x, y) in (sprites or {}).items():
        w[OAM_LOW + sprite * 4] = x
        w[OAM_LOW + sprite * 4 + 1] = y
    return bytes(w)


class SplitSpriteRipMarginTests(unittest.TestCase):
    def test_non_split_frame_is_ignored(self):
        self.assertIsNone(scan_frame(wram(rip=0x55), 43))

    def test_hidden_copy_band_and_clearance(self):
        # Sprite 97 at (48,48) lies in the top band, where the rip hides it.
        items = scan_frame(wram(sprites={97: (48, 48)}), 43)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["sprite"], 97)
        self.assertEqual(items[0]["right_edge"], 48 - 256 + 32)
        self.assertEqual(items[0]["leaks"], 0)
        # The same sprite in the bottom band is shown, not hidden.
        self.assertEqual(scan_frame(wram(sprites={97: (48, 150)}), 43), [])

    def test_leak_threshold(self):
        # Right edge -43 touches the margin edge only; -42 enters it.
        self.assertEqual(scan_frame(wram(sprites={99: (181, 120)}), 43)[0]["leaks"], 0)
        self.assertEqual(scan_frame(wram(sprites={99: (182, 120)}), 43)[0]["leaks"], 1)


    def test_shadow_geometry_never_qualifies_final_PPU_obj_or_HD(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "frame_000010_wram.bin").write_bytes(
                wram(sprites={97: (48, 48)}))
            result = check("bounded source", root, 43, 1)
            self.assertEqual(result["outcome"], "accepted")
            metrics = result["metrics"]
            self.assertEqual(
                metrics["source_basis"],
                "WRAM high-OAM shadow and synthetic physical-rip geometry")
            self.assertFalse(metrics["actual_live_PPU_OAM_HDMA_state_observed"])
            self.assertFalse(metrics["final_PPU_visible_sprite_pixels_checked"])
            self.assertFalse(metrics["authorizes_widescreen_HD_sprite_admission"])

    def test_corrupt_or_partial_WRAM_rejected_before_potential_leak(self):
        for data in (b"", wram()[:-1], wram() + b"\x00"):
            with self.subTest(size=len(data)):
                with self.assertRaisesRegex(ValueError, "complete 128 KiB"):
                    scan_frame(data, 43)

    def test_invalid_or_adversarial_margin_rejected(self):
        for invalid in (-1, 129, 1000):
            with self.subTest(margin=invalid):
                with self.assertRaisesRegex(ValueError, "bounded"):
                    scan_frame(wram(), invalid)
                with self.assertRaisesRegex(ValueError, "bounded"):
                    check("bounded source", Path("/missing"), invalid, 1)
        with self.assertRaisesRegex(ValueError, "at least one"):
            check("bounded source", Path("/missing"), 43, 0)

    def test_frame_name_forgery_rejected_instead_of_counting_fake_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "frame_000010_wram.bin").write_bytes(wram(sprites={97: (48, 48)}))
            (root / "frame_000010_alias_wram.bin").write_bytes(
                wram(sprites={97: (48, 48)}))
            with self.assertRaisesRegex(ValueError, "exact six-digit"):
                check("bounded source", root, 43, 2)

    def test_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "frame_000010_wram.bin").write_bytes(wram(sprites={97: (48, 48)}))
            (root / "frame_000011_wram.bin").write_bytes(wram(rip=0x55))
            env = check("r", root, 43, 1)
            self.assertEqual(env["outcome"], "accepted")
            self.assertEqual(env["metrics"]["split_frames"], 1)
            self.assertEqual(env["metrics"]["clearance_px"], -43 - (48 - 256 + 32))
            self.assertEqual(check("r", root, 43, 2)["outcome"], "rejected")
            (root / "frame_000012_wram.bin").write_bytes(wram(sprites={98: (200, 130)}))
            env = check("r", root, 43, 1)
            self.assertEqual(env["outcome"], "rejected")
            self.assertEqual(env["metrics"]["leaks"][0]["frame"], 12)


if __name__ == "__main__":
    unittest.main()

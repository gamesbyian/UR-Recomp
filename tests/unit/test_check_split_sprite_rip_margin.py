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

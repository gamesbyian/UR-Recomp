import tempfile
import unittest
from pathlib import Path

from tools.decode_uniracers_oam_split import (
    FIRST_SPRITE,
    TARGET_OAM_OFFSET,
    decode_high_oam_byte,
    inspect_oam,
)


class UniracersOamSplitTests(unittest.TestCase):
    def test_target_maps_to_sprites_96_through_99(self):
        self.assertEqual(TARGET_OAM_OFFSET, 0x218)
        self.assertEqual(FIRST_SPRITE, 96)

    def test_a5_and_5a_swap_high_x_and_size_pairs(self):
        a5 = decode_high_oam_byte(0xA5)
        v5a = decode_high_oam_byte(0x5A)
        self.assertEqual(
            [(r["x_msb"], r["size_select"]) for r in a5],
            [(1, 0), (1, 0), (0, 1), (0, 1)],
        )
        self.assertEqual(
            [(r["x_msb"], r["size_select"]) for r in v5a],
            [(0, 1), (0, 1), (1, 0), (1, 0)],
        )

    def test_snapshot_asserts_final_5a_target_byte(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "race.oam.bin"
            data = bytearray(544)
            data[0x218] = 0x5A
            path.write_bytes(data)
            row = inspect_oam(path, expected=0x5A)
            self.assertEqual(row["first_sprite"], 96)
            self.assertEqual(row["last_sprite"], 99)
            self.assertEqual(row["value_hex"], "0x5A")

    def test_wrong_target_value_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "race.oam.bin"
            path.write_bytes(bytes(544))
            with self.assertRaises(AssertionError):
                inspect_oam(path, expected=0x5A)


if __name__ == "__main__":
    unittest.main()

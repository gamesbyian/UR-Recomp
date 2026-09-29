from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import uniracers_state as us


class SignedWordTests(unittest.TestCase):
    def test_twos_complement_boundaries(self):
        self.assertEqual(us.s16(0x0000), 0)
        self.assertEqual(us.s16(0x7FFF), 32767)
        self.assertEqual(us.s16(0x8000), -32768)
        self.assertEqual(us.s16(0xFFFF), -1)

    def test_rejects_values_outside_u16(self):
        with self.assertRaises(ValueError):
            us.s16(-1)
        with self.assertRaises(ValueError):
            us.s16(0x10000)


class StateMapTests(unittest.TestCase):
    def test_player_pairs_do_not_alias(self):
        self.assertEqual(us.PLAYER1_FIELDS["air"].addr, 0x0545)
        self.assertEqual(us.PLAYER2_FIELDS["air"].addr, 0x0547)
        self.assertEqual(us.PLAYER1_FIELDS["pitch"].addr, 0x04C7)
        self.assertEqual(us.PLAYER2_FIELDS["pitch"].addr, 0x04C9)

    def test_historical_duplicate_keys_are_explicit(self):
        self.assertEqual(us.HISTORICAL_BOT_EFFECTIVE["air"].addr, 0x0545)
        self.assertEqual(us.HISTORICAL_BOT_OVERWRITTEN["air"].addr, 0x0547)
        self.assertEqual(us.HISTORICAL_BOT_EFFECTIVE["pitch_scratch"].addr, 0x0F49)
        self.assertEqual(us.HISTORICAL_BOT_OVERWRITTEN["pitch"].addr, 0x04C9)

    def test_signed_field_read_handles_0x8000(self):
        data = bytearray(0x20000)
        addr = us.PLAYER1_FIELDS["x_speed"].addr
        data[addr : addr + 2] = b"\x00\x80"
        self.assertEqual(us.read_field(data, us.PLAYER1_FIELDS["x_speed"]), -32768)

    def test_bounds_check(self):
        with self.assertRaises(ValueError):
            us.read_field(b"", us.Field("u8", 0, "test"))


if __name__ == "__main__":
    unittest.main()

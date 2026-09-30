from __future__ import annotations

import unittest

from tools.model_active_oam_cursor import (
    OAM_BYTES,
    active_oam_sprite_index,
    high_oam_byte,
)


def blank_oam() -> bytearray:
    data = bytearray(OAM_BYTES)
    # Park every sprite wholly offscreen-left (9-bit X=480, small size).
    for i in range(128):
        data[i * 4] = 0xE0
        data[i * 4 + 1] = 0xE0
        shift = 2 * (i & 3)
        data[0x200 + (i >> 2)] |= 1 << shift
    return data


def set_sprite(
    data: bytearray,
    index: int,
    *,
    x: int,
    y: int,
    large: bool = False,
) -> None:
    base = index * 4
    data[base] = x & 0xFF
    data[base + 1] = y & 0xFF
    high_index = 0x200 + (index >> 2)
    shift = 2 * (index & 3)
    data[high_index] &= ~(0x3 << shift)
    bits = ((x >> 8) & 1) | (2 if large else 0)
    data[high_index] |= bits << shift


class ActiveOamCursorTests(unittest.TestCase):
    def test_empty_line_preserves_last_fetched_sprite(self) -> None:
        oam = blank_oam()
        cursor, last = active_oam_sprite_index(
            oam,
            scanline=0,
            dot=283,
            size_select=4,
            last_fetched_index=99,
        )
        self.assertEqual(cursor, 99)
        self.assertEqual(last, 99)
        self.assertEqual(high_oam_byte(cursor), 0x218)

    def test_tile_fetch_walks_accepted_sprites_in_reverse_order(self) -> None:
        oam = blank_oam()
        # Size mode 4 small OBJ is 16x16 (two tiles). At dot 282 six tile
        # fetches have elapsed, enough to finish 99/98 and begin 97.
        for index in (97, 98, 99):
            set_sprite(oam, index, x=48, y=100)
        cursor, last = active_oam_sprite_index(
            oam,
            scanline=112,
            dot=282,
            size_select=4,
            last_fetched_index=12,
        )
        self.assertEqual(cursor, 97)
        self.assertEqual(last, 97)
        self.assertEqual(high_oam_byte(cursor), 0x218)

    def test_high_oam_target_separates_sprite_groups(self) -> None:
        self.assertEqual(high_oam_byte(96), 0x218)
        self.assertEqual(high_oam_byte(99), 0x218)
        self.assertEqual(high_oam_byte(64), 0x210)

    def test_mid_evaluation_reports_live_scan_cursor(self) -> None:
        oam = blank_oam()
        cursor, last = active_oam_sprite_index(
            oam,
            scanline=10,
            dot=20,
            size_select=0,
            last_fetched_index=77,
        )
        self.assertEqual(cursor, 10)
        self.assertEqual(last, 77)

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            active_oam_sprite_index(
                bytes(10),
                scanline=0,
                dot=100,
                size_select=0,
                last_fetched_index=0,
            )


if __name__ == "__main__":
    unittest.main()

import unittest

from tools.analyze_racer_piece_render_binding import (
    decode_4bpp_tile,
    decode_obsel,
    decode_oam_slot,
    find_direct_subrect_matches,
    object_tile_number,
)


class RacerPieceRenderBindingTests(unittest.TestCase):
    def test_obsel_83_is_16x16_64x64(self):
        row = decode_obsel(0x83)
        self.assertEqual(row["size_code"], 4)
        self.assertEqual(row["small_pixels"], [16, 16])
        self.assertEqual(row["large_pixels"], [64, 64])
        self.assertEqual(row["name_base_byte_address"], 0xC000)

    def test_oam_slot_decodes_high_x_and_size(self):
        oam = bytearray(544)
        slot = 99
        q = slot * 4
        oam[q:q+4] = bytes([0x68, 0x28, 0x88, 0x68])
        shift = (slot % 4) * 2
        oam[0x200 + slot // 4] |= 0b11 << shift
        row = decode_oam_slot(bytes(oam), slot, decode_obsel(0x83))
        self.assertEqual(row["x"], 0x168)
        self.assertTrue(row["large"])
        self.assertEqual(row["size_pixels"], [64, 64])
        self.assertEqual(row["tile_hex"], "0x88")
        self.assertTrue(row["hflip"])
        self.assertFalse(row["vflip"])

    def test_obj_subtile_numbering_uses_nibbles(self):
        self.assertEqual(object_tile_number(0x88, 2, 0), 0x8A)
        self.assertEqual(object_tile_number(0x88, 3, 1), 0x9B)
        self.assertEqual(object_tile_number(0x88, 4, 4), 0xCC)

    def test_4bpp_decoder_single_pixel(self):
        raw = bytearray(32)
        raw[0] = 0x80
        px = decode_4bpp_tile(bytes(raw))
        self.assertEqual(px[0][0], 1)
        self.assertEqual(sum(v != 0 for row in px for v in row), 1)

    def test_direct_subrect_match(self):
        big = [
            [False, False, False, False],
            [False, True, False, False],
            [False, False, True, False],
            [False, False, False, False],
        ]
        needle = [[True, False], [False, True]]
        self.assertEqual(
            find_direct_subrect_matches(big, needle),
            [{"x": 1, "y": 1, "width": 2, "height": 2}],
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from tools.analyze_racer_piece_render_binding import decode_obsel, decode_oam_slot


class RacerPieceRenderBindingTests(unittest.TestCase):
    def test_obsel_83_is_16x16_64x64(self):
        row = decode_obsel(0x83)
        self.assertEqual(row["size_code"], 4)
        self.assertEqual(row["small_pixels"], [16, 16])
        self.assertEqual(row["large_pixels"], [64, 64])

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


if __name__ == "__main__":
    unittest.main()

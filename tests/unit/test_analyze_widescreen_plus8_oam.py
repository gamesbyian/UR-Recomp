import unittest

from tools.analyze_widescreen_plus8_oam import decode_oam


class WidescreenPlus8OamTests(unittest.TestCase):
    def test_decode_oam_signed_x_and_size(self):
        blob = bytearray(0x220)
        blob[0:4] = bytes([0xFE, 0x20, 0x34, 0x56])
        blob[4:8] = bytes([0x05, 0x21, 0x35, 0x57])
        # slot 0: x-high=1, large=1. slot 1: neither.
        blob[0x200] = 0b00000011
        rows = decode_oam(bytes(blob))
        self.assertEqual(rows[0]["x"], -2)
        self.assertTrue(rows[0]["large"])
        self.assertEqual(rows[1]["x"], 5)
        self.assertFalse(rows[1]["large"])


if __name__ == "__main__":
    unittest.main()

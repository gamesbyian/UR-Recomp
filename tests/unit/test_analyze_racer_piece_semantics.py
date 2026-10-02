import unittest

from tools.analyze_racer_piece_semantics import set_bits


class RacerPieceSemanticsTests(unittest.TestCase):
    def test_set_bits_are_numbered_bytewise_lsb_first(self):
        self.assertEqual(set_bits(bytes.fromhex("01800040")), [0, 15, 30])

    def test_known_header_popcounts(self):
        for raw, expected in [
            ("70c31e30", 13),
            ("38c31c70", 13),
            ("38e71c70", 15),
            ("70c30e38", 13),
        ]:
            self.assertEqual(len(set_bits(bytes.fromhex(raw))), expected)


if __name__ == "__main__":
    unittest.main()

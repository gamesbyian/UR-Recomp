import unittest

from tools.scan_challenge_writer_entry import scan


class ChallengeWriterEntryScanTests(unittest.TestCase):
    def test_finds_jsr_and_jsl_into_bounded_neighborhood(self):
        rom = bytearray(0x20000)

        # 80:9000 JSR $E6A0.
        rom[0x1000:0x1003] = bytes((0x20, 0xA0, 0xE6))
        # 81:9000 JSL $80:E6B7.
        rom[0x9000:0x9004] = bytes((0x22, 0xB7, 0xE6, 0x80))
        # Outside the bounded target range.
        rom[0x1010:0x1013] = bytes((0x20, 0xC7, 0xE6))

        report = scan(bytes(rom), context=4)
        self.assertEqual(
            report["call_targets"],
            ["80:E6A0", "80:E6B7"],
        )
        self.assertEqual(len(report["calls"]), 2)
        self.assertEqual(report["calls"][0]["kind"], "JSR")
        self.assertEqual(report["calls"][1]["kind"], "JSL")

    def test_ignores_same_low_address_in_other_bank(self):
        rom = bytearray(0x20000)
        rom[0x1000:0x1004] = bytes((0x22, 0xB7, 0xE6, 0x81))
        report = scan(bytes(rom))
        self.assertEqual(report["call_targets"], [])
        self.assertEqual(report["calls"], [])


if __name__ == "__main__":
    unittest.main()

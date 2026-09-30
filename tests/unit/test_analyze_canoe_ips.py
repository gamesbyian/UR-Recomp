import unittest

from tools.analyze_canoe_ips import analyze, parse_ips


class CanoeIpsTests(unittest.TestCase):
    def test_literal_and_rle_records(self):
        patch = (
            b"PATCH"
            + bytes.fromhex("000010 0002 AA BB")
            + bytes.fromhex("000020 0000 0003 CC")
            + b"EOF"
        )
        rows = parse_ips(patch)
        self.assertEqual(rows[0]["data_hex"], "aa bb")
        self.assertEqual(rows[1]["data_hex"], "cc cc cc")

    def test_optional_rom_comparison_and_lorom_mapping(self):
        patch = b"PATCH" + bytes.fromhex("01534C 0002 22 00") + b"EOF"
        rom = bytearray(0x200000)
        rom[0x1534C:0x1534E] = b"\x12\x34"
        report = analyze(patch, bytes(rom))
        row = report["records"][0]
        self.assertEqual(row["lorom_cpu"], "02:D34C")
        self.assertEqual(row["original_hex"], "12 34")

    def test_rejects_trailing_bytes(self):
        with self.assertRaises(ValueError):
            parse_ips(b"PATCHEOFx")


if __name__ == "__main__":
    unittest.main()

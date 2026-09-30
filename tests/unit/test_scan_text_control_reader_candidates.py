import unittest

from tools.scan_text_control_reader_candidates import analyze, scan_cmp_sites


class TextControlReaderScanTests(unittest.TestCase):
    def test_clusters_multiple_control_compares(self):
        rom = bytearray(bytes([0]) * 0x200)
        rom[0x40:0x42] = bytes([0xC9, 0xFC])
        rom[0x60:0x62] = bytes([0xC9, 0xFF])
        rom[0x80:0x82] = bytes([0xC9, 0xF3])
        report = analyze(bytes(rom), radius=64)
        self.assertEqual(report["cmp_site_count"], 3)
        self.assertGreaterEqual(len(report["clusters"]), 1)
        top = report["clusters"][0]
        self.assertGreaterEqual(top["unique_control_count"], 2)

    def test_ignores_other_immediates(self):
        rom = bytes([0xC9, 0x10, 0xC9, 0xFC])
        sites = scan_cmp_sites(rom)
        self.assertEqual([row["value_hex"] for row in sites], ["0xFC"])


if __name__ == "__main__":
    unittest.main()

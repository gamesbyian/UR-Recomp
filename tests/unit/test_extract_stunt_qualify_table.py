import unittest

from tools.extract_stunt_qualify_table import extract


class StuntQualifyTableTests(unittest.TestCase):
    def test_extracts_eight_rows_three_generations(self):
        rom = bytearray(0x20000)
        start = 3 * 0x8000 + 0x2218
        values = list(range(1, 25))
        payload = b"".join(v.to_bytes(2, "little") for v in values)
        rom[start:start + len(payload)] = payload
        report = extract(bytes(rom))
        self.assertEqual(len(report["ordinary_tours"]), 8)
        self.assertEqual(
            report["ordinary_tours"][0]["thresholds"],
            {"bronze": 1, "silver": 2, "gold": 3},
        )
        self.assertEqual(
            report["ordinary_tours"][7]["thresholds"],
            {"bronze": 22, "silver": 23, "gold": 24},
        )


if __name__ == "__main__":
    unittest.main()

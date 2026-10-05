import unittest

from tools.scan_qualification_generation_refs import scan


class QualificationGenerationRefScanTests(unittest.TestCase):
    def test_reports_direct_generation_consumer_call(self):
        rom = bytearray(0x20000)
        # 83:8700 maps to offset 0x018700.
        off = 3 * 0x8000 + 0x0700
        rom[off:off + 4] = bytes((0x22, 0x15, 0xB3, 0x80))
        report = scan(bytes(rom))
        self.assertEqual(len(report["direct_calls_to_known_generation_consumers"]), 1)
        self.assertEqual(
            report["direct_calls_to_known_generation_consumers"][0]["target_cpu"],
            "80:B315")

    def test_reports_direct_snapshot_operand(self):
        rom = bytearray(0x20000)
        off = 3 * 0x8000 + 0x0700
        rom[off:off + 4] = bytes((0xAF, 0xD1, 0x10, 0x77))
        report = scan(bytes(rom))
        self.assertEqual(len(report["direct_10d1_operands_in_result_window"]), 1)


if __name__ == "__main__":
    unittest.main()

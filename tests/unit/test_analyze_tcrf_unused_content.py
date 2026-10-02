from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_tcrf_unused_content as tcrf


class TcrfUnusedContentTests(unittest.TestCase):
    def test_lorom_mapping(self) -> None:
        self.assertEqual(tcrf.lorom_to_file(0x83, 0x8000), 0x18000)
        self.assertEqual(tcrf.lorom_to_file(0x80, 0x8000), 0)
        with self.assertRaises(ValueError):
            tcrf.lorom_to_file(0x83, 0x7FFF)

    def test_ascii_runs(self) -> None:
        rows = tcrf.ascii_runs(b"\x00HELLO\x01ABCD\x00xy")
        self.assertEqual([row["text"] for row in rows], ["HELLO", "ABCD"])

    def test_synthetic_report(self) -> None:
        rom = bytearray(tcrf.ROM_SIZE)
        rom[tcrf.VERSION_OFFSET:tcrf.VERSION_OFFSET + 12] = b"ASJIver3.30\x00"
        rom[tcrf.BUILD_DATE_OFFSET:tcrf.BUILD_DATE_OFFSET + 10] = b"1994-11-29"
        report = tcrf.analyze(bytes(rom))
        self.assertTrue(report["claims"]["bank_83_8000_mapping"]["matches_reported_version_offset"])
        self.assertTrue(report["claims"]["version_string"]["starts_with_ASJIver3_30"])
        self.assertEqual(report["claims"]["version_string"]["decoded"], "ASJIver3.30")
        self.assertIn(
            "1994-11-29",
            [r["text"] for r in report["claims"]["build_date_area"]["window"]["ascii_runs"]],
        )


if __name__ == "__main__":
    unittest.main()

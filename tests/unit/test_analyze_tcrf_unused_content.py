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

    def test_file_to_lorom(self) -> None:
        self.assertEqual(tcrf.file_to_lorom(0x18000), (0x83, 0x8000))
        self.assertEqual(tcrf.file_to_lorom(0x0BD679), (0x97, 0xD679))

    def test_ascii_runs(self) -> None:
        rows = tcrf.ascii_runs(b"\x00HELLO\x01ABCD\x00xy")
        self.assertEqual([row["text"] for row in rows], ["HELLO", "ABCD"])

    def test_synthetic_report(self) -> None:
        rom = bytearray(tcrf.ROM_SIZE)
        rom[tcrf.VERSION_OFFSET:tcrf.VERSION_OFFSET + 12] = b"ASJIver3.30\x00"
        rom[tcrf.BUILD_DATE_OFFSET:tcrf.BUILD_DATE_OFFSET + 10] = b"1994-11-29"
        first = tcrf.COMBO_SET_OFFSET - (tcrf.COMBO_SET_COUNT - 1) * tcrf.COMBO_SET_SIZE
        for set_index in range(tcrf.COMBO_SET_COUNT):
            base = first + set_index * tcrf.COMBO_SET_SIZE
            for message_index in range(tcrf.COMBO_MESSAGE_COUNT):
                label = f"S{set_index + 1:02}M{message_index + 1:02}".ljust(tcrf.COMBO_MESSAGE_SIZE)
                rom[base + message_index * tcrf.COMBO_MESSAGE_SIZE:base + (message_index + 1) * tcrf.COMBO_MESSAGE_SIZE] = label.encode("ascii")
        report = tcrf.analyze(bytes(rom))
        self.assertTrue(report["claims"]["bank_83_8000_mapping"]["matches_reported_version_offset"])
        self.assertTrue(report["claims"]["version_string"]["starts_with_ASJIver3_30"])
        self.assertEqual(report["claims"]["version_string"]["decoded"], "ASJIver3.30")
        self.assertIn(
            "1994-11-29",
            [r["text"] for r in report["claims"]["build_date_area"]["window"]["ascii_runs"]],
        )
        combo = report["claims"]["unused_combo_message_set_9"]
        self.assertTrue(combo["reported_offset_begins_printable_message_text"])
        self.assertEqual(combo["cpu_address"], "97:D679")


if __name__ == "__main__":
    unittest.main()

"""Unmasked original/native Zoo WRAM diagnostic contract (synthetic only)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as probe


class FullWramByteAuditTests(unittest.TestCase):
    def test_equal_complete_images_are_byte_exact_without_release_admission(self):
        same = bytes(0x20000)
        report = probe.audit_qa01_wram_pair(same, same)
        self.assertTrue(report["byte_exact"])
        self.assertTrue(report["every_byte_compared"])
        self.assertEqual(report["excluded_byte_count"], 0)
        self.assertEqual(report["differing_byte_count"], 0)
        self.assertEqual(report["first_24_differences"], [])
        self.assertEqual(report["changed_256_byte_pages"], [])
        self.assertIsNone(report["first_differing_address"])
        self.assertFalse(report["cpu_or_logic_tick_parity_proven"])
        self.assertEqual(report["release_complete_event_credit"], 0)

    def test_real_address_ranges_and_all_changed_page_counts(self):
        original = bytearray(0x20000)
        native = bytearray(original)
        for offset, value in ((0x01DD, 0x04), (0x1199, 0x42),
                              (0x101DD, 0x40), (0x1FFFF, 0xFF)):
            native[offset] = value
        report = probe.audit_qa01_wram_pair(bytes(original), bytes(native))
        self.assertEqual(report["differing_byte_count"], 4)
        self.assertFalse(report["byte_exact"])
        self.assertEqual(report["first_differing_address"], "7E:01DD")
        self.assertEqual(report["last_differing_address"], "7F:FFFF")
        self.assertEqual(
            [d["snes_address"] for d in report["first_24_differences"]],
            ["7E:01DD", "7E:1199", "7F:01DD", "7F:FFFF"])
        self.assertEqual(
            [d["page_start"] for d in report["changed_256_byte_pages"]],
            ["7E:0100", "7E:1100", "7F:0100", "7F:FF00"])
        self.assertEqual(
            [d["differing_bytes"] for d in report["changed_256_byte_pages"]],
            [1, 1, 1, 1])
        self.assertNotEqual(report["original_wram_sha256"],
                            report["native_wram_sha256"])
        self.assertFalse(report["cpu_or_logic_tick_parity_proven"])
        self.assertEqual(report["release_complete_event_credit"], 0)

    def test_first_24_truncation_never_truncates_full_count(self):
        original = bytes(0x20000)
        native = bytearray(original)
        native[:4096] = bytes([0xAB]) * 4096
        report = probe.audit_qa01_wram_pair(original, bytes(native))
        self.assertEqual(report["differing_byte_count"], 4096)
        self.assertEqual(len(report["first_24_differences"]), 24)
        self.assertEqual(len(report["changed_256_byte_pages"]), 16)
        self.assertEqual(sum(x["differing_bytes"] for x in
                             report["changed_256_byte_pages"]), 4096)
        self.assertEqual(report["excluded_byte_count"], 0)
        self.assertEqual(report["release_complete_event_credit"], 0)

    def test_invalid_raw_size_fails_closed(self):
        complete = bytes(0x20000)
        for bad in (complete[:-1], complete + bytes([0]), b""):
            with self.assertRaisesRegex(probe.CompleteEventError, "full 128-KiB"):
                probe.audit_qa01_wram_pair(complete, bad)
            with self.assertRaisesRegex(probe.CompleteEventError, "full 128-KiB"):
                probe.audit_qa01_wram_pair(bad, complete)


if __name__ == "__main__":
    unittest.main()

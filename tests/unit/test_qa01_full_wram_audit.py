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



class DenseZooPhaseByteAuditTests(unittest.TestCase):
    def test_contiguous_result_window_retains_first_raw_mismatch(self):
        from tempfile import TemporaryDirectory
        from unittest import mock

        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "ref").mkdir()
            (root / "native").mkdir()
            logs = []
            for side, entry in (("ref", 1017), ("native", 1019)):
                lines = []
                for frame in probe.ZOO_TERMINAL_FRAMES:
                    tag = f"zoo-phase-{frame:05d}"
                    data = bytearray(0x20000)
                    data[0x00CE] = 1
                    data[0x009F] = 0xBC if frame >= 5163 else 0x16
                    data[0x0313] = 0x3D if frame >= 5163 else 1
                    if side == "native" and frame == 5164:
                        data[0x01DD] = 0x42
                    (root / side / f"{tag}.wram.bin").write_bytes(data)
                    lines.append(f"script f={entry + frame} dump {tag} ok")
                logs.append("\n".join(lines) + "\n")
            with mock.patch.object(probe.engine, "race_entry_frame",
                                   side_effect=[1017, 1019]):
                out = probe.summarize_zoo_terminal_phase(
                    root, logs[0], logs[1], 1017, 1019, 5163, 5163)
            edge = out["contiguous_post_result_observation"]
            self.assertIsNone(edge["first_named_state_difference_frame"])
            self.assertIsNone(edge["first_gameplay_field_difference_frame"])
            self.assertEqual(edge["first_unmasked_wram_byte_difference_frame"], 5164)
            self.assertFalse(edge["all_postresult_full_wram_byte_pairs_equal"])
            self.assertEqual(edge["first_full_wram_digest_difference_frame"], 5164)
            mismatched = next(x for x in out["relative_frame_comparisons"]
                              if x["relative_frame"] == 5164)
            self.assertEqual(mismatched["full_wram_byte_difference"][
                "first_differing_address"], "7E:01DD")
            self.assertEqual(mismatched["full_wram_byte_difference"][
                "differing_byte_count"], 1)
            self.assertTrue(next(x for x in out["relative_frame_comparisons"]
                                 if x["relative_frame"] == 5163)[
                                     "full_wram_byte_difference"]["byte_exact"])
            self.assertEqual(out["release_complete_event_credit"], 0)


if __name__ == "__main__":
    unittest.main()

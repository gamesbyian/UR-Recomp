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


class ExecutedZooWramReceiptTests(unittest.TestCase):
    def test_source_pinned_unmasked_receipt_cannot_promote_event(self):
        import json
        report = json.loads((ROOT / "analysis/data" /
                             "qa01-zoo-unmasked-wram-20261015.json").read_text())
        self.assertEqual(report["source"]["run_id"], 38820550442)
        self.assertEqual(report["source"]["producer_report_sha256"],
                         "0fdcb4a3120dcaec970964b64d737e4433f140982304cb55e885ad2bb4e877af")
        self.assertEqual(report["source"]["original_input_replay_script_sha256"],
                         "414cb0b1013509f60faf35102353dd10ce36fc684284dd46af11092ad22c5de9")
        self.assertEqual(report["source"]["original_native_producer_exit"], 0)
        self.assertEqual(report["source"]["case_disposition"], "strict_candidate")
        mem = report["wram"]
        self.assertEqual(mem["full_bytes_per_guest"], 131072)
        self.assertEqual(mem["excluded_byte_count"], 0)
        self.assertTrue(mem["all_sample_difference_addresses_enumerated"])
        self.assertEqual(mem["total_pairs"], 48)
        self.assertEqual(mem["total_byte_exact_pairs"], 9)
        windows = mem["windows"]
        for name, n, exact in (("dense_guest_relative", 31, 1),
                               ("result_followthrough", 6, 0),
                               ("next_bowl", 11, 8)):
            rows = windows[name]["sampled_frame_counts_and_first_addresses"]
            self.assertEqual(len(rows), n)
            self.assertEqual(windows[name]["samples_count"], n)
            self.assertEqual(sum(row[1] == 0 for row in rows), exact)
            self.assertEqual(windows[name]["byte_exact_pairs"], exact)
            self.assertEqual(sum(row[1] for row in rows),
                             windows[name]["differing_byte_occurrences"])
            self.assertEqual(len({row[0] for row in rows}), n)
            self.assertTrue(all((count == 0) == (first is None)
                                for _, count, first in rows))
        self.assertEqual(len(mem["all_distinct_differing_snes_addresses"]), 27)
        self.assertEqual(mem["all_distinct_differing_snes_addresses"][-2:],
                         ["7E:2000", "7E:2004"])
        entry = report["bowl_transition"]
        self.assertEqual(entry["source_original_fresh_native_result_relative_entry"], 267)
        self.assertEqual(
            [(d["snes_address"], d["original_byte"], d["native_byte"])
             for d in entry["plus_267_exact_differences"]],
            [("7E:01ED", 65, 135), ("7E:01EE", 2, 127),
             ("7E:2000", 4, 3), ("7E:2004", 64, 128)])
        self.assertTrue(entry["plus_268_wram_byte_exact"])
        self.assertTrue(entry["all_11_complete_original_native_8k_sram_pairs_byte_exact"])
        limits = report["negative_gates"]
        self.assertEqual(limits["original_event_acceptance"], 0)
        self.assertEqual(limits["usa_event_denominator"], 45)
        self.assertFalse(limits["complete_cpu_logic_tick_equivalence_proven"])
        self.assertFalse(limits["source_read_liveness_for_7E_2000_and_7E_2004_proven"])
        self.assertFalse(limits["host_disk_save_publish_and_hard_kill_proven"])
        repeat = report["independent_repeat"]
        self.assertEqual(repeat["run_id"], 38820862424)
        self.assertEqual(repeat["case_artifact_id"], 12013343141)
        self.assertEqual(repeat["producer_report_sha256"],
                         "8c915608e7299a6e9effd8dfb4a9551990b97920dc117f82360edb5c8a65d42f")
        self.assertEqual(repeat["case_artifact_sha256"],
                         "1443916e1fff57973ec472e05d5d4b0819bd1b868533184a08f0aa18556b6885")
        self.assertEqual(repeat["native_guest_elf_sha256"],
                         report["source"]["native_guest_elf_sha256"])
        self.assertNotEqual(repeat["reference_core_sha256"],
                            report["source"]["reference_core_sha256"])
        self.assertEqual(repeat["observations_exactly_equal"], {
            "zoo_terminal_host_phase": True,
            "source_terminal_followthrough": True,
            "zoo_next_bowl_handoff": True})
        self.assertEqual(repeat["case_disposition"], "strict_candidate")
        self.assertEqual(repeat["release_credit"], 0)



if __name__ == "__main__":
    unittest.main()

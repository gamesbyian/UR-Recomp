"""Invariant checks for the re-opened authentic RF054 status-consumer receipt.

These tests check frozen receipt structure, not a substitute for separately
re-opening the actual SHA-bound original/native case archive.
"""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RECEIPT=ROOT / "analysis/data/rf061-authentic-rf054-archive-consumed-nmi-status-20261019.json"


class RF061HistoricalReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(RECEIPT.read_text())

    def test_original_and_native_evidence_have_independent_lineages(self):
        r=self.r
        self.assertEqual(r["schema"],"ur-qa01-rf061-archived-original-native-bounded-consumption/1")
        self.assertEqual(r["provenance"]["case_zip_sha256"],
                         "3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c")
        for field in ("case_zip_sha256","original_reference_log_sha256","native_replay_log_sha256",
                      "rom_sha256","original_movie_sha256","expanded_input_sha256",
                      "native_elf_sha256","source_core_sha256"):
            self.assertEqual(len(r["provenance"][field]),64)
        self.assertEqual(r["original"]["original_macro_local_ordinal_rows"],0)
        self.assertFalse(r["original"]["shared_ordinal_across_bus_macro_checkpoint"])
        self.assertTrue(r["native"]["RF047_seq_is_complete_1_through_2741"])
        self.assertEqual(r["native"]["bus_helper_read_executed_guest_PC_rows"],0)
        self.assertEqual(r["native"]["read_11C774"]["actual_bus_read_ordinal"],492)

    def test_nine_actual_status_consumers_do_not_overclaim_full_rti(self):
        r=self.r["original_native_NMI"]
        self.assertTrue(r["nine_of_nine_status_values_match"])
        self.assertEqual(r["both_actual_consumed_status_values"],"26")
        self.assertEqual(r["original_true_status_pull_guest_PC"],"80:B0EB")
        self.assertEqual(r["original_true_status_pull_bus_address"],"00:01ED")
        self.assertEqual(len(r["native_after_push_status_read_ordinal_pairs"]),9)
        self.assertEqual(set(r["original_guest_resume_by_frame"]),{str(x) for x in range(1017,1026)})
        self.assertEqual(sum(pc=="82D4F0" for pc in r["original_guest_resume_by_frame"].values()),4)
        self.assertEqual(set(r["native_guest_resume_by_frame"].values()),{"82D4EE"})
        for left,right in r["native_after_push_status_read_ordinal_pairs"]:
            self.assertEqual(left+1,right)
        self.assertFalse(r["entire_RTI_saved_PC_PB_consumption_equivalence_claim"])
        self.assertFalse(r["all_later_stack_reads_proven_equal"])

    def test_full_unmasked_controls_are_research_only(self):
        r=self.r
        c=r["unmasked_controls"]
        self.assertEqual((c["pair_count"],c["whole_Wram_byte_exact_pairs"],
                          c["differing_byte_occurrences"]), (78,51,92))
        self.assertEqual(c["per_pair_original_and_native_bytes"],131072)
        self.assertEqual(c["excluded_memory_bytes"],0)
        self.assertFalse(c["original_raw_unmasked_memory_files_archived"])
        self.assertFalse(r["qa01_causal_window"]["qualified_first_consumed_divergence"])
        self.assertEqual(r["qa01_causal_window"]["admission"],"HOLD")
        self.assertEqual(c["accepted_complete_USA_events"],0)


if __name__=="__main__":
    unittest.main()

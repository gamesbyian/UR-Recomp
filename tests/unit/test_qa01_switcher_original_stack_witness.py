"""QA-01: preserve genuine source Snes9x Switcher JSR return-byte evidence.

All facts in the witness derive from archived CI run 38088102870 and its
hash-pinned original-opcode-scope log, recovered without replay in 38088688106.
Neither this test nor the source observation admits any full USA event.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WITNESS = ROOT / "analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json"


class SwitcherOriginalStackSourceWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(WITNESS.read_text(encoding="utf-8"))
        cls.observed = cls.source["observed"]

    def test_independent_source_artifacts_are_pinned_and_nonadmission(self):
        source = self.source["source"]
        self.assertEqual(self.source["schema"],
                         "UR-QA01-SWITCHER-ORIGINAL-STACK-JSR-WITNESS/1")
        self.assertEqual(source["original_execution_run_id"], 38088102870)
        self.assertEqual(source["original_artifact_id"], 11683670622)
        self.assertEqual(source["original_artifact_zip_sha256"],
                         "9f3f8020ea12f58b9094e0fbfe00d6161d9c6812dbf49837c91c7e5a57c29e95")
        self.assertEqual(source["recovery_run_id"], 38088688106)
        self.assertEqual(source["recovered_artifact_id"], 11684005205)
        self.assertEqual(source["original_source_result_movie_host_frame"], 17030)
        self.assertEqual(self.source["adjudication"]["complete_event_release_credit"], 0)
        self.assertEqual(self.source["adjudication"]["denominator_usa"], 45)
        self.assertTrue(self.source["adjudication"]["do_not_shift_input"])

    def test_all_archived_original_target_byte_change_counts_are_exhaustive(self):
        counts = self.observed["target_address_change_counts"]
        compatible = self.observed["push_opcode_sp_target_compatible_counts"]
        self.assertEqual(counts, compatible)
        self.assertTrue(self.observed["every_observed_change_sp_address_compatible"])
        self.assertEqual(sum(counts.values()), 13709)
        self.assertEqual(self.observed["original_bounded_opcode_scope_write_events"],
                         sum(counts.values()))
        self.assertEqual(set(counts),
                         {"7E:01E6", "7E:01E7", "7E:01EF", "7E:01F0",
                          "7E:01F1", "7E:01F2", "7E:01F3"})
        self.assertEqual(self.observed["unchanged_in_bounded_original_result_window"],
                         ["7E:01DD"])
        self.assertEqual(counts["7E:01F1"], 13204)
        self.assertEqual(self.observed["complete_original_opcode_histograms_per_address"]
                         ["7E:01F1"]["20"], 13171)

    def test_jsr_instruction_pushed_bytes_equal_65816_return_low_addresses(self):
        sites = self.observed["dominant_01f1_jsr_source_pcs"]
        counts = dict(self.observed["top_eight_original_cpu_pc_scopes_per_address"]
                      ["7E:01F1"])
        self.assertEqual({s["original_pc"] for s in sites},
                         {"82:B1F2", "82:B1F9"})
        for site in sites:
            with self.subTest(pc=site["original_pc"]):
                original_bank, original_pc = site["original_pc"].split(":")
                return_bank, return_pc = site["return_pc"].split(":")
                self.assertEqual(return_bank, original_bank)
                self.assertEqual(int(return_pc, 16), int(original_pc, 16) + 2)
                self.assertEqual(int(site["observed_byte_after"], 16),
                                 int(return_pc, 16) & 0xFF)
                self.assertEqual(site["original_opcode"], "20")
                self.assertEqual(site["stack_pointer_before"], "01F2")
                self.assertEqual(site["stack_pointer_after"], "01F0")
                self.assertEqual(site["guest_wram_address"], "7E:01F1")
                self.assertEqual(site["observed_count"], counts[site["original_pc"]])
        total_dominant = sum(site["observed_count"] for site in sites)
        self.assertEqual(total_dominant, 12939)
        self.assertAlmostEqual(self.observed["dominant_jsr_share_of_01f1_changes"],
                               total_dominant / 13204)
        observed = [e for e in self.observed["raw_examples_from_bounded_sample"]
                    if e["wram_address"] == "7E:01F1"
                    and e["original_pc"] in counts]
        self.assertGreaterEqual(len(observed), 2)
        for event in observed:
            if event["original_pc"] not in {s["original_pc"] for s in sites}:
                continue
            with self.subTest(event=event):
                self.assertEqual(event["opcode"], "20")
                self.assertTrue(event["stack_pointer_address_compatible"])
                self.assertEqual(event["sp_before"], "01F2")
                self.assertEqual(event["sp_after"], "01F0")
                return_low = (int(event["original_pc"].split(":")[1], 16) + 2) & 0xFF
                self.assertEqual(int(event["new"], 16), return_low)


if __name__ == "__main__":
    unittest.main()

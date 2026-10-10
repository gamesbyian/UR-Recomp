"""Executed original-Snes9x/Baldosa Switcher final pre-result equality, not release admission."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (ROOT / "analysis" / "data" /
            "switcher-original-baldosa-same-host-5782-executed-20261010.json")


class SwitcherSameHost5782ActualEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_provenance_not_an_invented_or_accepted_event(self):
        d = self.d
        self.assertEqual(d["schema"], "UR-QA01-SWITCHER-ORIGINAL-NATIVE-SAME-HOST-5782/1")
        p = d["provenance"]
        self.assertEqual(p["workflow_run_id"], 38076629158)
        self.assertEqual(p["artifact_id"], 11679421807)
        self.assertEqual(
            p["artifact_zip_sha256"],
            "0d7d6686b03658ebb1f2414aaa22e9a428d3670d43e3a6f6dae3c85f820b5193")
        self.assertEqual(
            p["original_report_sha256"],
            "cf69572ea1bc51e2a735f76d6cb87d6f61c57a4101ac893fa60794b1bfc2bb0d")
        self.assertTrue(p["one_shot_pr_closed_unmerged"])
        self.assertEqual(p["workflow_conclusion"], "failure")
        self.assertEqual(p["report_producer_exit_code"], 1)
        self.assertEqual(d["scope_limits"]["release_complete_event_credit"], 0)
        self.assertEqual(d["scope_limits"]["official_usa_full_event_passes"], 0)
        self.assertEqual(d["scope_limits"]["total_usa_events"], 45)

    def test_independent_entry_and_both_sides_real_same_absolute_host(self):
        d = self.d
        entry = d["independent_stock_entry"]
        x = d["genuine_penultimate_host_capture"]
        self.assertTrue(entry["source_to_fresh_reference_entry_fields_equal"])
        self.assertTrue(entry["source_to_fresh_native_entry_fields_equal"])
        self.assertEqual(entry["reference_entry_absolute_host"], 1079)
        self.assertEqual(entry["native_entry_absolute_host"], 1081)
        self.assertEqual(entry["reference_entry_absolute_host"] +
                         x["reference_relative_frame"], 5782)
        self.assertEqual(entry["native_entry_absolute_host"] +
                         x["native_relative_frame"], 5782)
        self.assertEqual(x["reference_absolute_host"], 5782)
        self.assertEqual(x["native_absolute_host"], 5782)
        self.assertEqual(x["original_and_native_next_result_absolute_host"], 5783)
        self.assertEqual(x["guest_wram_bytes_read_per_engine"], 0x20000)
        self.assertFalse(x["original_movie_input_modified"])

    def test_actual_equal_names_and_no_unsupported_all_memory_claim(self):
        d = self.d
        x = d["genuine_penultimate_host_capture"]
        self.assertTrue(x["all_named_fields_equal"])
        self.assertEqual(x["disagreeing_fields"], [])
        self.assertEqual(x["equal_fields"]["menu"], 0x16)
        self.assertEqual(x["equal_fields"]["in_race"], 0)
        self.assertEqual(x["equal_fields"]["observed_course_track"], 3)
        self.assertEqual(x["equal_fields"]["p1_finish_gate"], 1)
        self.assertEqual(x["equal_fields"]["p1_laps"], 0)
        self.assertEqual(x["equal_fields"]["p2_laps"], 0)
        self.assertEqual(x["equal_fields"]["clock_raw"], [1, 1, 2, 8, 1])
        self.assertEqual(x["equal_fields"]["p1_x"], 19456)
        self.assertEqual(x["equal_fields"]["p1_y"], 19456)
        self.assertTrue(x["equal_fields"]["source_terminal_phase_diagnostic_only"])
        self.assertEqual(d["scope_limits"]["all_131072_guest_memory_bytes_identical"],
                         "not measured; only named fields were compared")
        for missing_authority in ("cpu_pc_instruction_phase_parity",
                                  "nmi_ppu_dma_phase_parity",
                                  "continuous_4700_frame_physics_parity"):
            self.assertEqual(d["scope_limits"][missing_authority], "not measured")

    def test_real_p1_result_but_different_guest_relative_terminal(self):
        d = self.d
        p = d["genuine_penultimate_host_capture"]
        x = d["original_and_native_result"]
        self.assertEqual(
            d["independent_stock_entry"]["reference_entry_absolute_host"] +
            x["original_guest_relative_onset"], x["original_absolute_host_onset"])
        self.assertEqual(
            d["independent_stock_entry"]["native_entry_absolute_host"] +
            x["native_guest_relative_onset"], x["native_absolute_host_onset"])
        self.assertEqual(x["original_absolute_host_onset"],
                         x["native_absolute_host_onset"])
        self.assertEqual(x["original_absolute_host_onset"], 5783)
        self.assertEqual(x["p1_race_time"], "1:08.81")
        self.assertEqual(x["p1_name"], "MIKE")
        self.assertTrue(x["settled_ppu_text_equal"])
        self.assertEqual(x["ordinary_paired_relative_samples"], 46)
        self.assertFalse(d["scope_limits"]["guest_relative_result_onset_equal"])
        self.assertTrue(d["scope_limits"]["absolute_host_terminal_onset_equal"])
        self.assertEqual(d["scope_limits"]["release_complete_event_credit"], 0)


if __name__ == "__main__":
    unittest.main()

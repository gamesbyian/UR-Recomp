"""Synthetic cross-report native writer/read provenance, no release admission."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_stack_read_pair_crosswalk as x
import qa01_native_nmi_beam_report as beam
import qa01_native_stack_read_report as reads

SHA = "f" * 64
PAIR = {"course_id": "course:04", "trusted": True}
BEAM = {
    "schema": beam.SCHEMA,
    "paired_report_bytes_sha256": SHA,
    "exact_original_native_switcher_pair_provenance": PAIR,
    "native_observation_host_frame_window": [5778, 5782],
    "accepted_usa_course_count_added": 0,
    "framework_beam_vs_original_cpu_phase_unaligned": True,
    "native_original_nmi_writer_beam": {
        "native_host_frame": 5781,
        "generated_owner": "I_NMI_M1X1",
        "wram_write_destination": "7E:01DD",
        "stack_word_saved": "4004",
        "accumulator_at_write": "4004",
        "stack_pointer_at_write": "01DD",
    },
}
READ = {
    "schema": reads.SCHEMA,
    "paired_report_bytes_sha256": SHA,
    "independently_authenticated_original_native_pair": PAIR,
    "native_frame_bounds": [5778, 5782],
    "native_read_observer_armed_by_real_nmi_4004_writer": True,
    "read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer": True,
    "native_bus_read_attempt_count": 1,
    "native_stack_read_attempts": [{
        "target_stack_bytes_touched": ["7E:01DD", "7E:01DE"],
        "native_snes_frame_counter": 5781,
        "read_value": "4004",
        "observed_after_4004_writer_callback_started": True,
    }],
    "native_bus_read_attempts_by_target": {"7E:01DD": 1, "7E:01DE": 1},
    "zero_count_is_bounded_native_negative_not_no_reader_ever": False,
    "release_complete_event_credit": 0,
}


class NativeStackReadPairCrosswalkTests(unittest.TestCase):
    def test_same_exact_replay_pair_and_one_observed_read_remains_no_credit(self):
        out = x.summarize(BEAM, READ)
        self.assertEqual(out["native_read_attempt_count"], 1)
        self.assertEqual(out["native_read_targets_tallied"],
                         {"7E:01DD": 1, "7E:01DE": 1})
        self.assertTrue(out["writer_and_reader_share_pair_bytes"])
        self.assertFalse(out["native_guest_result_consumer_proven"])
        self.assertFalse(out["source_original_and_native_beam_phase_alignment_proven"])
        self.assertEqual(out["complete_usa_course_credit"], 0)

    def test_zero_read_witness_is_still_qualified_bounded_negative(self):
        doc = copy.deepcopy(READ)
        doc["native_bus_read_attempt_count"] = 0
        doc["native_stack_read_attempts"] = []
        doc["native_bus_read_attempts_by_target"] = {"7E:01DD": 0, "7E:01DE": 0}
        doc["zero_count_is_bounded_native_negative_not_no_reader_ever"] = True
        data = x.summarize(BEAM, doc)
        self.assertEqual(data["native_read_attempt_count"], 0)
        self.assertFalse(data["native_guest_result_consumer_proven"])

    def test_mismatched_replay_identity_and_forged_attestations_fail_closed(self):
        for obj, key, value in (
            ("read", "paired_report_bytes_sha256", "e" * 64),
            ("read", "independently_authenticated_original_native_pair", {"course_id": "other"}),
            ("beam", "paired_report_bytes_sha256", "corrupt"),
            ("beam", "native_original_nmi_writer_beam", {"stack_word_saved": "4004"}),
            ("beam", "native_observation_host_frame_window", [5778, 5783]),
            ("read", "native_read_observer_armed_by_real_nmi_4004_writer", False),
            ("read", "native_bus_read_attempt_count", 2),
            ("read", "native_bus_read_attempt_count", True),
            ("read", "native_bus_read_attempts_by_target", {"7E:01DD": 0, "7E:01DE": 1}),
            ("read", "zero_count_is_bounded_native_negative_not_no_reader_ever", True),
            ("read", "release_complete_event_credit", 1),
        ):
            writer, reader = copy.deepcopy(BEAM), copy.deepcopy(READ)
            (writer if obj == "beam" else reader)[key] = value
            with self.subTest(obj=obj, field=key), self.assertRaises(ValueError):
                x.summarize(writer, reader)

    def test_manual_workflow_produces_separate_crosscheck_from_existing_logs(self):
        wf = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        self.assertIn("qa01_native_stack_read_pair_crosswalk.py", wf)
        self.assertIn("--native-read-report", wf)
        self.assertIn("--native-beam-report", wf)
        self.assertIn("native-read-writer-crosswalk.json", wf)


if __name__ == "__main__":
    unittest.main()

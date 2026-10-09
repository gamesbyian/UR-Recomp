"""Original/native bounded scene transition evidence, without causal overclaim."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import summarize_zoo_scene_event_transitions as report


def row(frame: int, *, checkpoint=3, gate=0, laps=1, word=0x2024,
        boost=64, active=1, track=1, x=5000) -> dict:
    return {
        "relative_frame": frame, "in_race": active, "track_id": track,
        "menu": 0, "p1_x": x,
        "p1_next_checkpoint": checkpoint, "p1_finish_gate": gate,
        "p1_laps_remaining": laps, "p1_stored_contact": word,
        "p1_boost": boost,
        "timer_minutes_raw": 0, "timer_tens_raw": 0,
        "timer_seconds_raw": 0, "timer_tenths_raw": 0,
        "timer_subtick_raw": 0,
    }


class ZooSceneTransitionEvidenceTests(unittest.TestCase):
    def test_adjacent_postframe_progression_preserves_prior_dispatch_candidate(self):
        rows = [
            row(209),
            row(210, checkpoint=1, gate=1, laps=0, word=0x2020),
            row(211, checkpoint=1, gate=1, laps=0, word=0x2020),
        ]
        summary = report.observed_transitions(rows)
        self.assertEqual(summary["progression_change_interval_count"], 1)
        self.assertEqual(summary["stored_contact_change_interval_count"], 1)
        transition = summary["progression_change_intervals"][0]
        self.assertEqual((transition["interval_start"], transition["interval_end"]), (209, 210))
        self.assertEqual(transition["observation_resolution"], "adjacent_postframe_only")
        self.assertEqual(transition["progress_changed"]["p1_laps_remaining"],
                         {"before": 1, "after": 0})
        self.assertEqual(transition["previous_postframe_stored_contact"], 0x2024)
        self.assertEqual(transition["previous_postframe_contact_slot_candidate"], 10)
        self.assertEqual(transition["next_postframe_contact_slot"], 8)
        self.assertIn("not an observed handler", transition["phase_limit"])

    def test_sparse_interval_never_forges_exact_transition_frame(self):
        rows = [row(190), row(200, checkpoint=2, word=0x0022),
                row(201, checkpoint=2, word=0x0022)]
        output = report.observed_transitions(rows)
        changed = output["progression_change_intervals"][0]
        self.assertEqual(changed["interval_guest_frames"], 10)
        self.assertEqual(
            changed["observation_resolution"], "sparse_interval_may_contain_multiple_events"
        )
        self.assertEqual(changed["interval_start"], 190)
        self.assertEqual(changed["interval_end"], 200)
        self.assertEqual(changed["previous_postframe_contact_slot_candidate"], 10)

    def test_early_motion_divergence_does_not_hide_later_progression_disagreement(self):
        original = [row(0), row(209), row(210, checkpoint=1, gate=1, laps=0)]
        native = [row(0, x=6000), row(209, x=6000), row(210, x=6000,
                  checkpoint=3, gate=0, laps=1)]
        diagnostic = report.paired_event_diagnostics(original, native)
        self.assertEqual(diagnostic["first_progression_state_disagreement"]["relative_frame"], 210)
        self.assertEqual(
            diagnostic["first_progression_state_disagreement"]["fields"],
            ["p1_next_checkpoint", "p1_finish_gate", "p1_laps_remaining"],
        )
        self.assertIsNone(diagnostic["first_stored_contact_disagreement"])
        self.assertIsNone(diagnostic["first_boost_disagreement"])
        self.assertEqual(diagnostic["reference_observed"]["progression_change_interval_count"], 1)
        self.assertEqual(diagnostic["native_observed"]["progression_change_interval_count"], 0)
        self.assertIn("NOT proof", diagnostic["authority_limit"])

    def test_scene_exit_is_not_silently_reported_as_identical_active_race(self):
        rows = [row(0), row(209), row(210, active=0)]
        diagnostic = report.paired_event_diagnostics(rows, list(map(dict, rows)))
        self.assertEqual(diagnostic["reference_observed"]["first_nonactive_relative_frame"], 210)
        self.assertEqual(diagnostic["native_observed"]["observed_active_samples"], 2)
        self.assertEqual(diagnostic["first_progression_state_disagreement"]["classification"],
                         "scene_not_pairwise_active")

    def test_contact_and_meter_differences_are_separate_from_checkpoint_result(self):
        original = [row(0), row(1, word=0x2020, boost=80)]
        native = [row(0), row(1, word=0x0022, boost=64)]
        output = report.paired_event_diagnostics(original, native)
        self.assertIsNone(output["first_progression_state_disagreement"])
        self.assertEqual(output["first_stored_contact_disagreement"]["relative_frame"], 1)
        self.assertEqual(output["first_stored_contact_disagreement"]["reference"],
                         {"p1_stored_contact": 0x2020})
        self.assertEqual(output["first_boost_disagreement"]["relative_frame"], 1)

    def test_original_horizontal_onset_and_first_clock_tick_are_distinct(self):
        original = [
            row(0, x=9200),
            row(190, x=9200),
            row(204, x=9200),
            row(205, x=9185),
            dict(row(206, x=9169), timer_subtick_raw=1),
            dict(row(207, x=9149), timer_subtick_raw=2),
        ]
        phase = report.observed_start_phase(original)
        self.assertEqual(phase["first_p1_x_change_interval"], [204, 205])
        self.assertEqual(phase["first_nonzero_timer_interval"], [205, 206])
        self.assertEqual(phase["initial_active_frame"], 0)
        self.assertIn("NOT first vertical motion", phase["qualifier"])
        reference = original
        native = [dict(x) for x in original]
        native[4]["timer_subtick_raw"] = 0
        native[4]["p1_x"] = 9169  # same movement despite delayed timer
        parity = report.paired_event_diagnostics(reference, native)
        self.assertIsNone(parity["first_progression_state_disagreement"])
        self.assertIsNone(parity["first_stored_contact_disagreement"])
        self.assertEqual(parity["first_stopwatch_disagreement"]["relative_frame"], 206)
        self.assertEqual(
            parity["first_stopwatch_disagreement"]["fields"], ["timer_subtick_raw"]
        )
        self.assertEqual(
            parity["reference_start_phase"]["first_nonzero_timer_interval"], [205, 206]
        )
        self.assertEqual(
            parity["native_start_phase"]["first_nonzero_timer_interval"], [206, 207]
        )

    def test_start_phase_denies_non_byte_clock_and_nonchronological_frames(self):
        with self.assertRaisesRegex(report.EventEvidenceError, "empty"):
            report.observed_start_phase([])
        bad = dict(row(0), timer_subtick_raw=256)
        with self.assertRaisesRegex(report.EventEvidenceError, "byte range"):
            report.observed_start_phase([bad])
        with self.assertRaisesRegex(report.EventEvidenceError, "chronological"):
            report.observed_start_phase([row(1), row(1)])
        exit_row = row(0, active=0)
        self.assertIsNone(report.observed_start_phase([exit_row])["initial_active_frame"])

    def test_invalid_samples_and_contact_words_rejected(self):
        with self.assertRaisesRegex(report.EventEvidenceError, "empty"):
            report.observed_transitions([])
        with self.assertRaisesRegex(report.EventEvidenceError, "chronological"):
            report.observed_transitions([row(1), row(1)])
        with self.assertRaisesRegex(report.EventEvidenceError, "nonnegative"):
            report.observed_transitions([row(-1)])
        bad = row(0)
        bad.pop("p1_next_checkpoint")
        with self.assertRaisesRegex(report.EventEvidenceError, "missing"):
            report.observed_transitions([bad])
        for value in (-1, 0x10000, "0x2024", True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(report.EventEvidenceError, "unsigned u16"):
                    report.surface_slot(value)
        with self.assertRaisesRegex(report.EventEvidenceError, "phases differ"):
            report.first_field_disagreement([row(1)], [row(2)], report.PROGRESS_FIELDS)
        with self.assertRaisesRegex(report.EventEvidenceError, "counts differ"):
            report.first_field_disagreement([row(1)], [], report.PROGRESS_FIELDS)


if __name__ == "__main__":
    unittest.main()

"""Synthetic non-emulator contract tests. Absolutely no USA event credit."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_event_acceptance_readiness as readiness


def fixture():
    return {
        "schema": "ur-qa01-event-campaign/1", "case": "zoom-zoo",
        "course_id": "course:02", "source_sha": "a" * 40,
        "plan_sha256": "a" * 64, "disposition": "strict_candidate",
        "release_credit": 0,
        "evidence": {
            **{key: "a" * 64 for key in (
                "producer_sha256", "rom_sha256", "movie_sha256", "core_sha256",
                "native_sha256", "input_sha256", "source_sram_sha256",
                "original_movie_window_sha256", "reference_script_sha256")},
            "strict_candidate": True, "terminal_frame_matched": True,
            "strict_producer_gate_audit": {
                "gates": {name: True for name in (
                    *readiness.campaign.STRICT_PRODUCER_GATES,
                    "no_sampled_state_disagreement", "same_guest_relative_result_onset")},
                "recomputed_candidate": True},
            "source_original_movie_vs_fresh_guest_result_phase": {
                "three_relative_durations_equal": True,
                "continuous_original_to_fresh_equivalence_proven": False,
                "independent_original_movie_and_fresh_guest_clocks_not_rebased": True,
                "release_credit": 0},
            "post_result_bounded": {
                "status": "six_sample_triplet_named_agreement", "release_credit": 0},
            "next_bowl_bounded": {
                "status": "bounded_source_handoff_agreement", "release_credit": 0,
                "source_entry_offset": 267, "fresh_original_entry_offset": 267,
                "fresh_native_entry_offset": 267, "all_sampled_sram_pairs_equal": True,
                "all_sampled_named_triplets_equal": True,
                "unsampled_frames_or_windows_disk_persistence_proven": False,
                "raw_wram_differing_sample_offsets": [266, 280],
                "raw_wram_differing_byte_occurrences": 8,
                "all_sampled_full_wram_pairs_equal": False},
        },
    }


class ReadinessTests(unittest.TestCase):
    def test_positive_bounded_zoo_remains_hold_with_raw_residuals(self):
        report = readiness.assess(fixture())
        self.assertEqual(report["event_adjudication"], "HOLD")
        self.assertEqual(report["accepted_event_credit"], 0)
        self.assertEqual(report["bounded_findings"]["strict_onset"], "matched")
        self.assertIn("observed_unwaived_handoff_full_wram_differences_need_causality",
                      report["blocking_requirements"])
        self.assertIn("same_shipping_windows_executable_source_and_controller_route_unbound",
                      report["blocking_requirements"])

    def test_zero_residuals_still_do_not_grant_credit(self):
        row = fixture()
        handoff = row["evidence"]["next_bowl_bounded"]
        handoff["raw_wram_differing_sample_offsets"] = []
        handoff["raw_wram_differing_byte_occurrences"] = 0
        handoff["all_sampled_full_wram_pairs_equal"] = True
        report = readiness.assess(row)
        self.assertEqual(report["event_adjudication"], "HOLD")
        self.assertEqual(report["accepted_event_credit"], 0)
        self.assertNotIn("observed_unwaived_handoff_full_wram_differences_need_causality",
                         report["blocking_requirements"])

    def test_impossible_raw_wram_aggregate_and_equality_claims_rejected(self):
        # Two distinct differing full-WRAM pairs require >=2 unequal bytes.
        # They cannot report more than 2 * 128 KiB different bytes either.
        for mismatch in ("too_few", "too_many", "false_equality",
                         "false_inequality"):
            row = fixture()
            handoff = row["evidence"]["next_bowl_bounded"]
            if mismatch == "too_few":
                handoff["raw_wram_differing_byte_occurrences"] = 1
            elif mismatch == "too_many":
                handoff["raw_wram_differing_byte_occurrences"] = 2 * 131072 + 1
            elif mismatch == "false_equality":
                handoff["all_sampled_full_wram_pairs_equal"] = True
            else:
                handoff["raw_wram_differing_sample_offsets"] = []
                handoff["raw_wram_differing_byte_occurrences"] = 0
            with self.subTest(mismatch=mismatch), self.assertRaisesRegex(
                    ValueError, "WRAM"):
                readiness.assess(row)

    def test_bounds_are_inclusive_and_do_not_award_promotion(self):
        for count in (2, 2 * 131072):
            row = fixture()
            row["evidence"]["next_bowl_bounded"][
                "raw_wram_differing_byte_occurrences"] = count
            result = readiness.assess(row)
            self.assertEqual(result["event_adjudication"], "HOLD")
            self.assertEqual(result["accepted_event_credit"], 0)

    def test_archived_source_clock_is_independent(self):
        row = fixture()
        row["evidence"]["source_original_movie_vs_fresh_guest_result_phase"][
            "three_relative_durations_equal"] = False
        self.assertIn("archived_movie_fresh_guest_result_clock_disagreement",
                      readiness.assess(row)["blocking_requirements"])

    def test_negative_guest_and_bad_harness_remain_distinct(self):
        row = fixture()
        row["disposition"] = "strict_divergence"
        row["evidence"]["strict_candidate"] = False
        row["evidence"]["strict_producer_gate_audit"] = {
            "gates": {**fixture()["evidence"]["strict_producer_gate_audit"]["gates"],
                      "timed_race_or_circuit_result_visible": False},
            "recomputed_candidate": False}
        self.assertIn("strict_original_native_result_or_active_state_divergence",
                      readiness.assess(row)["blocking_requirements"])
        row = fixture()
        row["disposition"] = "producer_error"
        del row["evidence"]
        self.assertEqual(readiness.assess(row)["blocking_requirements"][0],
                         "producer_error_requires_genuine_source_bound_replay")

    def test_fail_closed_on_overpromotion_or_contradiction(self):
        edits = (
            lambda x: x.update(release_credit=1),
            lambda x: x["evidence"].update(strict_candidate=False),
            lambda x: x["evidence"]["strict_producer_gate_audit"].update(
                recomputed_candidate=False),
            lambda x: x["evidence"]["strict_producer_gate_audit"]["gates"].clear(),
            lambda x: x["evidence"]["strict_producer_gate_audit"]["gates"].update(
                unknown=True),
            lambda x: x["evidence"]["next_bowl_bounded"].update(
                unsampled_frames_or_windows_disk_persistence_proven=True),
            lambda x: x["evidence"]["next_bowl_bounded"].update(
                raw_wram_differing_byte_occurrences=0),
            lambda x: x["evidence"]["next_bowl_bounded"].update(
                raw_wram_differing_sample_offsets=[999]),
            lambda x: x["evidence"]["source_original_movie_vs_fresh_guest_result_phase"].update(
                continuous_original_to_fresh_equivalence_proven=True),
            lambda x: x.update(source_sha="main"),
            lambda x: x["evidence"].update(rom_sha256="invalid"),
        )
        for mutate in edits:
            with self.subTest(edit=mutate):
                row = copy.deepcopy(fixture())
                mutate(row)
                with self.assertRaises(ValueError):
                    readiness.assess(row)


if __name__ == "__main__":
    unittest.main()

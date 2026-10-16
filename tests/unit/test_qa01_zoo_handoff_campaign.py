"""Synthetic negative/positive contract tests. No original/native emulation or release credit."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_event_campaign as c


def source_fixture(*, early_native: bool = False, changed_sram: bool = False) -> dict:
    """Two independent clocks, real source 267 bracket, synthetic 11-frame memory."""
    if early_native:
        changed_sram = True
    report = {
        "schema_version": 1, "name": "zoom-zoo",
        "course_id": "course:02", "family": "circuit-a",
        "native_backend": "pinned-baldosa",
        "admission": "investigative candidate; not a release-ledger pass",
        "reference_entry": 1017, "native_entry": 1019,
        "native_frame_shift": 2,
        "original_source_event": {
            "original_entry_frame": 3190, "original_result_frame": 8353,
            "source_active_frames_to_result": 5163},
        "comparison": {
            "paired_event_candidate": True,
            "terminal_result_frame_matched": True,
            "terminal_result_guest_frame": {
                "reference_relative": 5163, "native_relative": 5163},
            "first_sample_disagreement": None,
            **{key: True for key in c.STRICT_PRODUCER_GATES}},
        **{key: "a" * 64 for key in (
            "rom_sha256", "original_movie_sha256",
            "native_executable_sha256", "reference_core_sha256",
            "input_sha256", "source_sram_sha256",
            "original_movie_window_sha256", "reference_script_sha256")},
    }
    def bracket(offset: int) -> dict:
        return {
            "last_observed_inactive_offset": offset - 1,
            "first_observed_active_offset": offset,
            "exact_observed_entry_offset": offset}
    offsets = c.ZOO_BOWL_OFFSETS
    source_samples = {}
    pairs = []
    for offset in offsets:
        source_row = {
            "original_movie_host_frame": 8353 + offset,
            "menu": 0, "track": 2, "in_race": int(offset >= 267)}
        source_samples[str(offset)] = source_row
        original = {
            "menu": 0, "track": 2, "in_race": source_row["in_race"],
            "actual_host_frame": 1017 + 5163 + offset,
            "full_wram_bytes": 131072, "wram_sha256": "a" * 64,
            "source_earned_zoo_best_lap": {
                "rank": 0, "value_word": 2510, "holder_index": 0},
            "record_checksum_stored": 100,
            "record_checksum_calculated": 100,
            "record_checksum_matches": True,
            "sram_sha256": "a" * 64,
        }
        native = copy.deepcopy(original)
        native["actual_host_frame"] = 1019 + 5163 + offset
        native["in_race"] = int(offset >= (265 if early_native else 267))
        if early_native and offset in (265, 266):
            native["wram_sha256"] = "b" * 64
        if changed_sram:
            native["sram_sha256"] = "b" * 64
        raw_equal = (original["wram_sha256"] == native["wram_sha256"])
        sram_equal = (original["sram_sha256"] == native["sram_sha256"])
        pairs.append({
            "offset_from_observed_zoo_result": offset,
            "original_movie": source_row,
            "fresh_guests": {"original": original, "native": native},
            "original_native_full_wram_byte_difference": {
                "full_wram_bytes_per_guest": 131072,
                "every_byte_compared": True, "excluded_byte_count": 0,
                "differing_byte_count": 0 if raw_equal else 1,
                "byte_exact": raw_equal,
                "original_wram_sha256": original["wram_sha256"],
                "native_wram_sha256": native["wram_sha256"],
                "cpu_or_logic_tick_parity_proven": False,
                "release_complete_event_credit": 0},
            "triplet_named_states_equal": (
                original["in_race"] == native["in_race"]),
            "original_native_full_sram_equal": sram_equal,
            "battery_sram_differing_byte_count": 0 if sram_equal else 1,
            "battery_first_differences": [] if sram_equal else [{
                "offset": 3889, "original_byte": 26, "native_byte": 27}],
        })
    report["original_source_event"]["source_next_bowl"] = {
        "original_result_host_frame": 8353,
        "original_next_bowl_entry_host_frame": 8620,
        "source_result_to_next_active_entry_frames": 267,
        "samples": source_samples,
        "source_original_active_entry_sustained_eight_frames": True,
        "native_next_course_entry_proven": False,
        "release_complete_event_credit": 0,
    }
    nat_offset = 265 if early_native else 267
    ref_absolute = 1017 + 5163 + 267
    native_absolute = 1019 + 5163 + nat_offset
    report["zoo_next_bowl_handoff"] = {
        "schema": c.ZOO_BOWL_SCHEMA, "sample_count": len(offsets),
        "sample_offsets": list(offsets), "samples": pairs,
        "reference_next_bowl_absolute_host_frame": ref_absolute,
        "native_next_bowl_absolute_host_frame": native_absolute,
        "next_bowl_same_absolute_host_frame": (
            ref_absolute == native_absolute),
        "original_source_movie_result_host_frame": 8353,
        "original_source_movie_next_bowl_active_host_frame": 8620,
        "source_controller_masks_modified": False,
        "source_next_bowl_active_entry_offset": 267,
        "fresh_reference_next_bowl_entry_offset": 267,
        "fresh_native_next_bowl_entry_offset": nat_offset,
        "original_source_entry_bracket": bracket(267),
        "fresh_reference_entry_bracket": bracket(267),
        "fresh_native_entry_bracket": bracket(nat_offset),
        "all_triplet_named_states_equal": not early_native,
        "all_original_native_full_sram_pairs_equal": not changed_sram,
        "all_original_native_full_wram_pairs_equal": not early_native,
        "next_bowl_entry_triple_equal": not early_native,
        "zoo_rank0_2510_and_checksum_preserved_every_sample": True,
        "full_event_guest_logic_tick_equivalence_proven": False,
        "shipping_windows_candidate_proven": False,
        "cold_process_disk_persistence_proven": False,
        "release_complete_event_credit": 0,
    }
    return report


class NextBowlCampaignVerdictTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = c.make_plan("zoom-zoo", "b" * 40)

    def adjudicate(self, data: dict) -> dict:
        source = self.root / "producer.json"
        c.write_json(source, data)
        return c.classify("zoom-zoo", 0, source, self.plan)

    def test_source_matched_handoff_is_bounded_not_release_accepted(self):
        case = self.adjudicate(source_fixture())
        self.assertEqual(case["disposition"], "strict_candidate")
        bounded = case["evidence"]["next_bowl_bounded"]
        self.assertEqual(bounded["status"], "bounded_source_handoff_agreement")
        self.assertEqual(bounded["samples"], 11)
        self.assertEqual([bounded[k] for k in ("source_entry_offset",
                                               "fresh_original_entry_offset",
                                               "fresh_native_entry_offset")],
                         [267, 267, 267])
        self.assertEqual(case["release_credit"], 0)

    def test_authentic_negative_same_absolute_host_cannot_hide_relative_lead(self):
        case = self.adjudicate(source_fixture(early_native=True))
        self.assertEqual(case["disposition"], "strict_candidate")
        status = case["evidence"]["next_bowl_bounded"]
        self.assertEqual(status["status"], "sampled_progression_divergence")
        self.assertEqual(status["fresh_native_entry_offset"], 265)
        self.assertEqual(status["source_entry_offset"], 267)
        self.assertEqual(status["first_sampled_progression_difference_offset"], 259)
        self.assertIn("post-result lifecycle BLOCKED", case["reason"])
        self.assertEqual(case["release_credit"], 0)
        folder = self.root / "qa01-campaign-case-zoom-zoo"
        c.write_json(folder / "case-result.json", case)
        summary, md = c.aggregate(self.plan, self.root)
        self.assertTrue(summary["transport_complete"])
        self.assertEqual(summary["bounded_next_bowl_progression_divergences"], 1)
        self.assertIn("progression blockers: 1", md)
        self.assertEqual(summary["release_admissions"], 0)

    def test_sram_only_source_negative_is_visible_without_entry_lead(self):
        case = self.adjudicate(source_fixture(changed_sram=True))
        status = case["evidence"]["next_bowl_bounded"]
        self.assertEqual(status["status"], "sampled_progression_divergence")
        self.assertEqual(status["fresh_native_entry_offset"], 267)
        self.assertFalse(status["all_sampled_sram_pairs_equal"])
        self.assertTrue(status["all_sampled_named_triplets_equal"])

    def test_missing_observer_cannot_claim_lifecycle_success(self):
        row = self.adjudicate({
            k: v for k, v in source_fixture().items()
            if k != "zoo_next_bowl_handoff" and k != "original_source_event"
        } | {"original_source_event": {
            "original_entry_frame": 3190, "original_result_frame": 8353,
            "source_active_frames_to_result": 5163}})
        self.assertEqual(row["evidence"]["next_bowl_bounded"]["status"],
                         "not_observed")
        self.assertEqual(row["release_credit"], 0)

    def test_mismatched_source_and_guests_are_producer_errors(self):
        mutations = [
            lambda r: r["zoo_next_bowl_handoff"].__setitem__(
                "source_controller_masks_modified", True),
            lambda r: r["zoo_next_bowl_handoff"]["samples"][0][
                "fresh_guests"]["native"].__setitem__("actual_host_frame", 999),
            lambda r: r["zoo_next_bowl_handoff"]["samples"][0][
                "original_movie"].__setitem__("original_movie_host_frame", 8613),
            lambda r: r["zoo_next_bowl_handoff"]["samples"][0][
                "original_native_full_wram_byte_difference"].__setitem__(
                    "byte_exact", False),
            lambda r: r["zoo_next_bowl_handoff"]["samples"][0].__setitem__(
                "battery_sram_differing_byte_count", 2),
            lambda r: r["zoo_next_bowl_handoff"].__setitem__(
                "fresh_native_next_bowl_entry_offset", 267),
            lambda r: r["zoo_next_bowl_handoff"].__setitem__(
                "next_bowl_entry_triple_equal", True),
            lambda r: r["zoo_next_bowl_handoff"].__setitem__(
                "all_original_native_full_sram_pairs_equal", True),
            lambda r: r["zoo_next_bowl_handoff"].__setitem__(
                "shipping_windows_candidate_proven", True),
            lambda r: r["original_source_event"]["source_next_bowl"][
                "samples"]["265"].__setitem__("in_race", 1),
            lambda r: r["zoo_next_bowl_handoff"]["samples"][0][
                "fresh_guests"]["original"].__setitem__(
                    "sram_sha256", "NOT A SHA256"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=repr(mutate)):
                record = source_fixture(early_native=True)
                mutate(record)
                result = self.adjudicate(record)
                self.assertEqual(result["disposition"], "producer_error")
                self.assertEqual(result["release_credit"], 0)

    def test_aggregate_rejects_forged_source_handoff_promotion(self):
        case = self.adjudicate(source_fixture(early_native=True))
        folder = self.root / "qa01-campaign-case-zoom-zoo"
        row = copy.deepcopy(case)
        row["evidence"]["next_bowl_bounded"]["status"] = (
            "bounded_source_handoff_agreement")
        c.write_json(folder / "case-result.json", row)
        summary, _ = c.aggregate(self.plan, self.root)
        self.assertEqual(summary["counts"]["missing_evidence"], 1)
        self.assertFalse(summary["transport_complete"])
        self.assertEqual(summary["release_admissions"], 0)


if __name__ == "__main__":
    unittest.main()

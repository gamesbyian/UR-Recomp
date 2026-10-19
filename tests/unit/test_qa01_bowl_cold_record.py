"""Bowl source-earned cold guest ranked record contract (synthetic only)."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_bowl_cold_record as target
import qa01_bowl_switcher_handoff as handoff
import qa01_cold_result_record as shared


class BowlColdTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.replay = self.root / "replay"
        self.seed = bytearray(8192)
        self.seed[0x0426:0x0428] = (764).to_bytes(2, "little")
        self.seed[0x054E:0x0550] = (764).to_bytes(2, "little")
        rows = []
        for offset in handoff.OFFSETS:
            row = {"offset_from_observed_bowl_result": offset, "fresh_guests": {}}
            for side, subdir in (("original", "ref"), ("native", "native")):
                (self.replay / subdir).mkdir(parents=True, exist_ok=True)
                (self.replay / subdir /
                    f"bowl-next-switcher-{offset}.sram.bin").write_bytes(self.seed)
                row["fresh_guests"][side] = {
                    "in_race": 1 if offset >= 342 else 0, "track": 3,
                    "full_sram_bytes": 8192,
                    "sram_sha256": shared.digest(self.seed),
                    "source_earned_bowl_rank0": {
                        "rank": 0, "value_word": 764, "holder_index": 0},
                    "record_table_checksum_matches": True}
            rows.append(row)
        self.report = {
            "schema_version": 1, "name": "bowl", "course_id": "course:03",
            "family": "stunt", "native_backend": "pinned-baldosa",
            "admission": "investigative candidate; not a release-ledger pass",
            "rom_sha256": target.EXPECTED_ROM,
            "original_movie_sha256": target.EXPECTED_MOVIE,
            "input_sha256": target.expected_script_sha256(),
            "reference_script_sha256": target.expected_script_sha256(),
            "native_executable_sha256": "1" * 64,
            "reference_core_sha256": "2" * 64,
            "source_sram_sha256": "3" * 64,
            "original_movie_window_sha256": "4" * 64,
            "original_source_event": {
                "original_entry_frame": 8620,
                "original_result_frame": 11985,
                "source_active_frames_to_result": 3365,
                "source_stunt_tally_frame": 11915},
            "comparison": {
                "first_sample_disagreement": None,
                "rendered_result_and_score_text_matched": True,
                "intermediate_result_text_matched": True,
                "stunt_positive_score_visible": True,
                "both_reached_terminal_menu": True,
                "terminal_result_guest_frame": {
                    "reference_relative": 3365, "native_relative": 3364}},
            "bowl_next_switcher_handoff": {
                "schema": handoff.SCHEMA,
                "source_original_result_frame": 11985,
                "source_original_next_switcher_frame": 12327,
                "source_next_switcher_entry_offset": 342,
                "source_controller_masks_modified": False,
                "source_earned_bowl_rank0_764_and_checksum_every_sample": True,
                "release_complete_event_credit": 0,
                "original_native_clocks_unrebased": True,
                "cold_process_disk_persistence_proven": False,
                "shipping_windows_candidate_proven": False,
                "sample_offsets": list(handoff.OFFSETS),
                "samples": rows,
            },
        }
        self.boot = self.root / "new"
        for side, subdir in (("original", "ref"), ("native", "native")):
            d = self.boot / side / subdir
            d.mkdir(parents=True)
            for frame in target.BOOT_FRAMES:
                (d / f"cold-{frame:03d}.sram.bin").write_bytes(self.seed)

    def test_authentic_shape_all_150_records_preserved_in_two_cold_boots(self):
        sources = target.validate_source(self.report, self.replay)
        result = target.evaluate_cold(sources, self.boot)
        self.assertEqual(result["source_qualified_bowl_score"], 764)
        self.assertTrue(result["two_independent_new_guest_processes_observed"])
        self.assertTrue(result["fresh_guest_loaded_entire_ranked_table_holders_and_checksum"])
        self.assertFalse(result["complete_original_native_course_fidelity_proven"])
        self.assertFalse(result["actual_host_disk_publication_or_power_failure_proven"])
        self.assertEqual(result["release_complete_usa_event_credit"], 0)

    def test_wrong_original_source_unknown_script_and_malformed_score_fail_closed(self):
        for mutate in (
            lambda x: x["original_source_event"].update({"original_entry_frame": 8621}),
            lambda x: x.update({"input_sha256": "5" * 64}),
            lambda x: x["comparison"]["terminal_result_guest_frame"].update({
                "native_relative": 3362}),
            lambda x: x["bowl_next_switcher_handoff"].update({
                "source_next_switcher_entry_offset": 343}),
            lambda x: x["bowl_next_switcher_handoff"]["samples"][-1][
                "fresh_guests"]["native"].update({"source_earned_bowl_rank0": {
                    "rank": 0, "value_word": 763, "holder_index": 0}}),
        ):
            report = copy.deepcopy(self.report)
            mutate(report)
            with self.subTest(mutate=mutate), self.assertRaises(target.BowlColdEvidenceError):
                target.validate_source(report, self.replay)
        path = self.replay / "native" / "bowl-next-switcher-354.sram.bin"
        path.write_bytes(bytes(8191))
        with self.assertRaises((shared.ColdProofError, target.BowlColdEvidenceError)):
            target.validate_source(self.report, self.replay)

    def test_guest_cold_rewrite_and_missing_original_record_are_negative(self):
        sources = target.validate_source(self.report, self.replay)
        path = self.boot / "native" / "native" / "cold-300.sram.bin"
        image = bytearray(path.read_bytes())
        image[0x0552] = 16
        path.write_bytes(image)
        with self.assertRaisesRegex(target.BowlColdEvidenceError, "rewrote"):
            target.evaluate_cold(sources, self.boot)
        path.write_bytes(self.seed)
        original = self.boot / "original" / "ref" / "cold-420.sram.bin"
        original.unlink()
        with self.assertRaisesRegex(target.BowlColdEvidenceError, "missing actual"):
            target.evaluate_cold(sources, self.boot)

"""Synthetic QA-01 cold-guest source and record contract, never event credit."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_cold_result_record as v


class ColdGuestRecordTests(unittest.TestCase):
    def setUp(self):
        self.ctx = tempfile.TemporaryDirectory()
        self.addCleanup(self.ctx.cleanup)
        self.root = Path(self.ctx.name)
        self.replay = self.root / "replay"
        for s in ("ref", "native"):
            (self.replay / s).mkdir(parents=True)
        self.seed = bytearray(v.SIZE)
        self.seed[0x0424:0x0426] = (2510).to_bytes(2, "little")
        self.seed[0x054E:0x0550] = (2510).to_bytes(2, "little")
        self.seed[0x0551] = 0
        self.boot = self.root / "boot"
        for side, name in (("original", "ref"), ("native", "native")):
            d = self.boot / side / name
            d.mkdir(parents=True)
            for frame in v.BOOT_FRAMES:
                (d / f"cold-{frame:03d}.sram.bin").write_bytes(self.seed)
        self.report = self.source_report()

    def source_report(self):
        receipt = {
            "full_sram_bytes": 8192, "crawler_course_track_index": 1,
            "in_memory_snapshot_only": True,
            "cold_process_reload_proven": False, "sram_sha256": v.digest(self.seed),
            "record_table_checksum_stored": 2510,
            "crawler_record_three_ranks": [
                {"rank": 0, "value_word": 2510, "holder_index": 0},
                {"rank": 1, "value_word": 0, "holder_index": 0},
                {"rank": 2, "value_word": 0, "holder_index": 0}],
        }
        for directory in (self.replay / "ref", self.replay / "native"):
            (directory / "original-follow-72.sram.bin").write_bytes(self.seed)
        return {
            "schema_version": 1, "name": "zoom-zoo",
            "course_id": "course:02", "native_backend": "pinned-baldosa",
            "rom_sha256": v.ROM_SHA, "original_movie_sha256": v.MOVIE_SHA,
            "input_sha256": v.INPUT_SHA,
            "original_source_event": {"original_entry_frame": 3190,
                                      "original_result_frame": 8353},
            "comparison": {
                "terminal_result_guest_frame": {
                    "reference_relative": 5163, "native_relative": 5163},
                "terminal_result_frame_matched": True,
                "rendered_result_and_score_text_matched": True,
                "circuit_multiple_lap_decrements_sampled": True},
            "source_terminal_followthrough": {
                "schema": "UR-QA01-SOURCE-ORIGINAL-NATIVE-RESULT-FOLLOWTHROUGH/2",
                "sample_count": 6, "release_complete_usa_event_credit": 0,
                "battery_sram_cold_process_persistence_proven": False,
                "samples": [
                    {"offset_from_each_observed_result_onset": n,
                     "fresh_guest_battery_sram": {
                         "original": dict(receipt), "native": dict(receipt)}}
                    for n in (8, 16, 24, 32, 64, 72)]}
        }

    def test_reload_preserves_exact_original_native_record_layout(self):
        seeds = v.validate_source(self.report, self.replay)
        result = v.evaluate_cold(seeds, self.boot)
        self.assertEqual(result["source_qualified_best_lap_centiseconds"], 2510)
        self.assertTrue(result["fresh_guest_loaded_ranked_records_and_checksum"])
        self.assertTrue(result["cold_process_record_load_only"])
        self.assertFalse(result["native_host_disk_publish_or_hard_kill_proven"])
        self.assertFalse(result["strict_full_frame_parity_proven"])
        self.assertEqual(result["release_complete_usa_event_credit"], 0)
        self.assertEqual([x["boot_host_frame"] for x in result["boot_observations"]],
                         [300, 420])

    def test_missing_wrong_hash_or_wrong_course_fails_closed(self):
        self.report["source_terminal_followthrough"]["samples"][-1][
            "fresh_guest_battery_sram"]["native"]["sram_sha256"] = "0" * 64
        with self.assertRaisesRegex(v.ColdProofError, "SHA256"):
            v.validate_source(self.report, self.replay)
        self.report = self.source_report()
        self.report["course_id"] = "course:03"
        with self.assertRaisesRegex(v.ColdProofError, "source-pinned"):
            v.validate_source(self.report, self.replay)
        self.report = self.source_report()
        (self.replay / "ref" / "original-follow-72.sram.bin").unlink()
        with self.assertRaisesRegex(v.ColdProofError, "missing SRAM"):
            v.validate_source(self.report, self.replay)

    def test_not_guessed_frame_or_absent_record(self):
        self.report["comparison"]["terminal_result_guest_frame"]["native_relative"] = 5162
        with self.assertRaisesRegex(v.ColdProofError, "corrected"):
            v.validate_source(self.report, self.replay)
        self.report = self.source_report()
        self.seed[0x0424:0x0426] = (60000).to_bytes(2, "little")
        (self.replay / "native" / "original-follow-72.sram.bin").write_bytes(self.seed)
        with self.assertRaisesRegex(v.ColdProofError, "wrong size or SHA256"):
            v.validate_source(self.report, self.replay)

    def test_cold_boot_does_not_accept_just_one_side_or_invalid_checksum(self):
        seeds = v.validate_source(self.report, self.replay)
        bad = self.boot / "native" / "native" / "cold-420.sram.bin"
        data = bytearray(bad.read_bytes())
        data[0x054E] ^= 1
        bad.write_bytes(data)
        with self.assertRaisesRegex(v.ColdProofError, "lost or rewrote"):
            v.evaluate_cold(seeds, self.boot)
        bad.unlink()
        with self.assertRaisesRegex(v.ColdProofError, "missing fresh-process"):
            v.evaluate_cold(seeds, self.boot)


    def test_real_extended_movie_script_is_exactly_source_bound(self):
        # The +280 Zoo -> Bowl dump schedule changes only the replay-script
        # hash, not the archived 2014 ROM, movie or its controller masks.
        self.report["input_sha256"] = v.NEXT_BOWL_INPUT_SHA
        self.report["reference_script_sha256"] = v.NEXT_BOWL_INPUT_SHA
        self.report["original_movie_window_sha256"] = v.NEXT_BOWL_MOVIE_WINDOW_SHA
        self.report["zoo_next_bowl_handoff"] = {
            "source_next_bowl_active_entry_offset": 267,
            "fresh_reference_next_bowl_entry_offset": 267,
            "fresh_native_next_bowl_entry_offset": 267,
            "next_bowl_entry_triple_equal": True,
            "all_original_native_full_sram_pairs_equal": True,
            "release_complete_event_credit": 0,
        }
        seeds = v.validate_source(self.report, self.replay)
        self.assertEqual(set(seeds), {"original", "native"})
        self.assertFalse(v.evaluate_cold(seeds, self.boot)[
            "native_host_disk_publish_or_hard_kill_proven"])

        import copy
        good = copy.deepcopy(self.report)
        for alteration in (
                {"original_movie_window_sha256": "0" * 64},
                {"reference_script_sha256": v.INPUT_SHA},
                {"zoo_next_bowl_handoff": None},
                {"zoo_next_bowl_handoff": {
                    **good["zoo_next_bowl_handoff"],
                    "fresh_native_next_bowl_entry_offset": 265}},
                {"zoo_next_bowl_handoff": {
                    **good["zoo_next_bowl_handoff"],
                    "all_original_native_full_sram_pairs_equal": False}},
                {"zoo_next_bowl_handoff": {
                    **good["zoo_next_bowl_handoff"],
                    "release_complete_event_credit": 1}},
        ):
            bad = copy.deepcopy(good)
            bad.update(alteration)
            with self.assertRaisesRegex(v.ColdProofError,
                                        "source movie/window/handoff"):
                v.validate_source(bad, self.replay)
        bad = copy.deepcopy(good)
        bad["input_sha256"] = "1" * 64
        with self.assertRaisesRegex(v.ColdProofError, "unknown original"):
            v.validate_source(bad, self.replay)


    def composite_mesh_report(self):
        import copy
        report = copy.deepcopy(self.report)
        report["input_sha256"] = v.COMPOSITE_MESH_NEXT_BOWL_INPUT_SHA
        report["reference_script_sha256"] = v.COMPOSITE_MESH_NEXT_BOWL_INPUT_SHA
        report["original_movie_window_sha256"] = v.NEXT_BOWL_MOVIE_WINDOW_SHA
        report["reference_entry"] = 1017
        report["native_entry"] = 1017
        report["zoo_next_bowl_handoff"] = {
            "source_next_bowl_active_entry_offset": 267,
            "fresh_reference_next_bowl_entry_offset": 267,
            "fresh_native_next_bowl_entry_offset": 267,
            "next_bowl_entry_triple_equal": True,
            "all_original_native_full_sram_pairs_equal": True,
            "release_complete_event_credit": 0,
        }
        offsets = v.original.sample_frames("zoom-zoo", 5163,
                                          zoo_race_mesh=True,
                                          zoo_dp_window=True)
        report["zoo_race_mesh"] = {
            "schema": "UR-QA01-ZOO-FULL-RACE-UNMASKED-WRAM-MESH/1",
            "archived_source_active_frames_to_result": 5163,
            "original_2014_source_controller_masks_modified": False,
            "masked_or_excluded_wram_bytes": 0,
            "all_128k_wram_bytes_examined_per_pair": 131072,
            "mesh_checkpoint_count": len(offsets),
            "last_race_relative_checkpoint": 5120,
            "every_gameplay_frame_compared": False,
            "release_complete_usa_event_credit": 0,
            "samples": [{
                "race_relative_frame": f,
                "original_absolute_host_frame": 1017 + f,
                "native_absolute_host_frame": 1017 + f,
                "original_native_full_wram_byte_difference": {
                    "every_byte_compared": True,
                    "full_wram_bytes_per_guest": 131072,
                    "excluded_byte_count": 0,
                    "differing_byte_count": 0,
                },
            } for f in offsets],
            "late_direct_page_window": {
                "schema": "UR-QA01-ZOO-5040-DENSE-DP-WRAM/1",
                "range_inclusive": [5034, 5046],
                "all_guest_frames_in_range_captured": True,
                "raw_wram_bytes_excluded": 0,
                "release_complete_event_credit": 0,
                "samples": [
                    {"race_relative_frame": f} for f in range(5034, 5047)],
            },
        }
        self.assertEqual(len(offsets), 78)
        return report

    def test_authentic_composite_replay_script_is_cold_guest_eligible(self):
        # This is a source-contract synthetic unit test, NOT a real game run.
        report = self.composite_mesh_report()
        self.assertEqual(set(v.validate_source(report, self.replay)),
                         {"original", "native"})
        for mutate, failure in (
                (lambda r: r["zoo_race_mesh"]["samples"].pop(), "source mesh"),
                (lambda r: r["zoo_race_mesh"]["samples"][60].update(
                    {"original_absolute_host_frame": 0}), "mesh frame"),
                (lambda r: r["zoo_race_mesh"].update(
                    {"masked_or_excluded_wram_bytes": 4}), "source mesh"),
                (lambda r: r["zoo_race_mesh"]["samples"][1][
                    "original_native_full_wram_byte_difference"].update(
                    {"excluded_byte_count": 1}), "mesh frame"),
                (lambda r: r["zoo_race_mesh"]["late_direct_page_window"][
                    "samples"].pop(), "SPC window"),
                (lambda r: r.update(
                    {"original_movie_window_sha256": "0" * 64}),
                 "source movie/window/handoff"),
                (lambda r: r["zoo_next_bowl_handoff"].update(
                    {"fresh_native_next_bowl_entry_offset": 265}),
                 "source movie/window/handoff"),
        ):
            import copy
            altered = copy.deepcopy(report)
            mutate(altered)
            with self.subTest(failure=failure), self.assertRaisesRegex(
                    v.ColdProofError, failure):
                v.validate_source(altered, self.replay)

    def test_composite_script_cannot_be_passed_off_as_short_source_replay(self):
        report = self.composite_mesh_report()
        report["zoo_race_mesh"] = None
        with self.assertRaisesRegex(v.ColdProofError, "source mesh"):
            v.validate_source(report, self.replay)
        report = self.composite_mesh_report()
        report["input_sha256"] = "1" * 64
        with self.assertRaisesRegex(v.ColdProofError, "unknown original"):
            v.validate_source(report, self.replay)

    def test_native_wrapper_places_real_sram_seed_in_guest_cwd_not_elf_directory(self):
        # Actual pinned host with --config does NOT chdir to executable dir.
        # Mock the process only to inspect exactly what its RtlReadSram sees.
        from types import SimpleNamespace
        from unittest import mock
        import probe_original_event_complete as producer
        guest = self.root / "guest"
        guest.mkdir()
        (guest / "saves").mkdir()
        (guest / "saves" / "save.srm").write_bytes(b"untouched old guest")
        elf_dir = self.root / "bin"
        elf_dir.mkdir()
        (elf_dir / "saves").mkdir()
        (elf_dir / "saves" / "save.srm").write_bytes(b"wrong old executable-neighbor save")
        src = self.root / "genuine.srm"
        src.write_bytes(self.seed)
        script = guest / "cold.script"
        script.write_text("wait 1\ndump boot\nquit\n")
        args = SimpleNamespace(native=elf_dir / "native", rom=self.root / "usa.sfc",
                               sram=src)
        called = []

        def fake_run(argv, **kwargs):
            self.assertEqual(kwargs["cwd"], guest)
            self.assertIn("--config", argv)
            self.assertEqual((guest / "saves" / "save.srm").read_bytes(), self.seed)
            self.assertEqual((elf_dir / "saves" / "save.srm").read_bytes(),
                             b"wrong old executable-neighbor save")
            called.append(True)
            return SimpleNamespace(returncode=0, stdout="script f=1 dump boot ok\n",
                                   stderr="")

        with mock.patch.object(producer.subprocess, "run", side_effect=fake_run):
            log = producer.run_pinned_baldosa(guest, args, script, [], 0)
        self.assertIn("script f=1 dump boot", log)
        self.assertEqual(called, [True])
        self.assertEqual((guest / "saves" / "save.srm").read_bytes(),
                         b"untouched old guest")
        self.assertFalse((guest / "saves.qa01-bowl-recovery").exists())


    def test_campaign_retains_four_raw_cold_guest_sram_witnesses(self):
        # This is a workflow source contract, not a cold guest execution.
        # The 2026-10-28 sequence-17 ZIP retained only the JSON receipt,
        # preventing independent rehash of its four fresh-boot SRAM images.
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text(
            encoding="utf-8")
        upload = workflow.split(
            "name: Always retain per-case receipt and bounded diagnostic logs", 1)[1]
        upload = upload.split("\n  aggregate:", 1)[0]
        for side, directory in (("original", "original/ref"),
                                ("native", "native/native")):
            for frame in v.BOOT_FRAMES:
                path = ("qa01-case/qa01-cold-guest-boot/" + directory
                        + f"/cold-{frame:03d}.sram.bin")
                with self.subTest(side=side, frame=frame):
                    self.assertEqual(upload.count(path), 1)
        self.assertIn("qa01-case/qa01-cold-guest-report.json", upload)
        result = v.evaluate_cold(v.validate_source(self.report, self.replay),
                                 self.boot)
        self.assertFalse(result["native_host_disk_publish_or_hard_kill_proven"])


if __name__ == "__main__":
    unittest.main()

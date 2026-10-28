"""Synthetic tests for QA-01 campaign transport. No emulation or QA admission."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_event_campaign as c


def producer(case: str, *, matched: bool = False) -> dict:
    original = 5163
    native = original if matched else original - 1
    return {
        "schema_version": 1,
        "name": case,
        "course_id": c.CASES[case]["course_id"],
        "family": c.CASES[case]["family"],
        "native_backend": "pinned-baldosa",
        "admission": "investigative candidate; not a release-ledger pass",
        "original_source_event": {
            "original_entry_frame": 3190,
            "original_result_frame": 3190 + original,
            "source_active_frames_to_result": original,
        },
        "reference_entry": 984,
        "native_entry": 986,
        "native_frame_shift": 2,
        "comparison": {
            "paired_event_candidate": matched,
            "terminal_result_frame_matched": matched,
            "terminal_result_guest_frame": {
                "reference_relative": original,
                "native_relative": native,
            },
            "first_sample_disagreement": None if matched else {"relative_frame": 100},
            **{gate: True for gate in c.STRICT_PRODUCER_GATES},
            "diagnostic_exit_success_without_full_event_parity": False,
        },
        **{key: "a" * 64 for key in (
            "rom_sha256", "original_movie_sha256",
            "native_executable_sha256", "reference_core_sha256",
            "input_sha256", "source_sram_sha256",
            "original_movie_window_sha256", "reference_script_sha256")},
    }


def postresult_fixture(*, first_native_divergence: int | None = 16) -> dict:
    """Synthetic three-clock test only; NOT a genuine emulator witness."""
    report = producer("zoom-zoo", matched=True)
    offsets = c.FOLLOWTHROUGH_OFFSETS
    source = {}
    captures = []
    for offset in offsets:
        source_row = {
            "original_movie_host_frame": 8353 + offset,
            "menu": 0xBC if offset <= 16 else 0xF6,
            "track": 1, "in_race": 0x3D,
        }
        source[str(offset)] = source_row
        original = {
            "menu": source_row["menu"], "track": 1, "in_race": 0x3D,
            "p1_laps": 0, "p2_laps": 0,
            "p1_checkpoint": 1, "p1_finish_gate": 1,
            "full_wram_bytes": 0x20000, "wram_sha256": "a" * 64,
        }
        native = dict(original)
        if offset == first_native_divergence:
            native["menu"] = 0xF6 if original["menu"] != 0xF6 else 0xBC
            native["wram_sha256"] = "b" * 64
        diff = [k for k in c.FOLLOWTHROUGH_SOURCE
                if original[k] != native[k]]
        captures.append({
            "offset_from_each_observed_result_onset": offset,
            "source_original_movie": source_row,
            "independently_observed_replay_host_frames": {
                "original": 984 + 5163 + offset,
                "native": 986 + 5163 + offset,
            },
            "fresh_guests": {"original": original, "native": native},
            "source_named_state_comparison": {
                "original": {"source_named_state_equal": True,
                             "named_fields_different_from_source": []},
                "native": {"source_named_state_equal": not diff,
                           "named_fields_different_from_source": diff},
            },
            "paired_named_state_equal": not diff,
            "full_wram_bytes_equal": native["wram_sha256"] == original["wram_sha256"],
        })
    report["original_source_event"]["source_terminal_followthrough"] = source
    report["source_terminal_followthrough"] = {
        "schema": c.FOLLOWTHROUGH_SCHEMA,
        "sample_count": 6,
        "samples": captures,
        "source_guest_relative_result_onset_equivalence_proven": False,
        "original_and_native_result_phase_equal_proven": True,
        "all_followthrough_named_pairs_equal": first_native_divergence is None,
        "all_followthrough_full_wram_pairs_equal": first_native_divergence is None,
        "post_result_sram_persistence_proven": False,
        "menu_restoration_or_final_progression_proven": False,
        "strict_event_comparator_unchanged": True,
        "release_complete_usa_event_credit": 0,
    }
    return report


def battery_followthrough_fixture(*, changed_course_rank: bool = True) -> dict:
    """Only a synthetic integrity test for the read-only SRAM reporter."""
    report = postresult_fixture(first_native_divergence=None)
    record = report["source_terminal_followthrough"]
    for row in record["samples"]:
        offset = row["offset_from_each_observed_result_onset"]
        rank = [
            {"rank": n, "value_word": 2510 if n == 0 else 60000,
             "holder_index": 0 if n == 0 else 16}
            for n in range(3)
        ]
        base = {
            "full_sram_bytes": 8192, "sram_sha256": "a" * 64,
            "crawler_course_track_index": 1,
            "crawler_record_three_ranks": rank,
            "record_table_checksum_stored": 0,
            "record_table_checksum_calculated": 0,
            "record_table_checksum_matches_at_sample": True,
            "in_memory_snapshot_only": True,
            "cold_process_reload_proven": False,
        }
        original = json.loads(json.dumps(base))
        native = json.loads(json.dumps(base))
        if changed_course_rank and offset == 16:
            native["sram_sha256"] = "b" * 64
            native["crawler_record_three_ranks"][0]["value_word"] = 2420
            native["record_table_checksum_calculated"] = 1
            native["record_table_checksum_matches_at_sample"] = False
        row["fresh_guest_battery_sram"] = {
            "original": original, "native": native}
        row["sram_full_bytes_equal"] = (
            original["sram_sha256"] == native["sram_sha256"])
        row["sram_course_three_rank_records_equal"] = (
            original["crawler_record_three_ranks"] ==
            native["crawler_record_three_ranks"])
    record["all_followthrough_full_sram_pairs_equal"] = not changed_course_rank
    record["all_followthrough_crawler_record_pairs_equal"] = not changed_course_rank
    record["battery_sram_snapshot_bytes_per_guest"] = 8192
    record["battery_sram_cold_process_persistence_proven"] = False
    return report


class QA01CampaignTest(unittest.TestCase):
    SHA = "b" * 40

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def plan(self, selection="all"):
        return c.make_plan(selection, self.SHA)

    def report_file(self, case="bowl", *, matched=False):
        path = self.root / "producer.json"
        c.write_json(path, producer(case, matched=matched))
        return path

    def test_plan_is_allowlisted_bounded_and_sha_bound(self):
        plan = self.plan()
        self.assertEqual([r["id"] for r in plan["cases"]],
                         ["zoom-zoo", "bowl", "switcher"])
        self.assertEqual(len(plan["matrix"]["include"]), 3)
        c.validate_plan(plan)
        self.assertEqual(len(self.plan("switcher")["cases"]), 1)
        for selection in ("45", "race", "../bowl", ""):
            with self.assertRaises(ValueError):
                self.plan(selection)
        for bad_sha in ("a" * 39, "A" * 40, "g" * 40):
            with self.assertRaises(ValueError):
                c.make_plan("all", bad_sha)
        corrupt = dict(plan, plan_sha256="0" * 64)
        with self.assertRaises(ValueError):
            c.validate_plan(corrupt)

    def test_negative_strict_comparison_remains_negative_even_diagnostic_success(self):
        plan = self.plan("bowl")
        path = self.report_file()
        result = c.classify("bowl", 1, path, plan)
        self.assertEqual(result["disposition"], "strict_divergence")
        self.assertEqual(result["release_credit"], 0)
        record = producer("bowl")
        record["comparison"]["diagnostic_exit_success_without_full_event_parity"] = True
        c.write_json(path, record)
        diagnostic = c.classify("bowl", 0, path, plan)
        self.assertEqual(diagnostic["disposition"], "strict_divergence")
        self.assertEqual(diagnostic["release_credit"], 0)

    def test_strict_candidate_requires_consistent_complete_producer_evidence(self):
        plan = self.plan("bowl")
        path = self.report_file(matched=True)
        result = c.classify("bowl", 0, path, plan)
        self.assertEqual(result["disposition"], "strict_candidate")
        self.assertEqual(result["release_credit"], 0)
        self.assertIn("NOT", result["reason"])
        self.assertRegex(result["evidence"]["producer_sha256"], r"^[0-9a-f]{64}$")
        failed = c.classify("bowl", 1, path, plan)
        self.assertEqual(failed["disposition"], "producer_error")

    def test_strict_candidate_fails_closed_on_contradictory_producer_gates(self):
        plan = self.plan("zoom-zoo")
        target = self.root / "strict-gate.json"
        for key in c.STRICT_PRODUCER_GATES:
            with self.subTest(gate=key):
                report = producer("zoom-zoo", matched=True)
                report["comparison"][key] = False
                c.write_json(target, report)
                rejected = c.classify("zoom-zoo", 0, target, plan)
                self.assertEqual(rejected["disposition"], "producer_error")
                self.assertIn("contradicts", rejected["reason"])
                self.assertEqual(rejected["release_credit"], 0)
        for mutation in (
            lambda p: p["comparison"].pop("fresh_guest_entry_equivalent"),
            lambda p: p["comparison"].__setitem__("stunt_positive_score_visible", 1),
            lambda p: p["comparison"].__setitem__(
                "first_sample_disagreement", {"relative_frame": 42}),
        ):
            report = producer("zoom-zoo", matched=True)
            mutation(report)
            c.write_json(target, report)
            self.assertEqual(c.classify("zoom-zoo", 0, target, plan)[
                             "disposition"], "producer_error")
        valid = producer("zoom-zoo", matched=True)
        c.write_json(target, valid)
        admitted = c.classify("zoom-zoo", 0, target, plan)
        self.assertEqual(admitted["disposition"], "strict_candidate")
        self.assertTrue(admitted["evidence"]["strict_producer_gate_audit"][
            "recomputed_candidate"])
        self.assertEqual(admitted["release_credit"], 0)

    def test_real_actions_case_mixed_upload_root_is_a_completed_case(self):
        plan=self.plan("zoom-zoo")
        row=c.classify("zoom-zoo",0,self.report_file("zoom-zoo",matched=True),plan)
        directory=self.root/"multi-root"/"qa01-campaign-case-zoom-zoo"
        c.write_json(directory/"qa01-case"/"case-result.json",row)
        # Extra research output changes Actions' common upload ancestor,
        # but must not relabel a completed actual case as missing evidence.
        (directory/"qa01-rf062-ab"/"off").mkdir(parents=True)
        result,_=c.aggregate(plan,self.root/"multi-root")
        self.assertTrue(result["transport_complete"])
        self.assertEqual(result["counts"]["strict_candidate"],1)
        self.assertEqual(result["release_admissions"],0)
        self.assertEqual(c.exact_case_artifact_root(directory),directory/"qa01-case")

    def test_ambiguous_or_symlinked_nested_case_receipts_are_not_selected(self):
        plan=self.plan("zoom-zoo")
        row=c.classify("zoom-zoo",0,self.report_file("zoom-zoo",matched=True),plan)
        directory=self.root/"multi-root"/"qa01-campaign-case-zoom-zoo"
        c.write_json(directory/"qa01-case"/"case-result.json",row)
        c.write_json(directory/"case-result.json",row)
        with self.assertRaisesRegex(ValueError,"ambiguous"):
            c.exact_case_artifact_root(directory)
        invalid,_=c.aggregate(plan,self.root/"multi-root")
        self.assertFalse(invalid["transport_complete"])
        self.assertEqual(invalid["counts"]["missing_evidence"],1)
        (directory/"case-result.json").unlink()
        (directory/"qa01-case"/"case-result.json").unlink()
        (directory/"qa01-case").rmdir()
        (directory/"qa01-case").symlink_to(self.root/"multi-root",target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"symlinked"):
            c.exact_case_artifact_root(directory)
        still_invalid,_=c.aggregate(plan,self.root/"multi-root")
        self.assertEqual(still_invalid["release_admissions"],0)

    def test_distributed_aggregate_rejects_corrupted_strict_gate_receipt(self):
        plan = self.plan("zoom-zoo")
        path = self.report_file("zoom-zoo", matched=True)
        row = c.classify("zoom-zoo", 0, path, plan)
        folder = self.root / "distributed" / "qa01-campaign-case-zoom-zoo"
        path = folder / "case-result.json"
        c.write_json(path, row)
        self.assertTrue(c.aggregate(plan, self.root / "distributed")[0][
            "transport_complete"])
        for mutate in (
            lambda a: a["gates"].__setitem__("rendered_result_and_score_text_matched", False),
            lambda a: a["gates"].pop("fresh_guest_entry_equivalent"),
            lambda a: a.__setitem__("recomputed_candidate", False),
        ):
            corrupted = json.loads(json.dumps(row))
            mutate(corrupted["evidence"]["strict_producer_gate_audit"])
            c.write_json(path, corrupted)
            aggregated, _ = c.aggregate(plan, self.root / "distributed")
            self.assertEqual(aggregated["counts"]["missing_evidence"], 1)
            self.assertEqual(aggregated["release_admissions"], 0)

    def test_strict_result_candidate_with_divergent_menu_remains_investigative(self):
        report = postresult_fixture()
        plan = self.plan("zoom-zoo")
        path = self.root / "source-followthrough.json"
        c.write_json(path, report)
        result = c.classify("zoom-zoo", 0, path, plan)
        self.assertEqual(result["disposition"], "strict_candidate")
        self.assertEqual(result["release_credit"], 0)
        bounded = result["evidence"]["post_result_bounded"]
        self.assertEqual(bounded["status"], "sampled_named_divergence")
        self.assertEqual(bounded["samples"], 6)
        self.assertEqual(bounded["first_named_divergence_offset"], 16)
        self.assertEqual(bounded["named_divergences"][0][
            "native_vs_fresh_original"], ["menu"])
        self.assertFalse(bounded["all_fresh_wram_sha256_pairs_equal"])
        self.assertIn("result-relative +16", result["reason"])
        self.assertFalse(bounded["unsampled_frames_or_persistence_proven"])
        aggregate_dir = self.root / "qa01-case"
        c.write_json(aggregate_dir /
                     "qa01-campaign-case-zoom-zoo/case-result.json", result)
        summary, _ = c.aggregate(plan, aggregate_dir)
        self.assertTrue(summary["transport_complete"])
        self.assertEqual(summary["release_admissions"], 0)

    def test_bounded_six_sample_agreement_never_grants_full_event(self):
        plan = self.plan("zoom-zoo")
        path = self.root / "bounded-match.json"
        c.write_json(path, postresult_fixture(first_native_divergence=None))
        result = c.classify("zoom-zoo", 0, path, plan)
        self.assertEqual(result["disposition"], "strict_candidate")
        self.assertEqual(result["evidence"]["post_result_bounded"]["status"],
                         "six_sample_triplet_named_agreement")
        self.assertIsNone(result["evidence"]["post_result_bounded"][
            "first_named_divergence_offset"])
        self.assertEqual(result["release_credit"], 0)
        self.assertFalse(result["evidence"]["post_result_bounded"][
            "unsampled_frames_or_persistence_proven"])
        # Producer without the option cannot silently imply lifecycle parity.
        c.write_json(path, producer("zoom-zoo", matched=True))
        absent = c.classify("zoom-zoo", 0, path, plan)
        self.assertEqual(absent["evidence"]["post_result_bounded"],
                         {"status": "not_observed", "samples": 0,
                          "first_named_divergence_offset": None,
                          "release_credit": 0})

    def test_source_qualified_original_native_course_records_are_in_memory_only(self):
        path = self.root / "sram-paired.json"
        plan = self.plan("zoom-zoo")
        c.write_json(path, battery_followthrough_fixture())
        row = c.classify("zoom-zoo", 0, path, plan)
        self.assertEqual(row["disposition"], "strict_candidate")
        self.assertEqual(row["release_credit"], 0)
        p = row["evidence"]["post_result_bounded"]
        self.assertEqual(p["status"], "six_sample_triplet_named_agreement")
        battery = p["fresh_original_native_battery_sram"]
        self.assertEqual(battery["status"],
                         "six_sample_original_native_in_memory_sram_observed")
        self.assertFalse(battery["all_fresh_sram_byte_pairs_equal"])
        self.assertFalse(battery["all_fresh_crawler_ranked_record_pairs_equal"])
        self.assertEqual(battery["first_full_sram_difference_offset"], 16)
        self.assertEqual(battery["first_course_record_difference_offset"], 16)
        self.assertFalse(battery["cold_process_persistence_proven"])
        c.write_json(path, battery_followthrough_fixture(changed_course_rank=False))
        matching = c.classify("zoom-zoo", 0, path, plan)
        got = matching["evidence"]["post_result_bounded"][
            "fresh_original_native_battery_sram"]
        self.assertTrue(got["all_fresh_sram_byte_pairs_equal"])
        self.assertTrue(got["all_fresh_crawler_ranked_record_pairs_equal"])
        self.assertIsNone(got["first_course_record_difference_offset"])
        self.assertEqual(matching["release_credit"], 0)

    def test_forged_battery_records_do_not_become_a_scientific_negative(self):
        plan = self.plan("zoom-zoo")
        path = self.root / "sram-invalid.json"
        def change_checksum_claim(x):
            x["source_terminal_followthrough"]["samples"][1][
                "fresh_guest_battery_sram"]["native"][
                    "record_table_checksum_matches_at_sample"] = True
        def change_track_identity(x):
            x["source_terminal_followthrough"]["samples"][1][
                "fresh_guest_battery_sram"]["native"][
                    "crawler_course_track_index"] = 4
        def claim_disk_persistence(x):
            x["source_terminal_followthrough"][
                "battery_sram_cold_process_persistence_proven"] = True
        def change_hash(x):
            x["source_terminal_followthrough"]["samples"][1][
                "fresh_guest_battery_sram"]["native"]["sram_sha256"] = "bad"
        def change_record(x):
            x["source_terminal_followthrough"]["samples"][1][
                "fresh_guest_battery_sram"]["native"][
                    "crawler_record_three_ranks"][0]["rank"] = 5
        def remove_one_snapshot(x):
            x["source_terminal_followthrough"]["samples"][0].pop(
                "fresh_guest_battery_sram")
        def falsify_equal_flag(x):
            x["source_terminal_followthrough"]["samples"][1][
                "sram_full_bytes_equal"] = True
        def falsify_global_equal(x):
            x["source_terminal_followthrough"][
                "all_followthrough_crawler_record_pairs_equal"] = True
        for mutate in (change_checksum_claim, change_track_identity,
                       claim_disk_persistence, change_hash, change_record,
                       remove_one_snapshot, falsify_equal_flag,
                       falsify_global_equal):
            with self.subTest(tweak=mutate.__name__):
                v = battery_followthrough_fixture()
                mutate(v)
                c.write_json(path, v)
                verdict = c.classify("zoom-zoo", 0, path, plan)
                self.assertEqual(verdict["disposition"], "producer_error")
                self.assertEqual(verdict["release_credit"], 0)

    def test_postresult_report_must_reconcile_actual_triplet_host_receipts(self):
        plan = self.plan("zoom-zoo")
        path = self.root / "tampered-followthrough.json"
        def mutate_native_time(p):
            p["source_terminal_followthrough"]["samples"][1][
                "independently_observed_replay_host_frames"]["native"] += 1
        def mutate_source_frame(p):
            p["original_source_event"]["source_terminal_followthrough"]["16"][
                "original_movie_host_frame"] += 1
        def mutate_source_copy(p):
            p["source_terminal_followthrough"]["samples"][1][
                "source_original_movie"]["menu"] = 0xF6
        def mutate_menu_pair_flag(p):
            p["source_terminal_followthrough"]["samples"][1][
                "paired_named_state_equal"] = True
        def mutate_native_movie_claim(p):
            p["source_terminal_followthrough"]["samples"][1][
                "source_named_state_comparison"]["native"][
                    "source_named_state_equal"] = True
        def mutate_raw_sha_pair_flag(p):
            p["source_terminal_followthrough"]["samples"][1][
                "full_wram_bytes_equal"] = True
        def mutate_strict_result(p):
            p["source_terminal_followthrough"][
                "original_and_native_result_phase_equal_proven"] = False
        def mutate_sram_claim(p):
            p["source_terminal_followthrough"][
                "post_result_sram_persistence_proven"] = True
        def mutate_credited(p):
            p["source_terminal_followthrough"][
                "release_complete_usa_event_credit"] = 1
        def mutate_missing_source(p):
            p["original_source_event"].pop("source_terminal_followthrough")
        def mutate_summary(p):
            p["source_terminal_followthrough"][
                "all_followthrough_named_pairs_equal"] = True
        def mutate_duplicate_sample(p):
            p["source_terminal_followthrough"]["samples"][2][
                "offset_from_each_observed_result_onset"] = 16
        for tweak in (
            mutate_native_time, mutate_source_frame, mutate_source_copy,
            mutate_menu_pair_flag, mutate_native_movie_claim,
            mutate_raw_sha_pair_flag, mutate_strict_result,
            mutate_sram_claim, mutate_credited, mutate_missing_source,
            mutate_summary, mutate_duplicate_sample,
        ):
            with self.subTest(tweak=tweak.__name__):
                report = postresult_fixture()
                tweak(report)
                c.write_json(path, report)
                out = c.classify("zoom-zoo", 0, path, plan)
                self.assertEqual(out["disposition"], "producer_error")
                self.assertEqual(out["release_credit"], 0)

    def test_invalid_identity_provenance_or_frame_is_not_scientific_negative(self):
        plan = self.plan("bowl")
        path = self.report_file()
        for change in (
            {"name": "switcher"},
            {"native_backend": "legacy"},
            {"rom_sha256": "not-a-hash"},
            {"admission": "accepted"},
            {"course_id": "course:04"},
        ):
            bad = {**producer("bowl"), **change}
            c.write_json(path, bad)
            self.assertEqual(c.classify("bowl", 1, path, plan)["disposition"],
                             "producer_error")
        bad = producer("bowl")
        bad["comparison"]["terminal_result_frame_matched"] = True
        c.write_json(path, bad)
        self.assertEqual(c.classify("bowl", 1, path, plan)["disposition"],
                         "producer_error")
        self.assertEqual(c.classify("bowl", 124, self.root/"absent.json", plan)[
                         "disposition"], "producer_error")

    def test_archived_movie_and_fresh_guest_timing_provenance_fails_closed(self):
        plan = self.plan("zoom-zoo")
        good = self.report_file("zoom-zoo", matched=True)
        row = c.classify("zoom-zoo", 0, good, plan)
        self.assertEqual(row["disposition"], "strict_candidate")
        ev = row["evidence"]
        self.assertEqual(ev["original_movie_entry_frame"], 3190)
        self.assertEqual(ev["original_movie_result_frame"], 8353)
        self.assertEqual(ev["original_event_frames"], 5163)
        self.assertEqual(ev["native_entry_frame"] - ev["reference_entry_frame"],
                         ev["native_frame_shift"])
        self.assertEqual(ev["source_sram_sha256"], "a" * 64)
        self.assertEqual(ev["original_movie_window_sha256"], "a" * 64)
        self.assertEqual(ev["reference_script_sha256"], "a" * 64)
        self.assertEqual(row["release_credit"], 0)
        # The observed shift is signed. A native guest that enters earlier
        # than the original may still be a valid, independently calibrated
        # experiment; never clamp or silently rebase its controller movie.
        earlier = producer("zoom-zoo", matched=True)
        earlier["native_entry"] = 982
        earlier["native_frame_shift"] = -2
        c.write_json(good, earlier)
        valid_earlier = c.classify("zoom-zoo", 0, good, plan)
        self.assertEqual(valid_earlier["disposition"], "strict_candidate")
        self.assertEqual(valid_earlier["evidence"]["native_frame_shift"], -2)
        self.assertEqual(valid_earlier["release_credit"], 0)
        for mutate in (
            lambda v: v.pop("original_movie_window_sha256"),
            lambda v: v.__setitem__("reference_script_sha256", "not-a-sha"),
            lambda v: v.__setitem__("source_sram_sha256", "unverified"),
            lambda v: v.__setitem__("native_frame_shift", 3),
            lambda v: v.__setitem__("native_entry", True),
            lambda v: v["original_source_event"].__setitem__(
                "original_result_frame", 8354),
            lambda v: v["original_source_event"].__setitem__(
                "original_entry_frame", -1),
            lambda v: v["original_source_event"].__setitem__(
                "source_active_frames_to_result", 0),
        ):
            with self.subTest(mutate=repr(mutate)):
                candidate = producer("zoom-zoo", matched=True)
                mutate(candidate)
                c.write_json(good, candidate)
                bad = c.classify("zoom-zoo", 0, good, plan)
                self.assertEqual(bad["disposition"], "producer_error")
                self.assertEqual(bad["release_credit"], 0)

    def test_three_independent_source_movie_original_native_result_clocks(self):
        plan = self.plan("switcher")
        path = self.root / "three-clocks.json"
        report = producer("switcher", matched=True)
        # Genuine archived Switcher source: 12327 -> 17030 = +4703;
        # same freshly replayed original/native guest relative result +4704.
        report["original_source_event"].update(
            original_entry_frame=12327,
            original_result_frame=17030,
            source_active_frames_to_result=4703)
        report["comparison"]["terminal_result_guest_frame"] = {
            "reference_relative": 4704, "native_relative": 4704}
        c.write_json(path, report)
        case = c.classify("switcher", 0, path, plan)
        self.assertEqual(case["disposition"], "strict_candidate")
        self.assertEqual(case["release_credit"], 0)
        witness = case["evidence"]["source_original_movie_vs_fresh_guest_result_phase"]
        self.assertEqual([witness[k] for k in (
            "source_original_movie_relative", "fresh_original_relative",
            "fresh_native_relative")], [4703, 4704, 4704])
        self.assertEqual(witness["fresh_original_minus_source_frames"], 1)
        self.assertEqual(witness["fresh_native_minus_source_frames"], 1)
        self.assertFalse(witness["three_relative_durations_equal"])
        self.assertFalse(witness["continuous_original_to_fresh_equivalence_proven"])
        self.assertIn("source/movie timing equivalence NOT established", case["reason"])
        folder = self.root / "switcher-results" / "qa01-campaign-case-switcher"
        c.write_json(folder / "case-result.json", case)
        summary, md = c.aggregate(plan, self.root / "switcher-results")
        self.assertTrue(summary["transport_complete"])
        self.assertEqual(
            summary["source_movie_to_fresh_result_duration_difference_cases"], 1)
        self.assertIn("relative result offset: 1", md)
        self.assertEqual(summary["release_admissions"], 0)
        for mutation in (
            lambda r: r.pop("source_original_movie_vs_fresh_guest_result_phase"),
            lambda r: r["source_original_movie_vs_fresh_guest_result_phase"].__setitem__(
                "fresh_original_minus_source_frames", 0),
            lambda r: r["source_original_movie_vs_fresh_guest_result_phase"].__setitem__(
                "three_relative_durations_equal", True),
            lambda r: r["source_original_movie_vs_fresh_guest_result_phase"].__setitem__(
                "continuous_original_to_fresh_equivalence_proven", True),
            lambda r: r["source_original_movie_vs_fresh_guest_result_phase"].__setitem__(
                "release_credit", 1),
        ):
            with self.subTest(mutation=repr(mutation)):
                tampered = json.loads(json.dumps(case))
                mutation(tampered["evidence"])
                c.write_json(folder / "case-result.json", tampered)
                rejected, _ = c.aggregate(plan, self.root / "switcher-results")
                self.assertFalse(rejected["transport_complete"])
                self.assertEqual(rejected["counts"]["missing_evidence"], 1)
                self.assertEqual(rejected["release_admissions"], 0)

    def test_matching_source_movie_duration_is_still_not_release_credit(self):
        plan = self.plan("zoom-zoo")
        path = self.report_file("zoom-zoo", matched=True)
        row = c.classify("zoom-zoo", 0, path, plan)
        witness = row["evidence"]["source_original_movie_vs_fresh_guest_result_phase"]
        self.assertTrue(witness["three_relative_durations_equal"])
        self.assertFalse(witness["continuous_original_to_fresh_equivalence_proven"])
        self.assertEqual(row["release_credit"], 0)

    def test_cross_shard_source_sram_is_part_of_execution_identity(self):
        plan = self.plan()
        out = self.root / "source-sram-mismatch"
        for case in c.CASES:
            target = out / f"qa01-campaign-case-{case}" / "case-result.json"
            c.write_json(target, c.classify(case, 1, self.report_file(case), plan))
        self.assertTrue(c.aggregate(plan, out)[0]["transport_complete"])
        target = out / "qa01-campaign-case-switcher" / "case-result.json"
        row = c.load_json(target)
        row["evidence"]["source_sram_sha256"] = "f" * 64
        c.write_json(target, row)
        summary, _ = c.aggregate(plan, out)
        self.assertFalse(summary["transport_complete"])
        self.assertEqual(summary["counts"]["missing_evidence"], 1)
        self.assertIn("identity mismatch", summary["results"][-1]["reason"])
        self.assertEqual(summary["release_admissions"], 0)

    def test_aggregate_accounting_detects_missing_and_bad_foreign_artifacts(self):
        plan = self.plan("all")
        out = self.root / "results"
        for case in ("bowl", "zoom-zoo"):
            target = out / ("qa01-campaign-case-" + case) / "case-result.json"
            c.write_json(target, c.classify(
                case, 1, self.report_file(case), plan))
        aggregate, markdown = c.aggregate(plan, out)
        self.assertEqual(aggregate["completed"], 2)
        self.assertEqual(aggregate["counts"]["missing_evidence"], 1)
        self.assertFalse(aggregate["transport_complete"])
        self.assertEqual(aggregate["release_admissions"], 0)
        self.assertIn("switcher", markdown)
        target = out / "qa01-campaign-case-switcher" / "case-result.json"
        c.write_json(target, c.classify(
            "switcher", 1, self.report_file("switcher"), plan))
        aggregate, _ = c.aggregate(plan, out)
        self.assertTrue(aggregate["transport_complete"])
        self.assertEqual(aggregate["counts"]["strict_divergence"], 3)
        spoofed = json.loads(target.read_text())
        spoofed["plan_sha256"] = "0" * 64
        c.write_json(target, spoofed)
        self.assertFalse(c.aggregate(plan, out)[0]["transport_complete"])
        c.write_json(target, c.classify(
            "switcher", 1, self.report_file("switcher"), plan))
        c.write_json(out/"qa01-campaign-case-injected"/"case-result.json",
                     {"case": "injected"})
        self.assertFalse(c.aggregate(plan, out)[0]["transport_complete"])

    def test_cross_shard_emulator_identity_must_match(self):
        plan = self.plan("all")
        out = self.root / "results"
        for case in ("zoom-zoo", "bowl", "switcher"):
            target = out / ("qa01-campaign-case-" + case) / "case-result.json"
            c.write_json(target, c.classify(
                case, 1, self.report_file(case), plan))
        self.assertTrue(c.aggregate(plan, out)[0]["transport_complete"])
        target = out/"qa01-campaign-case-switcher"/"case-result.json"
        record = json.loads(target.read_text())
        record["evidence"]["native_sha256"] = "f" * 64
        c.write_json(target, record)
        summary, _ = c.aggregate(plan, out)
        self.assertFalse(summary["transport_complete"])
        self.assertEqual(summary["counts"]["missing_evidence"], 1)
        self.assertIn("identity mismatch", summary["results"][-1]["reason"])
        record["evidence"]["native_sha256"] = "a" * 64
        record["evidence"]["strict_candidate"] = True
        c.write_json(target, record)
        self.assertFalse(c.aggregate(plan, out)[0]["transport_complete"])

    def test_producer_failure_has_real_error_and_fails_case_job(self):
        plan = self.plan("bowl")
        log = self.root / "producer.log"
        log.write_text(
            "source prior output\n"
            "/tmp/native: error while loading shared libraries: "
            "libOpenGL.so.0: cannot open shared object file\n")
        result = c.classify("bowl", 1, self.root / "absent.json", plan, log)
        self.assertEqual(result["disposition"], "producer_error")
        self.assertEqual(result["release_credit"], 0)
        self.assertIn("libOpenGL.so.0", result["reason"])
        self.assertLess(len(result["reason"]), 420)
        log.write_text("Traceback (most recent call last):\n"
                       "__main__.CompleteEventError: "
                       "source movie never demonstrated this course/result pair\n")
        result = c.classify("bowl", 1, self.root/"absent.json", plan, log)
        self.assertIn("source movie never demonstrated", result["reason"])
        plan_path = self.root / "plan.json"
        output = self.root / "case-result.json"
        c.write_json(plan_path, plan)
        args = [sys.executable, str(ROOT / "tools/qa01_event_campaign.py"),
                "classify", "--plan", str(plan_path),
                "--case", "bowl", "--producer-exit", "1",
                "--producer-report", str(self.root / "absent.json"),
                "--producer-log", str(log), "--out", str(output)]
        proc = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("source movie never demonstrated",
                      json.loads(output.read_text())["reason"])
        # Scientific negative is a valid experiment and must remain a
        # green transport even though it cannot pass QA-01.
        producer_path = self.report_file("bowl")
        args[args.index(str(self.root / "absent.json"))] = str(producer_path)
        proc = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(output.read_text())["disposition"],
                         "strict_divergence")

    def test_cli_aggregate_exit_status_and_plan_roundtrip(self):
        plan = self.plan("bowl")
        plan_path = self.root / "plan.json"
        result_path = self.root / "aggregate.json"
        summary_path = self.root / "summary.md"
        c.write_json(plan_path, plan)
        args = [sys.executable, str(ROOT/"tools/qa01_event_campaign.py"),
                "aggregate", "--plan", str(plan_path),
                "--results-dir", str(self.root/"evidence"),
                "--out", str(result_path), "--summary", str(summary_path)]
        fail = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(fail.returncode, 1, fail.stderr)
        self.assertEqual(json.loads(result_path.read_text())["release_admissions"], 0)
        case_path = self.root/"evidence"/"qa01-campaign-case-bowl"/"case-result.json"
        c.write_json(case_path, c.classify(
            "bowl", 1, self.report_file("bowl"), plan))
        passed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn("strict_divergence", summary_path.read_text())

    def test_opt_in_switcher_nmi_reuses_source_event_classification_for_both_exits(self):
        workflow=(ROOT/".github/workflows/qa01-switcher-original-2014.yml").read_text()
        scope=workflow.split("      - name: Existing fresh-paired Switcher",1)[1]
        scope=scope.split("      - name: Preserve original/native logs",1)[0]
        self.assertIn('qa.classify("switcher",int(rc),Path(report),',scope)
        self.assertIn('("strict_candidate","strict_divergence")',scope)
        self.assertNotIn('test "$rc" -eq 1',scope)
        self.assertIn("paired-classification.json",workflow)
        self.assertIn("qa01_switcher_nmi_beam_crosswalk.py",scope)
        p=self.plan("switcher")
        file=self.report_file("switcher",matched=True)
        candidate=c.classify("switcher",0,file,p)
        self.assertEqual(candidate["disposition"],"strict_candidate")
        self.assertEqual(candidate["release_credit"],0)
        contradiction=c.classify("switcher",1,file,p)
        self.assertEqual(contradiction["disposition"],"producer_error")
        file=self.report_file("switcher",matched=False)
        divergence=c.classify("switcher",1,file,p)
        self.assertEqual(divergence["disposition"],"strict_divergence")
        self.assertEqual(divergence["release_credit"],0)
        invalid=c.classify("switcher",2,file,p)
        self.assertEqual(invalid["disposition"],"producer_error")

    def test_source_result_can_match_while_unmasked_strict_state_diverges(self):
        # This is a synthetic classification fixture, never a cold-guest
        # execution or proof that the real Zoo event is equivalent.
        report = producer("zoom-zoo", matched=True)
        report["comparison"]["first_sample_disagreement"] = {
            "relative_frame": 5040, "address": "7E:0063"}
        report["comparison"]["paired_event_candidate"] = False
        path = self.root / "zoo-unmasked-divergence.json"
        c.write_json(path, report)
        row = c.classify("zoom-zoo", 1, path, self.plan("zoom-zoo"))
        self.assertEqual(row["disposition"], "strict_divergence")
        self.assertTrue(row["evidence"]["terminal_frame_matched"])
        self.assertEqual(row["release_credit"], 0)
        self.assertEqual(row["evidence"]["first_sample_disagreement"]["relative_frame"], 5040)

    def test_cold_guest_opt_in_allows_classified_divergence_without_qa_credit(self):
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        start = workflow.index('if [[ "$QA01_COLD_GUEST" == "true" && "$QA01_CASE"')
        end = workflow.index("python3 tools/qa01_cold_result_record.py", start)
        gate = workflow[start:end]
        self.assertIn('"$QA01_SOURCE_FOLLOWTHROUGH" == "true"', gate)
        self.assertIn('"$case_rc" -eq 0', gate)
        self.assertIn('"$producer_rc" -eq 0 || "$producer_rc" -eq 1', gate)
        self.assertIn('("strict_candidate", "strict_divergence")', gate)
        self.assertIn('row.get("release_credit") != 0', gate)
        self.assertIn('raise SystemExit("cold guest requires valid source-classified Zoo evidence")', gate)
        self.assertNotIn('"$producer_rc" -eq 0 && "$case_rc" -eq 0', gate)
        self.assertIn("host disk durability NOT proven; zero event credit", workflow)

    def test_workflow_stays_manual_small_and_one_build(self):
        workflow = (ROOT/".github/workflows/qa01-event-campaign.yml").read_text()
        header = workflow.split("\njobs:", 1)[0]
        self.assertIn("workflow_dispatch:", header)
        self.assertNotIn("\n  push:", header)
        self.assertNotIn("\n  pull_request:", header)
        self.assertNotIn("\n  schedule:", header)
        self.assertIn("cancel-in-progress: false", header)
        self.assertIn("fail-fast: false", workflow)
        self.assertIn("max-parallel: 2", workflow)
        self.assertIn("timeout-minutes: 90", workflow)
        self.assertEqual(workflow.count("cmake --build baldosa/build"), 1)
        self.assertEqual(workflow.count("bootstrap_toolchain.py --offline --tool snes9x-libretro"), 1)
        self.assertIn("tools/probe_original_event_complete.py", workflow)
        self.assertIn("tools/qa01_event_campaign.py aggregate", workflow)
        self.assertIn("libopengl0", workflow)
        self.assertIn("zoo_terminal_phase:", workflow)
        self.assertEqual(workflow.count("      source_followthrough:"), 2)
        self.assertIn("QA01_SOURCE_FOLLOWTHROUGH: ${{ inputs.source_followthrough }}", workflow)
        self.assertIn('extra_args+=(--source-followthrough)', workflow)
        self.assertIn('if [[ "$QA01_SOURCE_FOLLOWTHROUGH" == "true" ]]', workflow)
        self.assertIn("original/native +8/+16/+24/+32 result follow-through", workflow)
        self.assertIn('selected=zoom-zoo', workflow)
        self.assertIn('extra_args+=(--zoo-terminal-phase)', workflow)
        self.assertIn('"${extra_args[@]}"', workflow)
        self.assertIn("zoo-terminal-phase/reference.log", workflow)
        self.assertIn("ldd \"$RUNNER_TEMP/qa01-binaries/native\"", workflow)
        self.assertIn("--producer-log \"$ROOT/producer.log\"", workflow)
        self.assertIn('exit "$case_rc"', workflow)
        self.assertNotIn("contents: write", workflow)


    def test_rf015_refresh_correction_is_opt_in_before_the_one_build(self):
        workflow = (ROOT/".github/workflows/qa01-event-campaign.yml").read_text()
        header = workflow.split("\njobs:", 1)[0]
        self.assertEqual(header.count("      baldosa_refresh_beam_rate:"), 2)
        for block in header.split("      baldosa_refresh_beam_rate:")[1:]:
            own = block.split("\n")[1:5]
            self.assertIn("        default: false", own)
            self.assertIn("        type: boolean", own)
        stage = 'python3 tools/baldosa_dram_refresh_beam_rate_patch.py --game baldosa'
        self.assertEqual(workflow.count(stage), 1)
        guard = 'if [[ "${{ inputs.baldosa_refresh_beam_rate }}" == "true" ]]; then'
        self.assertLess(workflow.index(guard), workflow.index(stage))
        self.assertLess(workflow.index(stage), workflow.index("cmake -S baldosa -B baldosa/build"))
        self.assertEqual(workflow.count("cmake --build baldosa/build"), 1)

    def test_spc_interrupt_stage_is_opt_in_ordered_and_gated_on_rf015_019(self):
        workflow = (ROOT/".github/workflows/qa01-event-campaign.yml").read_text()
        header = workflow.split("\njobs:", 1)[0]
        self.assertEqual(header.count("      baldosa_spc_interrupt_stage:"), 2)
        for block in header.split("      baldosa_spc_interrupt_stage:")[1:]:
            own = block.split("\n")[1:5]
            self.assertIn("        default: false", own)
            self.assertIn("        type: boolean", own)
        dispatch = header.split("  workflow_dispatch:", 1)[1]
        self.assertLessEqual(dispatch.count("        type: "), 25)  # GitHub dispatch-input limit
        stages = ["tools/baldosa_hdma_cpu_stall_patch.py --game baldosa",
                  "tools/baldosa_spc_power_on_patch.py --game baldosa --anchor 0",
                  "tools/baldosa_spc_frame_clock_patch.py --game baldosa",
                  "tools/baldosa_spc_bus_cycle_patch.py --game baldosa",
                  "tools/baldosa_interrupt_entry_cost_patch.py --game baldosa",
                  "cmake -S baldosa -B baldosa/build"]
        at = [workflow.index(x) for x in stages]
        self.assertEqual(at, sorted(at))
        for x in stages[1:5]:
            self.assertEqual(workflow.count(x), 1)
        guard = 'if [[ "${{ inputs.baldosa_spc_interrupt_stage }}" == "true" ]]; then'
        self.assertLess(workflow.index(guard), at[1])
        plan = workflow.split("\n  build:", 1)[0]
        self.assertIn('"$QA01_SPC_INTERRUPT_STAGE" == "true" && "$QA01_RF015_019" != "true"', plan)
        for name in ("baldosa_refresh_beam_rate", "baldosa_io_clock_order", "baldosa_spc_reference_rate",
                     "baldosa_dp_pointer_once", "baldosa_hdma_cpu_stall"):
            self.assertIn(f"inputs.{name}", plan)

if __name__ == "__main__":
    unittest.main()

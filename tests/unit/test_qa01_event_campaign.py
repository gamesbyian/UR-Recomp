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
            "diagnostic_exit_success_without_full_event_parity": False,
        },
        **{key: "a" * 64 for key in (
            "rom_sha256", "original_movie_sha256",
            "native_executable_sha256", "reference_core_sha256",
            "input_sha256", "source_sram_sha256",
            "original_movie_window_sha256", "reference_script_sha256")},
    }


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
        self.assertIn('selected=zoom-zoo', workflow)
        self.assertIn('extra_args+=(--zoo-terminal-phase)', workflow)
        self.assertIn('"${extra_args[@]}"', workflow)
        self.assertIn("zoo-terminal-phase/reference.log", workflow)
        self.assertIn("ldd \"$RUNNER_TEMP/qa01-binaries/native\"", workflow)
        self.assertIn("--producer-log \"$ROOT/producer.log\"", workflow)
        self.assertIn('exit "$case_rc"', workflow)
        self.assertNotIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()

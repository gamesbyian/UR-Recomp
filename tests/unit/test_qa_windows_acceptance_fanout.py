"""ROM-free, fail-closed contract tests for exact Windows fan-out."""
import hashlib
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_windows_acceptance_fanout as fanout
import run_baldosa_parallel_windows_journeys as bridge

SHA = "a" * 40
WHO = {"source_sha": SHA, "exe_sha256": "b" * 64,
       "fixture_sha256": "c" * 64, "zip_sha256": "d" * 64}


def packet(group, who=None):
    indices = fanout.GROUPS[group]
    original_hashes = fanout.original_script_hashes()
    rows = [{"index": i, "name": bridge.STEPS[i],
             "script_sha256": original_hashes[i], "exit_code": 0,
             "elapsed_seconds": 1.5, "log": "step-%02d.log" % i,
             "summary": "step-%02d.md" % i,
             "log_sha256": "b" * 64, "log_bytes": 82,
             "summary_sha256": "c" * 64, "summary_bytes": 16}
            for i in indices]
    result = {"schema": fanout.SCHEMA, "group": group,
              "candidate_identity": dict(who or WHO),
              "expected_indices": list(indices), "cases": rows,
              "all_passed": True, "release_gate_credit": 0,
              "independent_physical_qa": False,
              "elapsed_seconds": 12.0}
    result["receipt_sha256"] = fanout.digest(result)
    return result


class WindowsAcceptanceFanoutTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        for group in fanout.GROUPS:
            dest = self.path / ("windows-fanout-" + group)
            dest.mkdir()
            (dest / "result.json").write_text(json.dumps(packet(group)))

    def update(self, group, receipt):
        (self.path / ("windows-fanout-" + group) / "result.json").write_text(
            json.dumps(receipt))

    def test_exact_full_inventory(self):
        r = fanout.aggregate(self.path, SHA)
        self.assertTrue(r["transport_complete"])
        self.assertEqual(r["observed_cases"], 13)
        self.assertEqual([row["index"] for row in r["cases"]], list(range(13)))
        self.assertEqual(r["release_gate_credit"], 0)
        self.assertEqual(r["schema"], fanout.AGGREGATE_SCHEMA)
        self.assertEqual(r["cases"][0]["script_sha256"],
                         fanout.original_script_hashes()[0])

    def test_missing_group_is_rejected(self):
        (self.path / "windows-fanout-independent" / "result.json").unlink()
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_changed_executable_is_rejected(self):
        self.update("independent", packet("independent",
                    {**WHO, "exe_sha256": "e" * 64}))
        r = fanout.aggregate(self.path, SHA)
        self.assertFalse(r["transport_complete"])
        self.assertIn("different source", " ".join(r["issues"]))

    def test_modified_receipt_is_rejected(self):
        bad = packet("independent")
        bad["cases"][0]["elapsed_seconds"] = 9
        self.update("independent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_missing_case_is_rejected_even_with_matching_digest(self):
        bad = packet("independent")
        bad["cases"].pop()
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_failed_case_is_actionable_without_private_log_contents(self):
        bad = packet("independent")
        bad["cases"][4]["exit_code"] = 9
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertEqual(result["failed_cases"], [{
            "group": "independent", "index": 7, "name": bridge.STEPS[7],
            "reason": "nonzero_exit", "exit_code": 9}])
        self.assertNotIn("genuine-script-output", json.dumps(result))
        self.assertEqual(result["release_gate_credit"], 0)

    def test_failure_receipt_with_missing_case_never_claims_full_inventory(self):
        bad = packet("seed-dependent")
        bad["cases"] = bad["cases"][:1]
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertTrue(any("missing" in issue or "case" in issue
                            for issue in result["issues"]))

    def test_summarizer_never_invents_missing_case_success(self):
        rows = packet("seed-dependent")["cases"][:1]
        problems = fanout.summarize_case_failures("seed-dependent", rows)
        self.assertEqual([(r["index"], r["reason"], r["exit_code"])
                          for r in problems],
                         [(1, "missing_case", None), (2, "missing_case", None)])

    def test_real_original_script_failure_is_rejected(self):
        bad = packet("seed-dependent")
        bad["cases"][0]["exit_code"] = 1
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_false_release_gate_promotion_is_rejected(self):
        bad = packet("seed-dependent")
        bad["release_gate_credit"] = 1
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_no_duplicate_or_replaced_source_scenarios(self):
        source = bridge.WORKFLOW.read_text(encoding="utf-8")
        commands = bridge.extract_commands(source)
        self.assertEqual(len(commands), 13)
        self.assertEqual(set(fanout.GROUPS["seed-dependent"]), {0, 1, 2})
        self.assertEqual(set(fanout.GROUPS["independent"]), set(range(3, 13)))
        self.assertEqual([i for i in bridge.INDEPENDENT_PRIORITY if
                          i in fanout.GROUPS["independent"]].__len__(), 10)
        self.assertTrue(all("baseline/" not in commands[i] for i in range(3, 13)))

    def test_recomputed_receipt_digest_does_not_mask_changed_script(self):
        bad = packet("independent")
        bad["cases"][0]["script_sha256"] = "0" * 64
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertIn("script identity changed", " ".join(result["issues"]))

    def test_missing_script_hash_fails_even_with_valid_receipt_digest(self):
        bad = packet("seed-dependent")
        del bad["cases"][0]["script_sha256"]
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_same_names_changed_original_shell_body_is_not_equivalent(self):
        current = bridge.WORKFLOW.read_text(encoding="utf-8")
        changed = current.replace("--expected-frames 2473",
                                  "--expected-frames 2474", 1)
        self.assertNotEqual(current, changed)
        alternate = self.path / "changed-original-workflow.yml"
        alternate.write_text(changed, encoding="utf-8")
        with mock.patch.object(bridge, "WORKFLOW", alternate):
            result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertIn("script identity changed", " ".join(result["issues"]))

    def test_historical_v2_group_receipts_not_silently_promoted(self):
        old = packet("seed-dependent")
        old["schema"] = "ur-win32-acceptance-fanout/2"
        for row in old["cases"]:
            del row["script_sha256"]
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_authenticate_three_independent_source_hashes(self):
        names = ("exe", "fixture", "zip")
        for name in names:
            (self.path / name).write_bytes(name.encode())
        got = fanout.candidate_identity(SHA, *(self.path / x for x in names))
        self.assertEqual(got["exe_sha256"], hashlib.sha256(b"exe").hexdigest())

    def test_missing_original_group_output_cannot_pass(self):
        # The seed-dependent group can stop after a failed seed producer.
        old = packet("seed-dependent")
        old["cases"] = old["cases"][:1]
        old["all_passed"] = True
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_exact_original_script_groups_execute_without_rebuilding(self):
        # Synthetic subprocess seam, not a substitute Windows/game witness.
        env = {"GITHUB_SHA": SHA, "RUNNER_TEMP": str(self.path),
               "GITHUB_STEP_SUMMARY": str(self.path / "summary.md")}
        exe = self.path / "candidate.exe"
        fixture = self.path / "fixture.exe"
        archive = self.path / "candidate.zip"
        for path in (exe, fixture, archive):
            path.write_bytes(path.name.encode())

        def fake_runner(i, script, work, environ):
            (work / ("step-%02d.log" % i)).write_text("genuine-script-output")
            (work / ("step-%02d.md" % i)).write_text("original-step-summary")
            if i == 0:
                save = (self.path / "UR Baldosa Win32 Pause Route" /
                        "baseline" / "Modern Player Data With Spaces" /
                        "saves" / "save.srm")
                save.parent.mkdir(parents=True, exist_ok=True)
                save.write_bytes(bytes(8192))
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}

        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=fake_runner):
            seed = fanout.run_group("seed-dependent", SHA, archive,
                                    self.path / "seed-work", env)
            self.assertEqual([r["index"] for r in seed["cases"]], [0, 1, 2])
            self.assertTrue(seed["all_passed"])
            # Two independent Windows jobs have separate ephemeral temp roots.
            fresh = self.path / "other-runner"
            fresh.mkdir()
            new_env = {**env, "RUNNER_TEMP": str(fresh)}
            independent = fanout.run_group(
                "independent", SHA, archive, fresh / "work", new_env)
            self.assertEqual([r["index"] for r in independent["cases"]],
                             list(range(3, 13)))
            self.assertTrue(independent["all_passed"])

    def _seed_followup_fake_inputs(self):
        env = {"GITHUB_SHA": SHA, "RUNNER_TEMP": str(self.path),
               "GITHUB_STEP_SUMMARY": str(self.path / "summary.md")}
        paths = [self.path / "candidate.exe", self.path / "fixture.exe",
                 self.path / "candidate.zip"]
        for path in paths:
            path.write_bytes(path.name.encode())
        return env, paths

    def test_opt_in_seed_followups_start_only_after_real_seed_and_overlap(self):
        # A barrier is an execution-order witness. The original shell cases
        # are replaced by synthetic Python runners, never real Windows games.
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        barrier = threading.Barrier(2, timeout=5)
        lock = threading.Lock()
        events = []
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(range(256)) * 32)
            else:
                self.assertTrue(seed.is_file())
                self.assertEqual(seed.read_bytes(), bytes(range(256)) * 32)
                barrier.wait()
            with lock:
                events.append(i)
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            result = fanout.run_group("seed-dependent", SHA, archive,
                                      self.path / "two-seed-workers", env,
                                      seed_followup_workers=2)
        self.assertEqual(result["schema"], fanout.SCHEMA)
        self.assertTrue(result["all_passed"])
        self.assertEqual([r["index"] for r in result["cases"]], [0, 1, 2])
        self.assertEqual(events[0], 0)
        self.assertEqual(set(events[1:]), {1, 2})
        self.assertEqual(seed.read_bytes(), bytes(range(256)) * 32)
        self.assertEqual(result["release_gate_credit"], 0)

    def test_seed_followup_parallel_refuses_changed_original_seed_argument(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        source = bridge.WORKFLOW.read_text(encoding="utf-8")
        scripts = bridge.extract_commands(source)
        needle = 'baseline/Modern Player Data With Spaces/saves/save.srm'
        self.assertIn(needle, scripts[1])
        bad = list(scripts)
        bad[1] = bad[1].replace(needle, "other/save.srm")
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "extract_commands", return_value=bad), \
             mock.patch.object(bridge, "run_one") as runner:
            with self.assertRaisesRegex(ValueError, "source path changed"):
                fanout.run_group("seed-dependent", SHA, archive,
                                 self.path / "source-drift", env,
                                 seed_followup_workers=2)
            runner.assert_not_called()
        self.assertFalse((self.path / "source-drift").exists())

    def test_seed_followup_parallel_fails_closed_if_original_seed_is_mutated(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        barrier = threading.Barrier(2, timeout=5)
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(8192))
            else:
                barrier.wait()
                if i == 1:
                    seed.write_bytes(b"X" + bytes(8191))
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            with self.assertRaisesRegex(ValueError, "baseline SRAM changed"):
                fanout.run_group("seed-dependent", SHA, archive,
                                 self.path / "seed-mutated", env,
                                 seed_followup_workers=2)
        self.assertFalse((self.path / "seed-mutated" / "result.json").exists())

    def test_seed_followup_parallel_never_runs_without_authentic_seed(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seen = []
        def runner(i, script, work, environ):
            seen.append(i)
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            result = fanout.run_group("seed-dependent", SHA, archive,
                                      self.path / "no-real-seed", env,
                                      seed_followup_workers=2)
        self.assertEqual(seen, [0])
        self.assertFalse(result["all_passed"])
        self.assertEqual([r["index"] for r in result["cases"]], [0])

    def test_invalid_seed_followup_mode_rejected_before_file_io(self):
        env = {"GITHUB_SHA": SHA}
        for setting in (0, 3, -1, True, None, "2"):
            with self.subTest(setting=setting), self.assertRaisesRegex(ValueError, "follow-up workers"):
                fanout.run_group("seed-dependent", SHA,
                                 self.path / "missing-archive",
                                 self.path / "bad-mode", env,
                                 seed_followup_workers=setting)
        with self.assertRaisesRegex(ValueError, "only to the seed-dependent"):
            fanout.run_group("independent", SHA, self.path / "missing-archive",
                             self.path / "bad-mode", env,
                             seed_followup_workers=2)
        self.assertFalse((self.path / "bad-mode").exists())

    def test_pre_digest_v1_receipt_cannot_be_misread_as_current(self):
        old = packet("seed-dependent")
        old["schema"] = "ur-win32-acceptance-fanout/1"
        for row in old["cases"]:
            for key in ("log_sha256", "log_bytes", "summary_sha256", "summary_bytes"):
                row.pop(key)
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_tampered_private_output_digest_is_rejected(self):
        value = packet("seed-dependent")
        value["cases"][0]["log_sha256"] = "not-a-real-sha"
        value["receipt_sha256"] = fanout.digest(
            {k: v for k, v in value.items() if k != "receipt_sha256"})
        self.update("seed-dependent", value)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_private_log_digest_is_actual_file_content(self):
        work = self.path / "proof"
        work.mkdir()
        rows = [{"index": 8, "log": "step-08.log",
                 "summary": "step-08.md"}]
        contents = b"test-only-genuine-source-log\n"
        (work / rows[0]["log"]).write_bytes(contents)
        (work / rows[0]["summary"]).write_bytes(b"summary")
        fanout.attest_private_case_files(rows, work)
        self.assertEqual(rows[0]["log_sha256"],
                         hashlib.sha256(contents).hexdigest())
        self.assertEqual(rows[0]["summary_bytes"], len(b"summary"))
        self.assertEqual(rows[0]["log_bytes"], len(contents))

    def test_missing_private_original_log_is_not_success(self):
        work = self.path / "missing-proof"
        work.mkdir()
        with self.assertRaisesRegex(ValueError, "missing original Windows log"):
            fanout.attest_private_case_files(
                [{"index": 0, "log": "step-00.log",
                  "summary": "step-00.md"}], work)

    def test_optional_original_summary_records_explicit_absence(self):
        work = self.path / "optional-summary"
        work.mkdir()
        (work / "step-03.log").write_bytes(b"original log")
        rows = [{"index": 3, "log": "step-03.log",
                 "summary": "step-03.md"}]
        fanout.attest_private_case_files(rows, work)
        self.assertIsNone(rows[0]["summary_sha256"])
        self.assertEqual(rows[0]["summary_bytes"], 0)

    def test_redirected_private_original_log_is_rejected(self):
        work = self.path / "redirect"
        work.mkdir()
        source = self.path / "outside-log"
        source.write_bytes(b"source")
        try:
            (work / "step-00.log").symlink_to(source)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "redirected original Windows"):
            fanout.attest_private_case_files(
                [{"index": 0, "log": "step-00.log",
                  "summary": "step-00.md"}], work)

    def test_aggregate_cli_publishes_fail_closed_machine_receipt(self):
        import subprocess
        outfile = self.path / "aggregate.json"
        p = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "qa_windows_acceptance_fanout.py"),
             "aggregate", "--source-sha", SHA, "--results", str(self.path),
             "--out", str(outfile)],
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(json.loads(outfile.read_text())["transport_complete"])


if __name__ == "__main__":
    unittest.main()

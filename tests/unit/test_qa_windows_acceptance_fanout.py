"""ROM-free, fail-closed contract tests for exact Windows fan-out."""
import hashlib
import json
import sys
import tempfile
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
    rows = [{"index": i, "name": bridge.STEPS[i], "exit_code": 0,
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

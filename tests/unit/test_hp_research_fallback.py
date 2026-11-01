"""Synthetic deterministic HP fallback scheduling tests; never touch GitHub."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import shutil
import subprocess
import os
import io
from contextlib import redirect_stdout
import unittest
from unittest.mock import patch
from tools.ci import hp_research_fallback as h

NOW = datetime(2026, 11, 1, 5, 0, tzinfo=timezone.utc)
SHA = "a" * 40
NAME = {
    h.RESEARCH: "HP unattended seeded 2P gameplay research",
    h.PRIORITY[0]: "HP current-source native Windows smoke",
    h.PRIORITY[1]: "Owner HP Windows runner benchmark (isolated)",
}


def row(name=h.RESEARCH, *, minutes=120, sha=SHA, status="completed", conclusion="success", event="schedule"):
    return {"id": 1001, "name": NAME[name], "path": ".github/workflows/"+name,
            "head_branch": "main", "head_sha": sha, "status": status,
            "conclusion": conclusion, "created_at": (NOW-timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event}


def mock_api(research=None, priority=None):
    research = [] if research is None else research
    priority = {} if priority is None else priority
    calls = []
    def request(args):
        calls.append(args)
        route = args[-1]
        if "/git/ref/heads/main" in route:
            return {"ref": "refs/heads/main", "object": {"sha": SHA}}
        if route.endswith("/dispatches"):
            return None
        for name in (h.RESEARCH, *h.PRIORITY):
            if f"/{name}/runs?" in route:
                return {"workflow_runs": research if name == h.RESEARCH else priority.get(name, [])}
        raise AssertionError(route)
    return request, calls


class HPFallbackTests(unittest.TestCase):
    def test_stale_success_dispatches_exact_main(self):
        req, calls = mock_api(research=[row()])
        result = h.execute(NOW, req, dry_run=False)
        self.assertTrue(result["dispatched"])
        self.assertEqual(calls[-1], ["--method", "POST", "-f", "ref=main",
            f"repos/{h.REPO}/actions/workflows/{h.RESEARCH}/dispatches"])

    def test_main_ref_rechecked_immediately_before_post(self):
        req, calls = mock_api(research=[row()])
        result = h.execute(NOW, req, dry_run=False)
        self.assertTrue(result["dispatched"])
        self.assertEqual(sum("/git/ref/heads/main" in a[-1] for a in calls), 2)
        self.assertEqual(result["main_sha"], SHA)

    def test_main_ref_advance_during_census_aborts_without_post(self):
        req, calls = mock_api(research=[row()])
        reads = [0]
        def race(args):
            if "/git/ref/heads/main" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return {"ref": "refs/heads/main", "object": {"sha": "b" * 40}}
            return req(args)
        result = h.execute(NOW, race, dry_run=False)
        self.assertEqual(result["decision"], "skip:main-ref-changed")
        self.assertEqual(result["main_sha"], SHA)
        self.assertFalse(result["dispatched"])
        self.assertEqual(reads[0], 2)
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_malformed_main_ref_fails_closed_on_both_reads(self):
        for payload in (None, {}, [], {"ref": "refs/heads/main"},
                        {"ref": "refs/heads/main", "object": {"sha": "Z" * 40}}):
            with self.subTest(payload=payload):
                self.assertRaises(ValueError, h.main_sha, lambda _: payload)
        req, calls = mock_api(research=[row()])
        reads = [0]
        def malformed_second(args):
            if "/git/ref/heads/main" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return None
            return req(args)
        with self.assertRaises(ValueError):
            h.execute(NOW, malformed_second, dry_run=False)
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_recent_manual_blocks(self):
        req, calls = mock_api(research=[row(minutes=30, event="workflow_dispatch")])
        self.assertEqual(h.execute(NOW, req, dry_run=False)["decision"], "skip:recent-research")
        self.assertEqual(len(calls), 4)

    def test_pending_schedule_blocks_even_if_stale(self):
        req, _ = mock_api(research=[row(minutes=300, status="queued", conclusion=None)])
        self.assertEqual(h.execute(NOW, req, dry_run=False)["decision"], "skip:research-already-active")

    def test_main_build_blocks(self):
        req, _ = mock_api(research=[row()], priority={h.PRIORITY[0]: [row(h.PRIORITY[0], status="in_progress")]})
        self.assertEqual(h.execute(NOW, req, dry_run=False)["decision"], "skip:priority-windows-build-active")

    def test_failed_current_source_stops_retry(self):
        req, _ = mock_api(research=[row(conclusion="failure")])
        self.assertEqual(h.execute(NOW, req, dry_run=False)["decision"], "skip:latest-source-research-not-successful")

    def test_failed_older_source_can_retry_new_main(self):
        req, _ = mock_api(research=[row(sha="b"*40, conclusion="failure")])
        self.assertTrue(h.execute(NOW, req, dry_run=False)["dispatched"])

    def test_dry_run_never_mutates(self):
        req, calls = mock_api(research=[row()])
        self.assertFalse(h.execute(NOW, req, dry_run=True)["dispatched"])
        self.assertEqual(len(calls), 4)

    def test_schedule_arrives_during_second_read(self):
        req, calls = mock_api(research=[row()])
        reads = [0]
        def race(args):
            if f"/{h.RESEARCH}/runs?" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return {"workflow_runs": [row(minutes=1, status="queued"), row()]}
            return req(args)
        result = h.execute(NOW, race, dry_run=False)
        self.assertEqual(result["decision"], "skip:research-census-changed")
        self.assertFalse(result["dispatched"])
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_status_published_as_bounded_local_json(self):
        with tempfile.TemporaryDirectory() as temp:
            h.publish_status(Path(temp), {"dispatched": False, "decision": "skip"})
            self.assertIn('"decision": "skip"', (Path(temp)/"last-status.json").read_text())
            h.publish_status(Path(temp), {"dispatched": True})
            self.assertNotIn('"decision"', (Path(temp)/"last-status.json").read_text())

    def test_priority_job_arrives_during_second_read(self):
        req, calls = mock_api(research=[row()])
        reads = [0]
        def race(args):
            if f"/{h.PRIORITY[0]}/runs?" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return {"workflow_runs": [row(h.PRIORITY[0], minutes=1,
                                                   status="in_progress", conclusion=None)]}
            return req(args)
        result = h.execute(NOW, race, dry_run=False)
        self.assertEqual(result["decision"], "skip:priority-census-changed")
        self.assertFalse(result["dispatched"])
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_losing_main_lock_never_overwrites_winner_status(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp)
            h.publish_status(state_dir, {"dispatched": True, "main_sha": SHA})
            before = (state_dir / "last-status.json").read_bytes()
            stdout = io.StringIO()
            with h.single_instance(state_dir):
                with patch.object(h, "execute", side_effect=AssertionError("must not request")):
                    with redirect_stdout(stdout):
                        exit_code = h.main(["--once", "--state-dir", str(state_dir)])
                self.assertEqual(exit_code, 2)
                self.assertEqual((state_dir / "last-status.json").read_bytes(), before)
            self.assertEqual((state_dir / "last-status.json").read_bytes(), before)
            self.assertIn('"category": "RuntimeError"', stdout.getvalue())

    def test_locked_failure_publishes_failure_without_leaking_cli_detail(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp)
            stdout = io.StringIO()
            with patch.object(h, "execute", side_effect=RuntimeError("SECRET_SENTINEL")):
                with redirect_stdout(stdout):
                    exit_code = h.main(["--once", "--state-dir", str(state_dir)])
            self.assertEqual(exit_code, 2)
            self.assertIn('"status": "error"', (state_dir / "last-status.json").read_text())
            self.assertNotIn("SECRET_SENTINEL", stdout.getvalue())
            self.assertNotIn("SECRET_SENTINEL", (state_dir / "last-status.json").read_text())

    def test_no_previous_research_can_dispatch(self):
        req, calls = mock_api()
        self.assertTrue(h.execute(NOW, req, dry_run=False)["dispatched"])
        self.assertEqual(len(calls), 9)

    def test_malformed_or_foreign_rows_fail_closed(self):
        for change in ({"head_branch": "feature"}, {"path": "other.yml"},
                       {"created_at": "invalid"}, {"status": "surprise"},
                       {"name": "other"}):
            with self.subTest(change=change):
                self.assertRaises(ValueError, h.classify, [{**row(), **change}], expected_workflow=h.RESEARCH)

    def test_unrecognized_api_fails_closed(self):
        req, calls = mock_api(research=[row()])
        def corrupt(args):
            if "/runs?" in args[-1]:
                return {"workflows": []}
            return req(args)
        with self.assertRaises(ValueError):
            h.execute(NOW, corrupt, dry_run=False)
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_lock_mutual_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            with h.single_instance(path):
                with self.assertRaises(RuntimeError):
                    with h.single_instance(path):
                        pass
            with h.single_instance(path):
                pass

    def test_owner_installer_uses_powershell_interactive_enum(self):
        script = (Path(__file__).parents[2] / "tools" / "ci" / "Install-HP-Research-Fallback.ps1").read_text(encoding="utf-8")
        self.assertIn("-LogonType Interactive", script)
        self.assertNotIn("-LogonType InteractiveToken", script)
        self.assertIn("-MultipleInstances IgnoreNew", script)

    def test_owner_installer_powershell_parser_when_available(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("PowerShell Core not installed; Windows task acceptance remains external")
        script = Path(__file__).parents[2] / "tools" / "ci" / "Install-HP-Research-Fallback.ps1"
        check = ("$tokens = $null; $errors = $null; "
                 "[void][System.Management.Automation.Language.Parser]::ParseFile("
                 "$env:HP_PS1_TEST, [ref]$tokens, [ref]$errors); "
                 "if ($errors.Count -gt 0) { exit 1 }")
        r = subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", check],
                           env={**os.environ, "HP_PS1_TEST": str(script)},
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, "owner installer PowerShell syntax failed")

    def test_iso_time_and_cooldown_boundary(self):
        self.assertEqual(h.parse_utc("2026-11-01T05:00:00Z"), NOW)
        self.assertRaises(ValueError, h.parse_utc, "2026-11-01")
        q = h.classify([row(minutes=90)], expected_workflow=h.RESEARCH)
        self.assertEqual(h.decision(NOW, SHA, q, []), "dispatch:missed-research-window")
        q = h.classify([row(minutes=89)], expected_workflow=h.RESEARCH)
        self.assertEqual(h.decision(NOW, SHA, q, []), "skip:recent-research")


    def test_same_research_id_rerun_changes_status_without_new_id(self):
        req, calls = mock_api(research=[row()])
        reads = [0]
        def rerun(args):
            if f"/{h.RESEARCH}/runs?" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return {"workflow_runs": [{**row(), "status": "in_progress",
                                              "conclusion": None}]}
            return req(args)
        result = h.execute(NOW, rerun, dry_run=False)
        self.assertEqual(result["decision"], "skip:research-census-changed")
        self.assertFalse(result["dispatched"])
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_same_priority_id_rerun_changes_status_without_new_id(self):
        req, calls = mock_api(research=[row()], priority={h.PRIORITY[0]: [row(h.PRIORITY[0])]})
        reads = [0]
        def rerun(args):
            if f"/{h.PRIORITY[0]}/runs?" in args[-1]:
                reads[0] += 1
                if reads[0] == 2:
                    return {"workflow_runs": [{**row(h.PRIORITY[0]), "status": "in_progress",
                                              "conclusion": None}]}
            return req(args)
        result = h.execute(NOW, rerun, dry_run=False)
        self.assertEqual(result["decision"], "skip:priority-census-changed")
        self.assertFalse(result["dispatched"])
        self.assertFalse(any("/dispatches" in a[-1] for a in calls))

    def test_accepted_dispatch_with_unwritable_status_reports_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp)
            h.publish_status(state_dir, {"decision": "previous"})
            before = (state_dir / "last-status.json").read_bytes()
            stdout = io.StringIO()
            accepted = {"dispatched": True, "main_sha": SHA,
                        "decision": "dispatch:missed-research-window"}
            with patch.object(h, "execute", return_value=accepted):
                with patch.object(h, "publish_status", side_effect=PermissionError("SECRET_SENTINEL")) as publish:
                    with redirect_stdout(stdout):
                        exit_code = h.main(["--once", "--state-dir", str(state_dir)])
            self.assertEqual(exit_code, 2)
            self.assertEqual(publish.call_count, 1)
            self.assertEqual((state_dir / "last-status.json").read_bytes(), before)
            report = __import__("json").loads(stdout.getvalue())
            self.assertTrue(report["dispatch_request_accepted"])
            self.assertIn("accepted dispatch", report["detail"])
            self.assertNotIn("no confirmed dispatch", report["detail"])
            self.assertNotIn("SECRET_SENTINEL", stdout.getvalue())

    def test_owner_zip_matches_exact_reviewed_sources(self):
        from zipfile import ZipFile
        root = Path(__file__).parents[2]
        package = root / "tools" / "ci" / "HP-Research-Fallback-Owner-Install.zip"
        names = ["Install-HP-Research-Fallback.cmd", "Install-HP-Research-Fallback.ps1",
                 "hp_research_fallback.py", "Uninstall-HP-Research-Fallback.cmd", "README.md"]
        with ZipFile(package) as archive:
            self.assertEqual(archive.namelist(), names)
            self.assertIsNone(archive.testzip())
            for name in names:
                source = (root / "docs" / "HP-RESEARCH-FALLBACK.md"
                          if name == "README.md" else root / "tools" / "ci" / name)
                self.assertEqual(archive.read(name), source.read_bytes(), name)

if __name__ == "__main__":
    unittest.main()
"""Synthetic deterministic HP fallback scheduling tests; never touch GitHub."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
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

    def test_no_previous_research_can_dispatch(self):
        req, calls = mock_api()
        self.assertTrue(h.execute(NOW, req, dry_run=False)["dispatched"])
        self.assertEqual(len(calls), 6)

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

    def test_iso_time_and_cooldown_boundary(self):
        self.assertEqual(h.parse_utc("2026-11-01T05:00:00Z"), NOW)
        self.assertRaises(ValueError, h.parse_utc, "2026-11-01")
        q = h.classify([row(minutes=90)], expected_workflow=h.RESEARCH)
        self.assertEqual(h.decision(NOW, SHA, q, []), "dispatch:missed-research-window")
        q = h.classify([row(minutes=89)], expected_workflow=h.RESEARCH)
        self.assertEqual(h.decision(NOW, SHA, q, []), "skip:recent-research")


if __name__ == "__main__":
    unittest.main()
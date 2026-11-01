"""Source-bound, read-only owner HP automation cadence watchdog tests."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from tools import hp_compute_watch as watch

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/ops-live-snapshot.yml"
NOW = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def row(*, event="schedule", when=NOW, state="completed", conclusion="success",
        main=True, rid=100, sha="a" * 40):
    return {"id": rid, "event": event, "status": state,
            "conclusion": conclusion, "head_branch": "main" if main else "other",
            "head_sha": sha, "created_at": when.isoformat().replace("+00:00", "Z")}


class HpComputeWatchTests(unittest.TestCase):
    def test_detects_firing_cron_not_manual_trial(self):
        recent = NOW - timedelta(hours=2)
        entries = [row(event="workflow_dispatch", when=NOW - timedelta(minutes=10), rid=101),
                   row(when=recent)]
        result = watch.observe("unattended_2p", entries, NOW)
        self.assertEqual(result["status"], "LAST_RUN_PASSED")
        self.assertEqual(result["last_run_id"], 100)
        self.assertEqual(result["recent_manual_trials"], 1)
        # Without an actual cron event, even a successful manual run cannot
        # prove that the scheduled workflow is delivering any research.
        missing = watch.observe("unattended_2p", entries[:1], NOW)
        self.assertEqual(missing["status"], "SCHEDULE_OVERDUE")
        self.assertEqual(missing["recent_manual_trials"], 1)

    def test_reports_overdue_and_failing_scheduled_runs(self):
        overdue = watch.observe("unattended_2p",
                                [row(when=NOW - timedelta(hours=9))], NOW)
        self.assertEqual(overdue["status"], "SCHEDULE_OVERDUE")
        failed = watch.observe("unattended_2p",
                               [row(when=NOW - timedelta(hours=3), conclusion="failure")], NOW)
        self.assertEqual(failed["status"], "LAST_RUN_NOT_PASSED")
        self.assertEqual(failed["non_success_24h"], 1)

    def test_builds_respond_to_source_not_wall_clock(self):
        old = watch.observe("product_windows",
                            [row(event="push", when=NOW - timedelta(days=3))], NOW)
        self.assertEqual(old["status"], "LAST_RUN_PASSED")
        self.assertEqual(old["last_event"], "push")
        running = watch.observe("product_windows",
                                [row(event="push", when=NOW - timedelta(hours=1),
                                     state="in_progress", conclusion=None)], NOW)
        self.assertEqual(running["status"], "IN_FLIGHT")

    def test_manual_build_does_not_mask_failed_push(self):
        # A later green manual experiment cannot hide an automatic main
        # verification failure, or make missing push evidence appear green.
        runs = [row(event="workflow_dispatch", when=NOW, rid=201),
                row(event="push", when=NOW - timedelta(hours=1),
                    rid=200, conclusion="failure")]
        result = watch.observe("product_windows", runs, NOW)
        self.assertEqual(result["status"], "LAST_RUN_NOT_PASSED")
        self.assertEqual(result["last_run_id"], 200)
        self.assertEqual(result["non_success_24h"], 1)
        self.assertEqual(result["recent_manual_trials"], 1)
        missing = watch.observe("product_windows", runs[:1], NOW)
        self.assertEqual(missing["status"], "NOT_YET_OBSERVED")
        self.assertEqual(missing["recent_manual_trials"], 1)

    def test_never_accepts_wrong_branch_event_future_or_unbound_identity(self):
        x = watch.observe("unattended_2p", [row(main=False)], NOW)
        self.assertEqual(x["status"], "SCHEDULE_OVERDUE")
        with self.assertRaisesRegex(ValueError, "future"):
            watch.observe("unattended_2p",
                          [row(when=NOW + timedelta(minutes=2))], NOW)
        with self.assertRaisesRegex(ValueError, "run ID"):
            watch.observe("unattended_2p", [row(rid="fake")], NOW)
        with self.assertRaises(ValueError):
            watch.observe("unknown", [], NOW)

    def test_missing_schedule_has_bounded_startup_grace(self):
        start = watch.FIRST_ELIGIBLE_2P_UTC
        before = watch.observe("unattended_2p", [], start - timedelta(minutes=1))
        self.assertEqual(before["status"], "NOT_YET_OBSERVED")
        grace = watch.observe("unattended_2p", [], start + timedelta(hours=8))
        self.assertEqual(grace["status"], "NOT_YET_OBSERVED")
        overdue = watch.observe("unattended_2p", [], start + timedelta(hours=8, seconds=1))
        self.assertEqual(overdue["status"], "SCHEDULE_OVERDUE")
        self.assertIsNone(overdue["last_run_id"])
        # Product builds have no wall-clock cadence.
        self.assertEqual(watch.observe("product_windows", [],
                         start + timedelta(days=100))["status"], "NOT_YET_OBSERVED")

    def test_malformed_actions_records_fail_closed(self):
        valid = row()
        changes = [
            None, 42, {}, {"event": "schedule", "id": 100,
                          "created_at": NOW.isoformat()},
            dict(valid, id=True), dict(valid, id="100"),
            dict(valid, head_branch=None), dict(valid, head_branch=" main "),
            dict(valid, head_branch=" "), dict(valid, head_sha=None),
            dict(valid, head_sha="f" * 39), dict(valid, event=None),
            dict(valid, event="invented"),
            dict(valid, status="finished"), dict(valid, status=None),
            dict(valid, status="completed", conclusion=None),
            dict(valid, status="in_progress", conclusion="success"),
            dict(valid, created_at="nope"),
        ]
        for malformed in changes:
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    watch.observe("unattended_2p", [malformed], NOW)
        # Malformed foreign-branch rows are not silently discarded.
        with self.assertRaisesRegex(ValueError, "source SHA"):
            watch.observe("unattended_2p",
                          [dict(row(main=False), head_sha=None)], NOW)
        # An actual valid foreign-branch row can still be ignored.
        self.assertEqual(watch.observe("product_windows",
                         [row(main=False)], NOW)["status"], "NOT_YET_OBSERVED")

    def test_fetch_main_branch_query_prevents_foreign_runs_crowding_page(self):
        # GitHub paginates before local filtering. A burst of manual or
        # foreign-branch runs must not hide an older main cron/push.
        from unittest.mock import patch

        class Reply:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, *args):
                return b'{"workflow_runs": []}'

        def check(request, timeout):
            self.assertTrue(request.full_url.endswith(
                f"/runs?branch=main&per_page={watch.MAX_RUNS}"))
            self.assertEqual(timeout, 15)
            return Reply()

        with patch.object(watch, "urlopen", check):
            self.assertEqual(watch.fetch_runs(
                "owner-hp-seeded-2p-research.yml", "test"), [])
            self.assertEqual(watch.fetch_runs(
                "owner-hp-main-windows-smoke.yml", "test"), [])

    def test_workflow_registration_distinguishes_active_disabled_and_unknown(self):
        import json
        from unittest.mock import patch
        name = "owner-hp-seeded-2p-research.yml"

        class Reply:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, *args):
                return json.dumps(self.payload).encode("utf-8")

        value = {"path": f".github/workflows/{name}", "state": "active"}
        def read(request, timeout):
            self.assertEqual(timeout, 15)
            self.assertEqual(
                request.full_url,
                f"https://api.github.com/repos/{watch.REPOSITORY}/actions/workflows/{name}",
            )
            return Reply(value)
        with patch.object(watch, "urlopen", read):
            for state in ("active", "deleted", "disabled_fork",
                          "disabled_manually", "disabled_inactivity"):
                value["state"] = state
                self.assertEqual(watch.fetch_workflow_state(name, "token"), state)
            for payload in (None, [], {}, {"state": "active"},
                            {"path": "other.yml", "state": "active"},
                            {"path": f".github/workflows/{name}", "state": "invented"}):
                value = payload
                with self.subTest(payload=payload):
                    with self.assertRaisesRegex(ValueError, "unverifiable"):
                        watch.fetch_workflow_state(name, "token")
        with self.assertRaisesRegex(ValueError, "unknown owner HP"):
            watch.fetch_workflow_state("foreign.yml", "token")

    def test_report_is_compact_and_links_exact_run(self):
        result = {"schema": "ur-hp-compute-watch/1", "lanes": {
            "unattended_2p": watch.observe("unattended_2p", [row()], NOW),
            "product_windows": watch.observe("product_windows",
                                             [row(event="push", rid=200)], NOW),
        }}
        rendered = watch.render(result)
        self.assertIn("[#100](https://github.com/gamesbyian/UR-Recomp/actions/runs/100)", rendered)
        self.assertIn("research trial does not establish", rendered)
        self.assertIn("Registered workflow state", rendered)
        self.assertIn("disabled or deleted registration", rendered)
        self.assertNotIn("release gate earned", rendered)

    def test_existing_daily_ops_gets_read_only_monitor_and_bounded_artifacts(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cron: '30 14 * * *'", source)
        self.assertIn("actions: read", source)
        self.assertIn("python3 tools/hp_compute_watch.py", source)
        self.assertIn("python3 -m unittest -q tests.unit.test_hp_compute_watch", source)
        self.assertIn("hp-compute-status.json", source)
        self.assertIn("hp-compute-status.md", source)
        self.assertNotIn("actions: write", source)
        self.assertNotIn("contents: write", source)


if __name__ == "__main__":
    unittest.main()

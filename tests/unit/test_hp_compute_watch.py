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
        self.assertEqual(missing["status"], "NOT_YET_OBSERVED")
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

    def test_never_accepts_wrong_branch_event_future_or_unbound_identity(self):
        x = watch.observe("unattended_2p", [row(main=False)], NOW)
        self.assertEqual(x["status"], "NOT_YET_OBSERVED")
        with self.assertRaisesRegex(ValueError, "future"):
            watch.observe("unattended_2p",
                          [row(when=NOW + timedelta(minutes=2))], NOW)
        with self.assertRaisesRegex(ValueError, "run ID"):
            watch.observe("unattended_2p", [row(rid="fake")], NOW)
        with self.assertRaises(ValueError):
            watch.observe("unknown", [], NOW)

    def test_report_is_compact_and_links_exact_run(self):
        result = {"schema": "ur-hp-compute-watch/1", "lanes": {
            "unattended_2p": watch.observe("unattended_2p", [row()], NOW),
            "product_windows": watch.observe("product_windows",
                                             [row(event="push", rid=200)], NOW),
        }}
        rendered = watch.render(result)
        self.assertIn("[#100](https://github.com/gamesbyian/UR-Recomp/actions/runs/100)", rendered)
        self.assertIn("research trial does not establish", rendered)
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

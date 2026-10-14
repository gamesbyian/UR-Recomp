"""Synthetic scheduler contracts. These fixtures are queue snapshots and
ledger rows, never native/original emulator outcomes or research evidence."""
from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_cumulative_ledger as ledger  # noqa: E402
import research_admission as a  # noqa: E402

NOW = dt.datetime(2026, 10, 14, 3, 0, tzinfo=dt.timezone.utc)
SHA = "a" * 40
WORKFLOW = ROOT / ".github/workflows/qa-cumulative-research.yml"


def snap(linux=0, windows=0, queued=0, queued_age=0, macos=0):
    return {"schema": a.SCHEMA, "active_jobs": {"linux": linux, "windows": windows, "macos": macos},
            "queued_jobs": {"linux": queued, "windows": 0, "macos": 0},
            "oldest_queued_seconds": queued_age, "runs_inspected": 1, "truncated": False,
            "research_active_jobs": 0, "unseen_repository_reserve": a.UNSEEN_REPOSITORY_RESERVE}


def req(campaign="frontier", event="workflow_dispatch", admission="auto", parallel=2,
        cases=100, minutes=15, trials=3):
    return {"campaign": campaign, "event": event, "admission": admission,
            "frontier_parallel": parallel, "frontier_cases": cases,
            "minutes": minutes, "windows_trials": trials}


def job(status, labels=("ubuntu-latest",), created=None, started=None, completed=None,
        name="j", conclusion=None):
    return {"status": status, "labels": list(labels), "name": name, "conclusion": conclusion,
            "created_at": created, "started_at": started, "completed_at": completed}


def row(campaign, disposition="completed_positive", digest=None, run_id=1):
    value = {"campaign": campaign, "origin": "coordinator", "disposition": disposition,
             "github_run_id": run_id}
    if digest:
        value["producer_digest"] = digest
    return value


class AdmissionDecisions(unittest.TestCase):
    def test_idle_capacity_admits_exact_request(self):
        d = a.decide(snap(), req(parallel=4))
        self.assertEqual((d["decision"], d["frontier_parallel"]), ("admit", 4))
        self.assertFalse(d["scientific_identity_changed"])
        self.assertEqual(d["release_gate_credit"], 0)

    def test_busy_development_downsizes_only_frontier_parallelism(self):
        # 20 - 4 unseen - 8 busy - 6 agent headroom = 2 spare.
        d = a.decide(snap(linux=8), req(parallel=4))
        self.assertEqual((d["decision"], d["frontier_parallel"]), ("admit_downsized", 2))
        d = a.decide(snap(linux=9), req(parallel=4))
        self.assertEqual(d["frontier_parallel"], 1)
        self.assertIn("same cases, seeds and plan", d["reason"])

    def test_no_spare_capacity_defers(self):
        d = a.decide(snap(linux=10, windows=1), req())
        self.assertEqual(d["decision"], "defer")
        self.assertFalse(d["admitted"])

    def test_long_queue_means_saturation_regardless_of_counts(self):
        self.assertEqual(a.decide(snap(queued=1, queued_age=a.QUEUE_SATURATION_SECONDS),
                                  req())["decision"], "defer")
        # A just-queued job is normal scheduling latency, not saturation.
        self.assertEqual(a.decide(snap(queued=1, queued_age=5), req())["decision"], "admit")

    def test_large_campaigns_need_a_quiet_period(self):
        quiet = a.decide(snap(linux=2), req(cases=1000, parallel=4))
        self.assertTrue(quiet["admitted"])
        busy = a.decide(snap(linux=a.QUIET_ACTIVE_JOBS + 1), req(cases=1000))
        self.assertEqual(busy["decision"], "defer")
        self.assertIn("batches", busy["reason"])
        # Windows 60-trial soak is large too; a 3-trial smoke is not.
        self.assertEqual(a.decide(snap(linux=6), req("windows", trials=60))["decision"], "defer")
        self.assertTrue(a.decide(snap(linux=6), req("windows", trials=3))["admitted"])

    def test_schedule_keeps_extra_margin_and_defers_when_blind(self):
        # Spare 3 admits a manual 3-runner fault lane but not a scheduled one.
        self.assertTrue(a.decide(snap(linux=7), req("fault-recovery"))["admitted"])
        self.assertFalse(a.decide(snap(linux=7), req("fault-recovery", event="schedule"))["admitted"])
        self.assertEqual(a.decide(None, req(event="schedule"))["decision"], "defer")
        blind = a.decide(None, req(parallel=4))
        self.assertEqual((blind["decision"], blind["frontier_parallel"]), ("admit_downsized", 2))

    def test_force_overrides_but_keeps_the_snapshot(self):
        d = a.decide(snap(linux=30, queued=9, queued_age=9999), req(admission="force", parallel=4))
        self.assertEqual((d["decision"], d["frontier_parallel"]), ("admit", 4))
        self.assertEqual(d["snapshot"]["active_jobs"]["linux"], 30)

    def test_macos_does_not_consume_the_shared_ceiling(self):
        self.assertEqual(a.decide(snap(macos=5), req(parallel=4))["frontier_parallel"], 4)

    def test_invalid_requests_fail_closed(self):
        for bad in (req("bogus"), req(admission="maybe"), req(parallel=3)):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    a.decide(snap(), bad)


class QueueSnapshots(unittest.TestCase):
    def test_counts_jobs_by_runner_class_and_excludes_own_run(self):
        old = (NOW - dt.timedelta(seconds=400)).isoformat()
        runs = [
            {"run": {"id": 1, "path": ".github/workflows/x.yml"},
             "jobs": [job("in_progress"), job("queued", created=old, name="build"),
                      job("in_progress", labels=("windows-2022",)), job("completed")]},
            {"run": {"id": 2, "path": ".github/workflows/qa-cumulative-research.yml"},
             "jobs": [job("in_progress")]},
            {"run": {"id": 99, "path": "self"}, "jobs": [job("in_progress")] * 5},
        ]
        s = a.summarize_jobs(runs, NOW, exclude_run_id=99)
        self.assertEqual(s["active_jobs"], {"linux": 2, "windows": 1, "macos": 0})
        self.assertEqual(s["queued_jobs"]["linux"], 1)
        self.assertEqual(s["oldest_queued_seconds"], 400)
        self.assertEqual(s["research_active_jobs"], 1)
        self.assertEqual(s["runs_inspected"], 2)

    def test_matrix_max_parallel_backlog_is_not_runner_saturation(self):
        old = (NOW - dt.timedelta(seconds=900)).isoformat()
        win = ("windows-2022",)
        runs = [{"run": {"id": 5, "path": ".github/workflows/qa-cumulative-research.yml"},
                 "jobs": [job("in_progress", win, name="windows / scenario (guest-0)"),
                          job("in_progress", win, name="windows / scenario (guest-1)"),
                          job("queued", win, created=old, name="windows / scenario (launcher-0)"),
                          job("queued", win, created=old, name="windows / scenario (launcher-1)")]}]
        s = a.summarize_jobs(runs, NOW)
        self.assertEqual(s["queued_jobs"]["windows"], 0)
        self.assertEqual(s["matrix_throttled_jobs"]["windows"], 2)
        self.assertEqual(s["oldest_queued_seconds"], 0)
        # A queued job with no running sibling is genuine runner contention.
        runs[0]["jobs"].append(job("queued", created=old, name="other / build"))
        self.assertEqual(a.summarize_jobs(runs, NOW)["oldest_queued_seconds"], 900)


class FailureAwareRotation(unittest.TestCase):
    DIGESTS = {lane: f"{i:064x}" for i, lane in enumerate(a.CAMPAIGNS)}

    def test_never_run_lanes_first_then_least_recent(self):
        lane, _ = a.auto_lane([row("frontier"), row("windows")], self.DIGESTS)
        self.assertEqual(lane, "native-2p")
        history = [row(lane, run_id=i) for i, lane in enumerate(a.CAMPAIGNS)]
        history.append(row("native-2p", run_id=50))
        self.assertEqual(a.auto_lane(history, self.DIGESTS)[0], "windows")

    def test_unchanged_failing_producer_is_not_retried_automatically(self):
        history = [row(lane, run_id=i) for i, lane in enumerate(a.CAMPAIGNS)]
        history[0] = row("native-2p", "incomplete_or_failed", self.DIGESTS["native-2p"], 0)
        lane, excluded = a.auto_lane(history, self.DIGESTS)
        self.assertNotEqual(lane, "native-2p")
        self.assertIn("native-2p", excluded)
        changed = dict(self.DIGESTS, **{"native-2p": "f" * 64})
        self.assertEqual(a.auto_lane(history, changed)[0], "native-2p")

    def test_legacy_failure_without_digest_ranks_after_healthy_lanes(self):
        history = [row("native-2p", "incomplete_or_failed", run_id=1)]
        history += [row(lane, run_id=i + 2) for i, lane in enumerate(a.CAMPAIGNS[1:])]
        self.assertEqual(a.auto_lane(history, self.DIGESTS)[0], "windows")
        only_legacy = [row(lane, "incomplete_or_failed", run_id=i)
                       for i, lane in enumerate(a.CAMPAIGNS)]
        self.assertEqual(a.auto_lane(only_legacy, self.DIGESTS)[0], "native-2p")

    def test_all_lanes_failing_unchanged_stops_automation(self):
        history = [row(lane, "incomplete_or_failed", self.DIGESTS[lane], i)
                   for i, lane in enumerate(a.CAMPAIGNS)]
        with self.assertRaises(ValueError):
            a.auto_lane(history, self.DIGESTS)

    def test_producer_digest_tracks_listed_files(self):
        for lane in a.CAMPAIGNS:
            self.assertRegex(a.producer_digest(ROOT, lane), "^[0-9a-f]{64}$")
            for rel in a.PRODUCER_PATHS[lane]:
                self.assertTrue((ROOT / rel).is_file(), rel)


class UsageAndLedgerIntegration(unittest.TestCase):
    JOBS = [job("completed", started="2026-10-14T00:00:00Z", completed="2026-10-14T00:30:00Z",
                conclusion="success", name="experiments"),
            job("completed", labels=("windows-2022",), started="2026-10-14T00:00:00Z",
                completed="2026-10-14T00:06:00Z", conclusion="success", name="w"),
            job("completed", conclusion="skipped", name="skipped"),
            job("in_progress", started="2026-10-14T00:00:00Z", name="commit-evidence")]

    def test_runner_usage_is_measured_from_job_times(self):
        u = a.summarize_usage(self.JOBS, exclude_names=("commit-evidence",))
        a.validate_usage(u)
        self.assertEqual(u["runner_minutes"], {"linux": 30.0, "windows": 6.0, "macos": 0.0})
        self.assertEqual((u["jobs_counted"], u["total_runner_minutes"]), (2, 36.0))

    def test_deferral_consumes_nothing_so_a_later_admit_gets_the_same_window(self):
        empty = {"schema": ledger.SCHEMA, "records": []}
        digest = a.producer_digest(ROOT, "native-2p")
        first = ledger.make_plan(empty, selected="native-2p", source_sha=SHA, minutes=15,
                                 windows_trials=3, run_id=10, producer_digest=digest)
        # A deferred run (id 11) never calls make_plan/append; run 12 sees the
        # identical ledger and therefore the identical seed window.
        later = ledger.make_plan(empty, selected="native-2p", source_sha=SHA, minutes=15,
                                 windows_trials=3, run_id=12, producer_digest=digest)
        self.assertEqual(first["base_seed"], later["base_seed"])
        self.assertEqual(first["sequence"], later["sequence"])

    def test_digest_and_usage_are_signed_into_the_record_without_changing_seeds(self):
        empty = {"schema": ledger.SCHEMA, "records": []}
        plain = ledger.make_plan(empty, selected="windows", source_sha=SHA, minutes=15,
                                 windows_trials=3, run_id=10)
        digest = a.producer_digest(ROOT, "windows")
        plan = ledger.make_plan(empty, selected="windows", source_sha=SHA, minutes=15,
                                windows_trials=3, run_id=10, producer_digest=digest)
        self.assertEqual(plain["base_seed"], plan["base_seed"])
        usage = a.summarize_usage(self.JOBS, exclude_names=("commit-evidence",))
        new, record = ledger.append(empty, plan, None, "cancelled", usage)
        self.assertEqual(record["producer_digest"], digest)
        self.assertEqual(record["runner_usage"]["total_runner_minutes"], 36.0)
        # Cancellation is now recorded as such, still with no credit.
        self.assertEqual(record["metrics"]["reusable_job_result"], "cancelled")
        self.assertIs(record["metrics"]["aggregate_present"], False)
        self.assertEqual(record["disposition"], "incomplete_or_failed")
        ledger.validate_ledger(new)
        # The failure is now visible to the scheduler as an unchanged producer.
        lane, excluded = a.auto_lane(new["records"], {"windows": digest})
        self.assertIn("windows", excluded)
        self.assertNotEqual(lane, "windows")
        # Tampering with usage breaks the record signature.
        forged = {**new, "records": [{**record, "runner_usage": {**usage, "total_runner_minutes": 1}}]}
        with self.assertRaises(ValueError):
            ledger.validate_ledger(forged)

    def test_malformed_usage_is_flagged_not_fatal(self):
        empty = {"schema": ledger.SCHEMA, "records": []}
        plan = ledger.make_plan(empty, selected="windows", source_sha=SHA, minutes=15,
                                windows_trials=3, run_id=10)
        _, record = ledger.append(empty, plan, None, "failure", {"schema": "nope"})
        self.assertTrue(record["runner_usage_rejected"])
        self.assertNotIn("runner_usage", record)

    def test_legacy_records_without_new_fields_still_validate(self):
        legacy = {"campaign": "frontier", "origin": "coordinator", "sequence": 0,
                  "base_seed": 50000000, "source_sha": SHA, "github_run_id": 7,
                  "minutes": 15, "windows_trials": 3, "frontier_cases": 100,
                  "disposition": "incomplete_or_failed",
                  "metrics": {"reason": "original workflow or aggregate unavailable"},
                  "release_gate_credit": 0}
        legacy["record_sha256"] = ledger.digest(legacy)
        ledger.validate_ledger({"schema": ledger.SCHEMA, "records": [legacy]})


class FailedRunEvidenceIsRetainedNotCredited(unittest.TestCase):
    def test_partial_original_native_aggregate_is_kept_as_uncredited_diagnostic(self):
        empty = {"schema": ledger.SCHEMA, "records": []}
        plan = ledger.make_plan(empty, selected="original-native", source_sha=SHA, minutes=15,
                                windows_trials=3, run_id=10)
        partial = {"schema": "ur-qa01-event-campaign/1", "source_sha": SHA,
                   "transport_complete": False, "release_admissions": 0,
                   "selected_cases": 3, "completed": 2,
                   "counts": {"strict_candidate": 0, "strict_divergence": 2,
                              "producer_error": 1, "missing_evidence": 0},
                   "results": [{"case": "zoom-zoo", "disposition": "strict_divergence"},
                               {"case": "bowl", "disposition": "strict_divergence"},
                               {"case": "switcher", "disposition": "producer_error",
                                "reason": "reference core exited 2"}]}
        _, row = ledger.append(empty, plan, partial, "failure")
        self.assertEqual(row["disposition"], "incomplete_or_failed")
        self.assertNotIn("cases", row["metrics"])
        diag = row["metrics"]["diagnostic"]
        self.assertTrue(diag["aggregate_bound_to_plan"])
        self.assertEqual(diag["case_counts"]["strict_divergence"], 2)
        self.assertEqual(diag["case_dispositions"][2]["reason"], "reference core exited 2")
        self.assertEqual(row["release_gate_credit"], 0)

    def test_aggregate_from_another_source_is_not_described(self):
        empty = {"schema": ledger.SCHEMA, "records": []}
        plan = ledger.make_plan(empty, selected="graphics", source_sha=SHA, minutes=15,
                                windows_trials=3, run_id=10)
        _, row = ledger.append(empty, plan, {"schema": "ur-cumulative-graphics/1",
                                             "source_sha": "b" * 40, "issues": ["x"]}, "failure")
        diag = row["metrics"]["diagnostic"]
        self.assertFalse(diag["aggregate_bound_to_plan"])
        self.assertNotIn("issues", diag)

    def test_failed_job_and_first_failed_step_survive_run_deletion(self):
        jobs = [{"name": "original-native / cases (switcher)", "conclusion": "failure",
                 "status": "completed", "labels": ["ubuntu-22.04"],
                 "started_at": "2026-10-14T00:00:00Z", "completed_at": "2026-10-14T00:10:00Z",
                 "steps": [{"name": "Checkout", "conclusion": "success"},
                           {"name": "Run original/native producer", "conclusion": "failure"}]},
                {"name": "commit-evidence", "conclusion": "failure", "status": "in_progress",
                 "labels": [], "steps": []}]
        usage = a.summarize_usage(jobs, exclude_names=("commit-evidence",))
        a.validate_usage(usage)
        self.assertEqual(usage["failed_jobs"], [{
            "job": "original-native / cases (switcher)", "conclusion": "failure",
            "first_failed_step": "Run original/native producer"}])
        with self.assertRaises(ValueError):
            a.validate_usage({**usage, "failed_jobs": [{"job": 1}]})


class CoordinatorWorkflowContract(unittest.TestCase):
    def test_admission_precedes_reservation_and_gates_every_writer(self):
        text = WORKFLOW.read_text()
        self.assertIn("actions: read", text)
        self.assertLess(text.index("research_admission.py decide"),
                        text.index("qa_cumulative_ledger.py plan"))
        self.assertIn("if: ${{ steps.admission.outputs.admitted == 'true' }}\n        id: plan", text)
        self.assertIn("needs.reserve.outputs.campaign != ''", text)
        self.assertIn("max_parallel: ${{ needs.reserve.outputs.frontier_parallel }}", text)
        self.assertIn("options: [auto, force]", text)
        # Never cancel an admitted experiment; single writer remains global.
        self.assertIn("group: qa-cumulative-research-single-ledger-writer", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("--usage", text)


if __name__ == "__main__":
    unittest.main()

"""No-network controls for manual, source-bound HP research delivery census."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest import TestCase, mock
from urllib.parse import parse_qs, urlparse
import subprocess

from tools.ci import hp_research_delivery_census as hp

START = "2026-11-02T00:00:00Z"
END = "2026-11-05T23:59:59Z"


def run(rid, created="2026-11-02T00:05:00Z",
        event="schedule", conclusion="success"):
    return {
        "id": rid, "created_at": created, "event": event,
        "name": hp.WORKFLOW_NAME, "path": hp.WORKFLOW_PATH,
        "head_branch": "main", "head_sha": "a" * 40,
        "status": "completed", "conclusion": conclusion, "run_attempt": 1,
    }


def job(jid, rid, started="2026-11-02T00:05:05Z",
        completed="2026-11-02T00:10:05Z", conclusion="success"):
    return {
        "id": jid, "run_id": rid, "run_attempt": 1,
        "name": hp.JOB_NAME,
        "runner_name": hp.RUNNER_NAME, "status": "completed",
        "conclusion": conclusion, "started_at": started,
        "completed_at": completed,
    }


class FakeGitHub:
    def __init__(self, runs=None, jobs=None):
        self.runs = deepcopy(runs if runs is not None else [
            run(17), run(18, created="2026-11-03T00:06:00Z",
                         event="workflow_dispatch", conclusion="failure"),
        ])
        self.jobs = deepcopy(jobs if jobs is not None else {
            17: [job(301, 17)],
            18: [job(302, 18, started="2026-11-03T00:06:04Z",
                     completed="2026-11-03T00:15:04Z", conclusion="failure")],
        })
        self.calls = []
        self.drift = False
        self.short_page = False
        self.override_total = None

    def __call__(self, path):
        self.calls.append(path)
        url = urlparse(path)
        args = parse_qs(url.query)
        page = int(args["page"][0])
        if url.path.endswith("/workflows/402410752/runs"):
            total = len(self.runs)
            if self.override_total is not None:
                total = self.override_total
            if self.drift and page == 2:
                total -= 1
            start = (page - 1) * 100
            items = self.runs[start:start + (99 if self.short_page else 100)]
            return {"total_count": total, "workflow_runs": deepcopy(items)}
        if "/runs/" in url.path and url.path.endswith("/jobs"):
            rid = int(url.path.split("/runs/")[1].split("/")[0])
            if args.get("filter") != ["latest"]:
                raise AssertionError("job attempt policy must be explicit")
            items = self.jobs.get(rid, [])
            return {"total_count": len(items),
                    "jobs": deepcopy(items[(page - 1) * 100:page * 100])}
        raise AssertionError("unexpected GitHub source route: " + path)


class HPCensusTests(TestCase):
    def test_full_source_bound_observation(self):
        receipt = hp.measure(FakeGitHub(), START, END, workers=1)
        self.assertEqual(receipt["schema"], "ur-hp-research-delivery-census/1")
        self.assertEqual(receipt["counts"]["runs"], 2)
        self.assertEqual(receipt["counts"]["by_event"],
                         {"schedule": 1, "workflow_dispatch": 1})
        self.assertEqual(receipt["counts"]["by_outcome"],
                         {"success": 1, "failure": 1})
        self.assertEqual(receipt["counts"]["by_created_utc_date"],
                         {"2026-11-02": 1, "2026-11-03": 1})
        self.assertEqual(receipt["timing"]["window_minutes"], 5760)
        self.assertEqual(receipt["timing"]["observed_job_interval_minutes"], 14)
        self.assertEqual(receipt["timing"]["total_queue_minutes"], 0.15)
        self.assertEqual(receipt["timing"]["max_queue_minutes"], 0.08333)
        self.assertEqual(receipt["timing"]["queue_minutes_excluding_max"], 0.06667)
        self.assertEqual(receipt["timing"]["job_interval_minutes_by_event"],
                         {"schedule": 5, "workflow_dispatch": 9})
        self.assertEqual(receipt["timing"]["median_queue_minutes"], 0.075)
        self.assertEqual(receipt["job_attempt_policy"], "latest")
        self.assertEqual(receipt["queue_over_30m"], [])
        self.assertTrue(receipt["latest_job_census_complete"])
        self.assertIn("not measured CPU", receipt["limitations"])
        self.assertIn("- Runs: **2**", hp.render_markdown(receipt))

    def test_inclusive_source_bounds_and_utc_offset_grouping(self):
        f = FakeGitHub(
            runs=[run(17, created="2026-11-02T02:05:00+02:00")],
            jobs={17: [job(301, 17, started="2026-11-02T00:05:05.000Z",
                           completed="2026-11-02T00:10:05.000+00:00")]},
        )
        r = hp.measure(f, START, END, workers=1)
        self.assertEqual(r["counts"]["by_created_utc_date"],
                         {"2026-11-02": 1})
        self.assertEqual(r["runs"][0]["queue_seconds"], 5)

    def test_unstarted_or_extra_jobs_cannot_be_complete_census(self):
        for jobs in ([], [job(301, 17), job(302, 17)]):
            with self.subTest(rows=len(jobs)):
                f = FakeGitHub(runs=[run(17)], jobs={17: jobs})
                with self.assertRaisesRegex(ValueError, "latest jobs"):
                    hp.measure(f, START, END, workers=1)

    def test_inverted_job_and_queue_timing_rejected(self):
        cases = [
            job(301, 17, started="2026-11-02T00:04:59Z"),
            job(301, 17, completed="2026-11-02T00:05:04Z"),
            job(301, 17, completed=None),
            job(301, 17, started="2026-11-02T00:05:00"),
        ]
        for row in cases:
            with self.subTest(row=row):
                f = FakeGitHub(runs=[run(17)], jobs={17: [row]})
                with self.assertRaises(ValueError):
                    hp.measure(f, START, END, workers=1)

    def test_hp_job_end_conflicting_with_observed_steps_is_unknown(self):
        # A historical HP DST transition yielded a spurious extra hour in
        # the GitHub job end. No corrected time should be invented.
        for end in ("2026-11-02T01:10:05Z",
                    "2026-11-02T00:05:05Z"):
            with self.subTest(reported_end=end):
                record = job(301, 17, completed=end)
                record["steps"] = [{
                    "name": "Real last step",
                    "started_at": "2026-11-02T00:09:00Z",
                    "completed_at": "2026-11-02T00:10:05Z",
                }]
                f = FakeGitHub(runs=[run(17)], jobs={17: [record]})
                with self.assertRaisesRegex(
                        ValueError, "untrusted job end relative to final step"):
                    hp.measure(f, START, END, workers=1)

    def test_hp_job_end_step_evidence_normal_envelope_and_offsets(self):
        record = job(301, 17)
        record["steps"] = [{
            "name": "Real final step",
            "completed_at": "2026-11-02T00:09:59+00:00",
        }]
        f = FakeGitHub(runs=[run(17)], jobs={17: [record]})
        receipt = hp.measure(f, START, END, workers=1)
        self.assertEqual(receipt["timing"]["observed_job_interval_minutes"], 5)

    def test_malformed_hp_step_end_evidence_fails_closed(self):
        for steps in ("bad", [None], [{"completed_at": "naive"}],
                      [{"completed_at": "bad-time"}]):
            with self.subTest(steps=steps):
                record = job(301, 17)
                record["steps"] = steps
                f = FakeGitHub(runs=[run(17)], jobs={17: [record]})
                with self.assertRaises(ValueError):
                    hp.measure(f, START, END, workers=1)

    def test_job_source_identity_runner_name_and_outcome_rejected(self):
        overrides = [
            {"id": 0}, {"id": "301"}, {"run_id": 18},
            {"run_id": None},
            {"run_id": "17"}, {"run_attempt": 2},
            {"run_attempt": False}, {"run_attempt": None},
            {"run_attempt": "1"}, {"name": "other job"},
            {"runner_name": "github-hosted-windows"}, {"status": "queued"},
            {"conclusion": "failure"},
        ]
        for values in overrides:
            with self.subTest(overrides=values):
                row = {**job(301, 17), **values}
                f = FakeGitHub(runs=[run(17)], jobs={17: [row]})
                with self.assertRaises(ValueError):
                    hp.measure(f, START, END, workers=1)

    def test_missing_or_malformed_latest_job_attempt_is_unknown(self):
        for value in (None, "missing", "1", False, 0, -1, 2):
            with self.subTest(job_attempt=value):
                latest = job(301, 17)
                if value == "missing":
                    del latest["run_attempt"]
                else:
                    latest["run_attempt"] = value
                f = FakeGitHub(runs=[run(17)], jobs={17: [latest]})
                with self.assertRaisesRegex(
                        ValueError, "missing a source-consistent completed HP job"):
                    hp.measure(f, START, END, workers=1)

    def test_read_only_latest_job_must_match_selected_rerun_attempt(self):
        run_2 = {**run(17), "run_attempt": 2}
        latest = {**job(301, 17), "run_attempt": 2}
        f = FakeGitHub(runs=[run_2], jobs={17: [latest]})
        self.assertEqual(hp.measure(f, START, END, workers=1)
                         ["counts"]["rerun_workflow_ids"], 1)
        # One stale attempt hidden under an otherwise valid filter=latest
        # response invalidates the whole measurement, never a partial sum.
        older = {**latest, "run_attempt": 1}
        with self.assertRaisesRegex(
                ValueError, "missing a source-consistent completed HP job"):
            hp.measure(FakeGitHub(runs=[run_2], jobs={17: [older]}),
                       START, END, workers=1)

    def test_run_attempt_or_conclusion_drift_during_job_read_rejected(self):
        class ChangedMidCensus(FakeGitHub):
            def __init__(self, field, value):
                super().__init__(runs=[run(17)], jobs={17: [job(301, 17)]})
                self.field, self.value = field, value
                self.run_reads = 0

            def __call__(self, path):
                if "/workflows/402410752/runs?" in path:
                    self.run_reads += 1
                    if self.run_reads == 2:
                        self.runs[0][self.field] = self.value
                return super().__call__(path)

        for field, value in (
            ("run_attempt", 2),
            ("head_sha", "b" * 40),
            ("conclusion", "failure"),
        ):
            f = ChangedMidCensus(field, value)
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "changed during job reads"):
                hp.measure(f, START, END, workers=1)

    def test_stable_source_rechecked_after_job_census(self):
        f = FakeGitHub()
        hp.measure(f, START, END, workers=1)
        run_reads = [path for path in f.calls if
                     "/workflows/402410752/runs?" in path]
        self.assertEqual(len(run_reads), 2)

    def test_duplicate_job_id_across_runs(self):
        f = FakeGitHub()
        f.jobs[18][0]["id"] = 301
        with self.assertRaisesRegex(ValueError, "duplicate job ID"):
            hp.measure(f, START, END, workers=1)

    def test_bad_run_identity_or_origin_rejected(self):
        changes = [
            {"name": "other workflow"}, {"path": "other.yml"},
            {"head_branch": "side"}, {"head_sha": "wrong"},
            {"workflow_id": 1}, {"repository": {"full_name": "other/repo"}},
            {"head_sha": "A" * 39}, {"event": "pull_request"},
            {"event": "push"}, {"status": "queued"}, {"conclusion": None},
            {"run_attempt": 0}, {"run_attempt": True}, {"id": "17"},
            {"id": 0},
        ]
        for patch in changes:
            with self.subTest(patch=patch):
                r = {**run(17), **patch}
                f = FakeGitHub(runs=[r], jobs={17: [job(301, 17)]})
                with self.assertRaises(ValueError):
                    hp.measure(f, START, END, workers=1)

    def test_duplicate_run_id_and_out_of_bounds_rejected(self):
        for rows in (
            [run(17), run(17)],
            [run(17, created="2026-11-01T23:59:59Z")],
            [run(17, created="2026-11-06T00:00:00Z")],
        ):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    hp.measure(FakeGitHub(runs=rows), START, END, workers=1)

    def test_count_drift_and_truncated_population_fail_closed(self):
        many = [
            run(k, created="2026-11-02T00:05:00Z")
            for k in range(1, 102)
        ]
        for mode in ("drift", "short_page"):
            f = FakeGitHub(runs=many)
            setattr(f, mode, True)
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    hp.read_runs(f, START, END)

    def test_multiple_pages_really_exercised(self):
        rows = [run(k) for k in range(1, 102)]
        f = FakeGitHub(runs=rows)
        found = hp.read_runs(f, START, END)
        self.assertEqual(len(found), 101)
        self.assertTrue(any("page=2" in path for path in f.calls))

    def test_fails_on_api_1000_cap(self):
        f = FakeGitHub()
        f.override_total = 1001
        with self.assertRaisesRegex(ValueError, "over-limit"):
            hp.read_runs(f, START, END)

    def test_bad_page_types_and_rows_are_rejected(self):
        for override in (
            {"total_count": "1", "workflow_runs": []},
            {"total_count": 1, "workflow_runs": None},
            {"total_count": 1, "workflow_runs": ["bad"]},
            {"total_count": -1, "workflow_runs": []},
        ):
            with self.subTest(override=override):
                with self.assertRaisesRegex(ValueError, "invalid or over-limit"):
                    hp.fetch_pages(lambda _: override, "test?per_page=100",
                                   "workflow_runs")

    def test_window_bounded_and_exact_z(self):
        for start, end in (
            ("2026-11-02T00:00:00+00:00", END),
            ("2026-11-02T00:00:00Z", "2026-11-02T00:00:00Z"),
            ("2026-11-02T00:00:00Z", "2026-11-10T00:00:00Z"),
            (None, END), (True, END),
        ):
            with self.subTest(bounds=(start, end)):
                with self.assertRaises(ValueError):
                    hp.checked_window(start, end)

    def test_timestamp_requires_timezone_and_valid_offset(self):
        for t in ("2026-11-02T00:00:00", "2026-11-02T00:00:00+24:00",
                  "2026-11-02T00:00:00.1234567Z", "not-time", None):
            with self.subTest(value=t), self.assertRaises(ValueError):
                hp.utc(t)
        self.assertEqual(
            hp.utc("2026-11-02T02:00:00+02:00"),
            datetime(2026, 11, 2, tzinfo=timezone.utc)
        )

    def test_rerun_count_is_scope_signal_only(self):
        f = FakeGitHub(runs=[{**run(17), "run_attempt": 2}],
                       jobs={17: [{**job(301, 17), "run_attempt": 2}]})
        r = hp.measure(f, START, END, workers=1)
        self.assertEqual(r["counts"]["rerun_workflow_ids"], 1)
        self.assertEqual(r["job_attempt_policy"], "latest")

    def test_long_queue_does_not_claim_cpu_starvation(self):
        f = FakeGitHub(
            runs=[run(17)],
            jobs={17: [job(301, 17, started="2026-11-02T01:15:00Z",
                           completed="2026-11-02T01:20:00Z")]},
        )
        r = hp.measure(f, START, END, workers=1)
        self.assertEqual(len(r["queue_over_30m"]), 1)
        self.assertEqual(r["queue_over_30m"][0]["queue_minutes"], 70)
        self.assertIn("cause unknown", r["queue_over_30m"][0]["classification"])
        self.assertIn(">30-minute queues", hp.render_markdown(r))

    def test_empty_complete_population_has_no_fabricated_median(self):
        r = hp.measure(FakeGitHub(runs=[], jobs={}), START, END, workers=1)
        self.assertEqual(r["counts"]["runs"], 0)
        self.assertIsNone(r["timing"]["median_queue_minutes"])
        self.assertEqual(r["timing"]["observed_job_interval_minutes"], 0)

    def test_worker_limit_and_invalid_input(self):
        for workers in (0, -1, 7, 1.0, True, None):
            with self.subTest(workers=workers), self.assertRaises(ValueError):
                hp.measure(FakeGitHub(), START, END, workers=workers)

    def test_environment_credentials_before_cli(self):
        hp.auth_token.cache_clear()
        try:
            with mock.patch.dict("os.environ",
                                 {"GH_TOKEN": "  owner-token  ",
                                  "GITHUB_TOKEN": "secondary"}, clear=True):
                with mock.patch("subprocess.run") as process:
                    self.assertEqual(hp.auth_token(), "owner-token")
                    process.assert_not_called()
        finally:
            hp.auth_token.cache_clear()

    def test_cli_credentials_cached_and_not_logged(self):
        hp.auth_token.cache_clear()
        try:
            with mock.patch.dict("os.environ", {}, clear=True):
                with mock.patch("subprocess.run",
                                return_value=mock.Mock(stdout="  cli-secret  ")) as run:
                    self.assertEqual(hp.auth_token(), "cli-secret")
                    self.assertEqual(hp.auth_token(), "cli-secret")
                    run.assert_called_once()
                    self.assertEqual(run.call_args.args[0], ["gh", "auth", "token"])
                    self.assertTrue(run.call_args.kwargs["capture_output"])
        finally:
            hp.auth_token.cache_clear()

    def test_missing_auth_fails_before_http(self):
        hp.auth_token.cache_clear()
        try:
            with mock.patch.dict("os.environ", {}, clear=True):
                with mock.patch("subprocess.run",
                                side_effect=FileNotFoundError):
                    with mock.patch.object(hp, "urlopen") as open_url:
                        with self.assertRaisesRegex(RuntimeError, "authentication required"):
                            hp.api_get(hp.ROOT +
                                "/workflows/402410752/runs?per_page=100&page=1")
                        open_url.assert_not_called()
        finally:
            hp.auth_token.cache_clear()

    def test_cli_error_does_not_echo_secret(self):
        hp.auth_token.cache_clear()
        try:
            with mock.patch.dict("os.environ", {}, clear=True):
                with mock.patch("subprocess.run",
                                side_effect=subprocess.CalledProcessError(
                                    1, ["gh", "auth", "token"], "secret-value")):
                    with self.assertRaises(RuntimeError) as cm:
                        hp.auth_token()
                    self.assertNotIn("secret-value", str(cm.exception))
        finally:
            hp.auth_token.cache_clear()

    def test_route_guard_before_authentication(self):
        with mock.patch.object(hp, "auth_token") as token:
            with self.assertRaisesRegex(ValueError, "outside allowed"):
                hp.api_get("/repos/other/repo/actions/artifacts?per_page=100")
            token.assert_not_called()

    def test_markdown_has_no_billable_or_release_claim(self):
        text = hp.render_markdown(
            hp.measure(FakeGitHub(), START, END, workers=1)
        )
        self.assertIn("workflow_dispatch", text)
        self.assertIn("not measured CPU", text)
        self.assertIn("No source or runner changes", text)

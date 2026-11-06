"""No-network negative controls for read-only cancelled Actions timing census."""
from __future__ import annotations

import copy
import subprocess
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from tools.ci_cancelled_runner_census import (measure, span, get_run_census,
                                              get_run_jobs, render_markdown,
                                              auth_token, api_get, utc)

START = "2026-10-29T08:14:05Z"
END = "2026-11-05T08:14:05Z"
WORKFLOW = 123


def run(rid, status="cancelled", created=START):
    return {"id": rid, "workflow_id": WORKFLOW,
            "status": "completed", "run_attempt": 1, "head_sha": "a" * 40,
            "conclusion": status, "created_at": created}


def job(jid, start="2026-11-05T07:00:00Z",
        end="2026-11-05T07:01:00Z", conclusion="cancelled"):
    return {"id": jid, "started_at": start, "completed_at": end,
            "conclusion": conclusion}


class MockAPI:
    def __init__(self, runs=None, jobs=None, all_count=None):
        self.runs = runs if runs is not None else [run(17), run(18)]
        self.jobs = jobs if jobs is not None else {
            17: [job(101), job(102, end="2026-11-05T07:02:00Z",
                                conclusion="success")],
            18: [job(201, start="2026-11-05T07:10:01Z",
                         end="2026-11-05T07:10:00Z")],
        }
        self.all_count = all_count
        self.override = None
        self.calls = []

    def __call__(self, path):
        self.calls.append(path)
        if self.override:
            value = self.override(path)
            if value is not None:
                return copy.deepcopy(value)
        url = urlsplit(path)
        p = parse_qs(url.query)
        page = int(p.get("page", ["1"])[0])
        per_page = int(p.get("per_page", ["100"])[0])
        if "/actions/workflows/" in url.path:
            return {"total_count": len(self.runs) if "status" in p
                    else (len(self.runs) if self.all_count is None
                          else self.all_count),
                    "workflow_runs": copy.deepcopy(self.runs[
                        (page - 1)*per_page:page*per_page])}
        if "/actions/runs/" in url.path:
            rid = int(url.path.split("/")[-2])
            jobs = self.jobs.get(rid, [])
            return {"total_count": len(jobs),
                    "jobs": copy.deepcopy(jobs[
                        (page - 1)*per_page:page*per_page])}
        raise ValueError("Unexpected API path")


class CensusTests(unittest.TestCase):
    def test_explicit_seven_day_window(self):
        self.assertEqual(span(START, END), START + ".." + END)
        for a, b in ((END, START), (START, START), ("2026-10-29", END),
                     ("2026-10-28T08:14:04Z", END),
                     ("2026-10-29T08:14:05+00:00", END)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                span(a, b)

    def test_all_valid_time_and_missing_time_reported(self):
        report = measure(MockAPI(), START, END, workflows={"test": WORKFLOW},
                         workers=1)
        row = report["workflows"][0]
        self.assertEqual(row["all_runs"], 2)
        self.assertEqual(row["cancelled_runs"], 2)
        self.assertEqual(row["cancelled_with_started_jobs"], 1)
        self.assertEqual(row["valid_started"], 2)
        self.assertEqual(row["invalid_intervals"], 1)
        self.assertEqual(row["seconds_inside_cancelled_run"], 180)
        self.assertEqual(row["seconds_cancelled_jobs"], 60)
        self.assertIn("3.00", render_markdown(report))
        self.assertIn("neither proves billed", report["limitations"])
        self.assertEqual(report["job_attempt_policy"], "latest")
        self.assertEqual(report["schema"], "ur-ci-cancelled-runner-census/4")

    def test_long_job_start_to_first_step_gap(self):
        f = MockAPI(jobs={17: [{
            **job(301, end="2026-11-05T07:12:00Z"),
            "steps": [
                {"conclusion": "success", "started_at": "2026-11-05T07:06:00Z",
                 "completed_at": "2026-11-05T07:07:00Z"},
                {"conclusion": "cancelled", "started_at": "2026-11-05T07:07:00Z",
                 "completed_at": "2026-11-05T07:11:00Z"},
            ]}], 18: []})
        row = get_run_jobs(f, 17)
        self.assertEqual(row["seconds_inside_cancelled_run"], 720)
        self.assertEqual(row["seconds_in_timed_steps"], 300)
        self.assertEqual(row["seconds_job_to_first_step"], 360)
        self.assertEqual(row["timed_steps"], 2)
        self.assertEqual(row["jobs_with_timed_steps"], 1)

    def test_skipped_and_inverted_steps_excluded(self):
        f = MockAPI(jobs={17: [{
            **job(301),
            "steps": [
                {"conclusion": "skipped", "started_at": "2026-11-05T07:02:00Z",
                 "completed_at": "2026-11-05T07:01:59Z"},
                {"conclusion": "cancelled", "started_at": "2026-11-05T07:00:30Z",
                 "completed_at": "2026-11-05T07:00:20Z"},
                {"conclusion": "cancelled", "started_at": "2026-11-05T07:00:30Z",
                 "completed_at": "2026-11-05T07:00:50Z"},
            ]}], 18: []})
        row = get_run_jobs(f, 17)
        self.assertEqual(row["seconds_in_timed_steps"], 20)
        self.assertEqual(row["seconds_job_to_first_step"], 30)
        self.assertEqual(row["invalid_step_intervals"], 1)
        self.assertEqual(row["timed_steps"], 1)

    def test_missing_step_evidence_and_malformed_step(self):
        f = MockAPI(jobs={17: [job(301), {**job(302), "steps": []}], 18: []})
        row = get_run_jobs(f, 17)
        self.assertEqual(row["jobs_without_step_evidence"], 2)
        f.jobs[17][0]["steps"] = ["malformed"]
        with self.assertRaisesRegex(ValueError, "malformed job step"):
            get_run_jobs(f, 17)

    def test_steps_start_before_job_start_cannot_subtract_time(self):
        f = MockAPI(jobs={17: [{
            **job(301),
            "steps": [{"conclusion": "cancelled",
                       "started_at": "2026-11-05T06:59:59Z",
                       "completed_at": "2026-11-05T07:00:01Z"}]
        }], 18: []})
        row = get_run_jobs(f, 17)
        self.assertEqual(row["seconds_job_to_first_step"], 0)
        self.assertEqual(row["invalid_step_intervals"], 1)

    def tearDown(self):
        auth_token.cache_clear()

    def test_auth_environment_token_preferred_without_subprocess(self):
        auth_token.cache_clear()
        with mock.patch.dict("os.environ", {"GH_TOKEN": "  environment-token  ",
                                            "GITHUB_TOKEN": "secondary"}, clear=True):
            with mock.patch("subprocess.run") as run:
                self.assertEqual(auth_token(), "environment-token")
                run.assert_not_called()

    def test_auth_authenticated_cli_fallback_is_cached(self):
        auth_token.cache_clear()
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("subprocess.run", return_value=mock.Mock(
                    stdout="  cli-access-token  ")) as run:
                self.assertEqual(auth_token(), "cli-access-token")
                self.assertEqual(auth_token(), "cli-access-token")
                run.assert_called_once()
                self.assertEqual(run.call_args.args[0],
                                 ["gh", "auth", "token"])
                self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_auth_missing_fails_before_any_api_request(self):
        auth_token.cache_clear()
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("subprocess.run", side_effect=FileNotFoundError):
                with mock.patch("urllib.request.urlopen") as urlopen:
                    with self.assertRaisesRegex(RuntimeError,
                                                "authentication required"):
                        api_get("/repos/gamesbyian/UR-Recomp/actions/runs/12")
                    urlopen.assert_not_called()

    def test_auth_cli_failure_must_not_publish_token_or_fallback(self):
        auth_token.cache_clear()
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("subprocess.run",
                            side_effect=subprocess.CalledProcessError(
                                1, ["gh", "auth", "token"], "secret")):
                with self.assertRaisesRegex(RuntimeError,
                                            "authentication required") as cm:
                    auth_token()
                self.assertNotIn("secret", str(cm.exception))

    def test_offset_and_fractional_github_timestamps(self):
        self.assertEqual(
            utc("2026-11-05T00:00:00.250-07:00"),
            utc("2026-11-05T07:00:00.250Z"),
        )
        f = MockAPI(jobs={
            17: [job(301, start="2026-11-05T00:00:00.000-07:00",
                     end="2026-11-05T07:01:00Z")],
            18: [],
        })
        self.assertEqual(get_run_jobs(f, 17)["seconds_inside_cancelled_run"], 60)
        for value in ("2026-11-05T07:00:00", "2026-11-05T07:00:00+07",
                      "nonsense", "2026-11-05T07:00:00.0000000Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                utc(value)

    def test_explicit_job_attempt_policy_in_all_calls(self):
        f = MockAPI()
        self.assertEqual(get_run_jobs(f, 17)["valid_started"], 2)
        self.assertTrue(all("filter=latest" in x for x in f.calls))
        f.calls.clear()
        self.assertEqual(get_run_jobs(f, 17, "all")["valid_started"], 2)
        self.assertTrue(all("filter=all" in x for x in f.calls))
        for policy in ("both", None, 1):
            with self.subTest(policy=policy), self.assertRaisesRegex(
                    ValueError, "attempt policy"):
                get_run_jobs(f, 17, policy)

    def test_all_attempts_census_is_not_mislabelled_as_latest(self):
        f = MockAPI()
        f.override = lambda route: (
            {"total_count": 3, "jobs": [
                job(101), job(102), job(103)
            ]} if "/actions/runs/17/jobs" in route and "filter=all" in route
            else None
        )
        latest = measure(f, START, END, workflows={"test": WORKFLOW},
                         workers=1, attempt_policy="latest")
        all_attempts = measure(f, START, END, workflows={"test": WORKFLOW},
                               workers=1, attempt_policy="all")
        self.assertEqual(latest["workflows"][0]["valid_started"], 2)
        self.assertEqual(all_attempts["workflows"][0]["valid_started"], 3)
        self.assertEqual(all_attempts["job_attempt_policy"], "all")
        self.assertIn("**all**", render_markdown(all_attempts))

    def test_cross_run_job_identity_mismatch_rejected(self):
        f = MockAPI(jobs={17: [{**job(301), "run_id": 18}]})
        with self.assertRaisesRegex(ValueError, "another workflow run"):
            get_run_jobs(f, 17)

    def test_cancelled_rerun_count_recorded_separately(self):
        f = MockAPI(runs=[{**run(17), "run_attempt": 2},
                          {**run(18), "run_attempt": 1}])
        row = measure(f, START, END, workflows={"test": WORKFLOW},
                      workers=1)["workflows"][0]
        self.assertEqual(row["cancelled_runs_with_reruns"], 1)

    def test_completion_without_start_is_invalid_not_silently_unstarted(self):
        f = MockAPI(jobs={17: [job(301, start=None)], 18: []})
        r = get_run_jobs(f, 17)
        self.assertEqual(r["valid_started"], 0)
        self.assertEqual(r["missing_starts"], 1)
        self.assertEqual(r["missing_completions"], 0)

    def test_steps_outside_job_boundaries_do_not_add_duration(self):
        f = MockAPI(jobs={17: [{
            **job(301),
            "steps": [
                {"conclusion": "success", "started_at": "2026-11-05T06:59:00Z",
                 "completed_at": "2026-11-05T07:00:10Z"},
                {"conclusion": "cancelled", "started_at": "2026-11-05T07:00:30Z",
                 "completed_at": "2026-11-05T07:01:30Z"},
            ],
        }]})
        r = get_run_jobs(f, 17)
        self.assertEqual(r["seconds_inside_cancelled_run"], 60)
        self.assertEqual(r["seconds_in_timed_steps"], 0)
        self.assertEqual(r["invalid_step_intervals"], 2)
        self.assertEqual(r["jobs_with_timed_steps"], 0)
        self.assertEqual(r["seconds_job_to_first_step"], 0)

    def test_overlapping_steps_are_not_double_counted(self):
        f = MockAPI(jobs={17: [{
            **job(301, end="2026-11-05T07:05:00Z"),
            "steps": [
                {"conclusion": "success", "started_at": "2026-11-05T07:00:00Z",
                 "completed_at": "2026-11-05T07:02:00Z"},
                {"conclusion": "success", "started_at": "2026-11-05T07:01:00Z",
                 "completed_at": "2026-11-05T07:03:00Z"},
                {"conclusion": "cancelled", "started_at": "2026-11-05T07:03:00Z",
                 "completed_at": "2026-11-05T07:04:00Z"},
            ],
        }]})
        r = get_run_jobs(f, 17)
        self.assertEqual(r["seconds_in_timed_steps"], 180)
        self.assertEqual(r["timed_steps"], 2)
        self.assertEqual(r["invalid_step_intervals"], 1)
        self.assertEqual(r["seconds_job_to_first_step"], 0)

    def test_one_sided_step_timestamp_is_explicit_invalid_evidence(self):
        f = MockAPI(jobs={17: [{
            **job(301),
            "steps": [{"conclusion": "cancelled",
                       "started_at": "2026-11-05T07:00:01Z",
                       "completed_at": None}],
        }]})
        r = get_run_jobs(f, 17)
        self.assertEqual(r["invalid_step_intervals"], 1)
        self.assertEqual(r["seconds_in_timed_steps"], 0)

    def test_source_attempt_or_head_change_during_jobs_refuses_complete_census(self):
        for field, value in (("run_attempt", 2), ("head_sha", "b" * 40),
                             ("conclusion", "success")):
            f = MockAPI()
            reads = [0]
            def override(path):
                if "status=cancelled" not in path:
                    return None
                reads[0] += 1
                if reads[0] == 2:
                    rows = copy.deepcopy(f.runs)
                    rows[0][field] = value
                    return {"total_count": len(rows), "workflow_runs": rows}
                return None
            f.override = override
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "source cohort changed|wrong workflow or run conclusion"):
                measure(f, START, END, workflows={"test": WORKFLOW}, workers=1)

    def test_missing_source_provenance_is_rejected(self):
        for missing in ("head_sha", "run_attempt", "status"):
            row = run(17)
            del row[missing]
            with self.subTest(field=missing), self.assertRaisesRegex(
                    ValueError, "source/attempt metadata"):
                get_run_census(MockAPI(runs=[row]), WORKFLOW,
                               span(START, END))

    def test_missing_completion_excluded(self):
        f = MockAPI(jobs={17: [job(1, end=None),
                              job(2, start=None)], 18: []})
        row = measure(f, START, END, workflows={"test": WORKFLOW},
                      workers=1)["workflows"][0]
        self.assertEqual(row["missing_completions"], 1)
        self.assertEqual(row["valid_started"], 0)

    def test_cancelled_pagination_across_100(self):
        f = MockAPI(runs=[run(i) for i in range(1, 122)])
        total, rows = get_run_census(f, WORKFLOW, span(START, END))
        self.assertEqual((total, len(rows)), (121, 121))
        self.assertTrue(any("page=2" in x for x in f.calls))

    def test_job_pagination_across_100(self):
        f = MockAPI(jobs={17: [job(i) for i in range(1, 123)]})
        row = get_run_jobs(f, 17)
        self.assertEqual(row["valid_started"], 122)
        self.assertEqual(row["seconds_inside_cancelled_run"], 7320)

    def test_duplicate_run_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            get_run_census(MockAPI(runs=[run(1), run(1)]),
                           WORKFLOW, span(START, END))

    def test_mismatched_workflow_and_status_rejected(self):
        for row in (run(1, status="success"),
                    {**run(1), "workflow_id": 999}):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "wrong"):
                get_run_census(MockAPI(runs=[row]), WORKFLOW, span(START, END))

    def test_outside_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            get_run_census(MockAPI(runs=[run(1, created="2026-10-29T08:14:04Z")]),
                           WORKFLOW, span(START, END))

    def test_cancelled_page_cap_rejected(self):
        f = MockAPI()
        f.override = lambda p: {"total_count": 1001, "workflow_runs": []} if "status=cancelled" in p else None
        with self.assertRaisesRegex(ValueError, "exceeds"):
            get_run_census(f, WORKFLOW, span(START, END))

    def test_incomplete_run_page_rejected(self):
        f = MockAPI(runs=[run(i) for i in range(1, 102)])
        f.override = lambda p: {"total_count": 101, "workflow_runs": [run(1)]} if "status=cancelled" in p else None
        with self.assertRaisesRegex(ValueError, "incomplete"):
            get_run_census(f, WORKFLOW, span(START, END))

    def test_run_population_change_rejected(self):
        f = MockAPI(runs=[run(i) for i in range(1, 102)])
        f.override = lambda p: {"total_count": 102, "workflow_runs": [run(101)]} if ("status=cancelled" in p and "page=2" in p) else None
        with self.assertRaisesRegex(ValueError, "moved during"):
            get_run_census(f, WORKFLOW, span(START, END))

    def test_incomplete_job_page_rejected(self):
        f = MockAPI(jobs={17: [job(i) for i in range(1, 103)]})
        f.override = lambda p: {"total_count": 102, "jobs": []} if "/jobs" in p else None
        with self.assertRaisesRegex(ValueError, "incomplete"):
            get_run_jobs(f, 17)

    def test_duplicate_job_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            get_run_jobs(MockAPI(jobs={17: [job(1), job(1)]}), 17)

    def test_empty_population(self):
        row = measure(MockAPI(runs=[], jobs={}), START, END,
                      workflows={"test": WORKFLOW}, workers=1)["workflows"][0]
        self.assertEqual(row["cancelled_runs"], 0)
        self.assertEqual(row["seconds_inside_cancelled_run"], 0)

    def test_worker_bound(self):
        with self.assertRaisesRegex(ValueError, "workers"):
            measure(MockAPI(), START, END,
                    workflows={"test": WORKFLOW}, workers=9)

    def test_missing_api_run_count_rejected(self):
        f = MockAPI()
        f.override = lambda p: {"workflow_runs": []} if "status=cancelled" not in p else None
        with self.assertRaisesRegex(ValueError, "invalid count"):
            get_run_census(f, WORKFLOW, span(START, END))


if __name__ == "__main__":
    unittest.main()

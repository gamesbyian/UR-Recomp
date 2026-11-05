"""No-network negative controls for read-only cancelled Actions timing census."""
from __future__ import annotations

import copy
import unittest
from urllib.parse import parse_qs, urlsplit

from tools.ci_cancelled_runner_census import (measure, span, get_run_census,
                                              get_run_jobs, render_markdown)

START = "2026-10-29T08:14:05Z"
END = "2026-11-05T08:14:05Z"
WORKFLOW = 123


def run(rid, status="cancelled", created=START):
    return {"id": rid, "workflow_id": WORKFLOW,
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
        self.assertIn("not billable", report["limitations"])

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

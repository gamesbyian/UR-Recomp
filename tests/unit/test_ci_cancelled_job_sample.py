"""Real GitHub job timing, not cancellation-count-as-cost arithmetic."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from ci_cancelled_job_sample import sample_cancelled_jobs


def make_job(start, end):
    return {"started_at": start, "completed_at": end, "conclusion": "cancelled"}


class CancelledRunnerSampleTests(unittest.TestCase):
    def test_concurrent_jobs_sum_runner_occupancy_not_wall_span(self):
        runs = [
            {"id": 1, "name": "Bridge", "conclusion": "cancelled"},
            {"id": 2, "name": "Bridge", "conclusion": "cancelled"},
            {"id": 3, "name": "Unit", "conclusion": "success"},
        ]
        def read(path):
            if "/runs/1/jobs" in path:
                return {"total_count": 2, "jobs": [
                    make_job("2026-10-21T08:00:00Z", "2026-10-21T08:00:10Z"),
                    make_job("2026-10-21T08:00:00Z", "2026-10-21T08:00:15Z"),
                ]}
            if "/runs/2/jobs" in path:
                return {"total_count": 1, "jobs": [
                    {"started_at": None, "completed_at": None, "conclusion": "cancelled"}
                ]}
            raise AssertionError("should not fetch successful run")
        s = sample_cancelled_jobs(read, "/repos/gamesbyian/UR-Recomp", runs)
        self.assertEqual(s["selected"], 2)
        self.assertEqual(s["verified_job_censuses"], 2)
        self.assertEqual(s["observed_runner_seconds"], 25.0)
        self.assertEqual(s["workflows"][0]["zero_started_jobs"], 1)
        self.assertTrue(s["not_billable_minutes"])
        self.assertTrue(s["not_evidence_of_waste"])

    def test_pagination_does_not_undercount_as_complete(self):
        runs = [{"id": 9, "name": "Bridge", "conclusion": "cancelled"}]
        s = sample_cancelled_jobs(
            lambda path: {"jobs": [make_job("2026-10-21T08:00:00Z",
                                           "2026-10-21T08:01:00Z")],
                          "total_count": 101},
            "/repos/gamesbyian/UR-Recomp", runs,
        )
        self.assertEqual(s["verified_job_censuses"], 0)
        self.assertEqual(s["observed_runner_seconds"], 0)
        self.assertEqual(len(s["unknown_censuses"]), 1)
        self.assertIn("not complete", s["unknown_censuses"][0]["reason"])

    def test_failed_api_fetch_is_unknown_not_free(self):
        def denied(path):
            raise ValueError("HTTP 403")
        s = sample_cancelled_jobs(denied, "/repos/gamesbyian/UR-Recomp",
                                  [{"id": 12, "conclusion": "cancelled"}])
        self.assertEqual(s["unknown_censuses"][0]["reason"], "HTTP 403")
        self.assertEqual(s["verified_job_censuses"], 0)

    def test_latest_eight_bound_no_more_than_eight_queries(self):
        fetched = []
        rows = [{"id": n, "name": "Unit", "conclusion": "cancelled"}
                for n in range(1, 19)]
        def read(path):
            fetched.append(path)
            return {"total_count": 0, "jobs": []}
        s = sample_cancelled_jobs(read, "/repos/gamesbyian/UR-Recomp", rows)
        self.assertEqual(len(fetched), 8)
        self.assertEqual(s["selected"], 8)
        self.assertEqual(s["unselected_cancelled_runs"], 10)
        self.assertEqual(s["verified_job_censuses"], 8)

    def test_invalid_dates_do_not_inflate_occupancy(self):
        rows = [{"id": 1, "name": "One", "conclusion": "cancelled"}]
        s = sample_cancelled_jobs(
            lambda path: {"jobs": [
                make_job("2026-10-21T08:02:00Z", "2026-10-21T08:00:00Z"),
                {"started_at": None, "completed_at": None},
            ], "total_count": 2},
            "/repos/gamesbyian/UR-Recomp", rows,
        )
        self.assertEqual(s["observed_runner_seconds"], 0)

    def test_bad_limits_and_missing_ids_fail_closed(self):
        for limit in (0, 21, -1, 1.5, "8"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                sample_cancelled_jobs(lambda path: {}, "/repos/a/b", [], limit=limit)
        s = sample_cancelled_jobs(lambda path: {}, "/repos/a/b",
                                  [{"name": "Unknown", "conclusion": "cancelled"}])
        self.assertEqual(s["verified_job_censuses"], 0)
        self.assertEqual(s["unknown_censuses"][0]["reason"], "missing run ID")


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timezone

from tools.report_ci_runtime import summarize, markdown, job_parallelism_profile


class CiRuntimeReportTest(unittest.TestCase):
    def test_groups_and_sorts_by_total_runtime(self):
        payload = {"workflow_runs": [
            {"id": 1, "name":"A","status":"completed","conclusion":"success","created_at":"2026-10-03T00:00:00Z","run_started_at":"2026-10-03T00:00:00Z","updated_at":"2026-10-03T00:10:00Z"},
            {"id": 2, "name":"B","status":"completed","conclusion":"cancelled","created_at":"2026-10-03T01:00:00Z","run_started_at":"2026-10-03T01:00:00Z","updated_at":"2026-10-03T01:05:00Z"},
            {"id": 3, "name":"A","status":"completed","conclusion":"failure","created_at":"2026-10-03T02:00:00Z","run_started_at":"2026-10-03T02:00:00Z","updated_at":"2026-10-03T02:20:00Z"}
        ]}
        report = summarize(payload, 72, datetime(2026,10,4,tzinfo=timezone.utc))
        self.assertEqual(report["workflows"][0]["workflow"], "A")
        self.assertEqual(report["workflows"][0]["total_wall_seconds"], 1800)
        self.assertEqual(report["workflows"][1]["cancelled_runs"], 1)
        self.assertEqual(report["workflows"][1]["cancelled_wall_seconds"], 300)

    def test_pending_runs_do_not_pollute_completed_wall_average(self):
        payload = {"workflow_runs": [
            {"id": 11, "name": "Gate", "status": "completed", "conclusion": "success",
             "created_at": "2026-10-03T00:00:00Z",
             "run_started_at": "2026-10-03T00:00:00Z",
             "updated_at": "2026-10-03T00:10:00Z"},
            {"id": 12, "name": "Gate", "status": "in_progress", "conclusion": None,
             "created_at": "2026-10-03T01:00:00Z",
             "run_started_at": "2026-10-03T01:00:00Z",
             "updated_at": "2026-10-03T01:01:00Z"},
            {"id": 13, "name": "Gate", "status": "queued", "conclusion": None,
             "created_at": "2026-10-03T02:00:00Z",
             "run_started_at": None,
             "updated_at": "2026-10-03T02:01:00Z"},
        ]}
        report = summarize(payload, 72, datetime(2026,10,4,tzinfo=timezone.utc))
        row = report["workflows"][0]
        self.assertEqual(row["runs"], 3)
        self.assertEqual(row["completed_runs"], 1)
        self.assertEqual(row["total_wall_seconds"], 600)
        self.assertEqual(row["avg_wall_seconds"], 600)
        self.assertEqual(row["max_wall_seconds"], 600)

    def test_reports_queue_and_step_buckets(self):
        payload = {"workflow_runs": [{
            "id": 42,
            "name": "Native gate",
            "status": "completed",
            "conclusion": "cancelled",
            "created_at": "2026-10-03T00:00:00Z",
            "run_started_at": "2026-10-03T00:01:00Z",
            "updated_at": "2026-10-03T00:11:00Z",
        }]}
        jobs = {"runs": [{
            "run_id": 42,
            "jobs": [{
                "created_at": "2026-10-03T00:00:30Z",
                "started_at": "2026-10-03T00:02:00Z",
                "completed_at": "2026-10-03T00:10:00Z",
                "steps": [
                    {"name": "Install desktop build dependencies", "started_at": "2026-10-03T00:02:00Z", "completed_at": "2026-10-03T00:03:00Z"},
                    {"name": "Build native candidate", "started_at": "2026-10-03T00:03:00Z", "completed_at": "2026-10-03T00:05:00Z"},
                    {"name": "Prove deterministic route acceptance", "started_at": "2026-10-03T00:05:00Z", "completed_at": "2026-10-03T00:09:00Z"},
                ],
            }],
        }]}
        report = summarize(
            payload,
            72,
            datetime(2026,10,4,tzinfo=timezone.utc),
            jobs_payload=jobs,
        )
        row = report["workflows"][0]
        self.assertEqual(row["run_queue_seconds"], 60)
        self.assertEqual(row["job_queue_seconds"], 90)
        self.assertEqual(row["dependency_seconds"], 60)
        self.assertEqual(row["build_seconds"], 120)
        self.assertEqual(row["execution_seconds"], 240)
        self.assertEqual(row["cancelled_wall_seconds"], 600)
        self.assertEqual(row["top_steps"][0]["step"], "Prove deterministic route acceptance")


    def test_observed_parallelism_is_measured_from_intervals(self):
        jobs = [
            {"started_at": "2026-10-03T00:00:00Z", "completed_at": "2026-10-03T00:02:00Z"},
            {"started_at": "2026-10-03T00:01:00Z", "completed_at": "2026-10-03T00:03:00Z"},
            {"started_at": "2026-10-03T00:03:00Z", "completed_at": "2026-10-03T00:04:00Z"},
            {"started_at": "2026-10-03T00:01:00Z", "completed_at": "2026-10-03T00:01:00Z"},
            {"started_at": None, "completed_at": None},
        ]
        profile = job_parallelism_profile(jobs)
        self.assertEqual(profile["runner_seconds"], 300)
        self.assertEqual(profile["observed_span_seconds"], 240)
        self.assertEqual(profile["peak_active_jobs"], 2)
        self.assertIsNone(job_parallelism_profile(jobs[-2:]))

        payload = {"workflow_runs": [{
            "id": 4, "name": "Modern", "status": "completed",
            "conclusion": "success", "created_at": "2026-10-03T00:00:00Z",
            "run_started_at": "2026-10-03T00:00:00Z",
            "updated_at": "2026-10-03T00:05:00Z",
        }]}
        report = summarize(payload, 72, datetime(2026, 10, 4, tzinfo=timezone.utc),
                           jobs_payload={"runs": [{"run_id": 4, "jobs": jobs}]})
        row = report["workflows"][0]
        self.assertEqual(row["runs_with_job_timing"], 1)
        self.assertEqual(row["peak_active_jobs"], 2)
        self.assertEqual(row["runner_seconds"], 300)
        self.assertEqual(row["observed_job_span_seconds"], 240)
        self.assertEqual(row["mean_active_jobs"], 1.25)
        self.assertIn("| Modern | 1 | 5.0 | 4.0 | 1.25 | 2 |", markdown(report))

    def test_parallel_metrics_fail_closed_on_missing_job_timestamps(self):
        payload = {"workflow_runs": [{
            "id": 5, "name": "Empty", "status": "completed",
            "conclusion": "success", "created_at": "2026-10-03T00:00:00Z",
            "run_started_at": "2026-10-03T00:00:00Z",
            "updated_at": "2026-10-03T00:01:00Z",
        }]}
        report = summarize(payload, 72, datetime(2026, 10, 4, tzinfo=timezone.utc),
                           jobs_payload={"runs": [{"run_id": 5, "jobs": [{
                               "started_at": "2026-10-03T00:02:00Z",
                               "completed_at": None,
                           }]}]})
        row = report["workflows"][0]
        self.assertEqual(row["runs_with_job_timing"], 0)
        self.assertEqual(row["runner_seconds"], 0)
        self.assertEqual(row["mean_active_jobs"], 0)
        self.assertEqual(row["peak_active_jobs"], 0)


if __name__ == "__main__":
    unittest.main()

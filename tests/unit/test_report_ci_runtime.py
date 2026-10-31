import unittest
from datetime import datetime, timezone

from tools.report_ci_runtime import summarize, markdown, job_parallelism_profile, step_bucket


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

    def test_wall_percentiles_exclude_completed_runs_without_valid_timing(self):
        runs = [
            {"id": 1, "name": "Gate", "status": "completed",
             "created_at": "2026-10-20T10:00:00Z",
             "run_started_at": "2026-10-20T10:00:00Z",
             "updated_at": "2026-10-20T10:02:00Z"},
            {"id": 2, "name": "Gate", "status": "completed",
             "created_at": "2026-10-20T10:00:00Z",
             "run_started_at": "2026-10-20T10:00:00Z",
             "updated_at": "2026-10-20T10:05:00Z"},
            {"id": 3, "name": "Gate", "status": "completed",
             "created_at": "2026-10-20T10:00:00Z",
             "run_started_at": "2026-10-20T10:00:00Z",
             "updated_at": None},
            {"id": 4, "name": "Gate", "status": "in_progress",
             "created_at": "2026-10-20T10:00:00Z",
             "run_started_at": "2026-10-20T10:00:00Z",
             "updated_at": "2026-10-20T10:01:00Z"},
            {"id": 5, "name": "Empty", "status": "completed",
             "created_at": "2026-10-20T10:00:00Z",
             "run_started_at": "2026-10-20T10:03:00Z",
             "updated_at": "2026-10-20T10:02:00Z"},
        ]
        result = summarize({"workflow_runs": runs}, 72,
                           datetime(2026, 10, 21, tzinfo=timezone.utc))
        by_name = {x["workflow"]: x for x in result["workflows"]}
        gate = by_name["Gate"]
        self.assertEqual(gate["completed_runs"], 3)
        self.assertEqual(gate["timed_completed_runs"], 2)
        self.assertEqual(gate["completed_runs_missing_wall_timing"], 1)
        self.assertEqual(gate["total_wall_seconds"], 420)
        self.assertEqual(gate["avg_wall_seconds"], 210)
        self.assertEqual(gate["p50_wall_seconds"], 210)
        self.assertEqual(gate["p90_wall_seconds"], 300)
        self.assertIsNone(by_name["Empty"]["avg_wall_seconds"])
        self.assertIsNone(by_name["Empty"]["p50_wall_seconds"])
        self.assertIsNone(by_name["Empty"]["p90_wall_seconds"])
        report = markdown(result)
        self.assertIn("p50 min", report)
        self.assertIn("p90 min", report)
        self.assertIn("unknown", report)

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

    def test_hosted_sdl3_cache_preparation_is_measured_as_dependency(self):
        # A ~110-second static SDL3 preparation step previously disappeared
        # into the "other" bucket of the cost/critical-path report. Measure
        # restore and save overhead with the same dependency boundary.
        for step in (
            "Restore hosted Windows verified SDL3 candidate",
            "Prepare source-pinned static SDL3 cache (HP and hosted canary)",
            "Save hosted Windows verified SDL3 candidate",
        ):
            with self.subTest(step=step):
                self.assertEqual(step_bucket(step), "dependency")
        self.assertEqual(step_bucket("Configure and build (Visual Studio, ClangCL, SDL3)"),
                         "build")
        self.assertEqual(step_bucket("QA-05 packaged Windows Restart audio witness"),
                         "other")
        self.assertEqual(step_bucket("Prove deterministic route acceptance"),
                         "execution")
        self.assertEqual(step_bucket("Unrelated housekeeping"), "other")

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


    def test_skipped_matrix_job_with_github_synthetic_timestamps_is_not_runner_time(self):
        jobs = [
            {"id": 101, "conclusion": "success",
             "started_at": "2026-10-26T19:19:54Z",
             "completed_at": "2026-10-26T19:20:38Z"},
            {"id": 102, "conclusion": "skipped",
             "started_at": "2026-10-26T19:19:52Z",
             "completed_at": "2026-10-26T19:19:51Z"},
            {"id": 103, "conclusion": "skipped",
             "started_at": "2026-10-26T19:19:52Z",
             "completed_at": "2026-10-26T19:20:38Z"},
        ]
        profile = job_parallelism_profile(jobs)
        self.assertEqual(profile["runner_seconds"], 44)
        self.assertEqual(profile["peak_active_jobs"], 1)
        self.assertIsNone(job_parallelism_profile(jobs[1:]))

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
        self.assertIn("| Modern | 1 | 0 | 5.0 | 0.0 | 0.0 | 4.0 | 1.25 | 2 |", markdown(report))

    def test_sample_coverage_and_cancelled_runner_cost_are_explicit(self):
        now = datetime(2026, 10, 4, tzinfo=timezone.utc)
        payload = {"total_count": 500, "workflow_runs": [
            {"id": 61, "name": "Trial", "event": "pull_request",
             "status": "completed", "conclusion": "cancelled",
             "created_at": "2026-10-03T00:00:00Z",
             "run_started_at": "2026-10-03T00:00:00Z",
             "updated_at": "2026-10-03T00:10:00Z"},
        ]}
        jobs = {"runs": [{"run_id": 61, "jobs": [{
            "started_at": "2026-10-03T00:02:00Z",
            "completed_at": "2026-10-03T00:03:00Z",
        }]}]}
        report = summarize(payload, 72, now, jobs)
        row = report["workflows"][0]
        self.assertFalse(report["window_census_complete"])
        self.assertEqual(report["source_total_available"], 500)
        self.assertEqual(report["source_runs_fetched"], 1)
        self.assertEqual(row["cancelled_wall_seconds"], 600)
        self.assertEqual(row["cancelled_runner_seconds"], 60)
        self.assertEqual(row["failed_runner_seconds"], 0)
        self.assertEqual(row["events"], {"pull_request": 1})
        self.assertIn("NO (sample only", markdown(report))
        self.assertTrue(summarize(payload, 24, now, jobs)["window_census_complete"])
        payload["total_count"] = 1
        self.assertTrue(summarize(payload, 72, now, jobs)["window_census_complete"])

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
        self.assertEqual(row["runs_missing_job_timing"], 1)
        self.assertIn("lower bounds", markdown(report))
        self.assertEqual(row["runner_seconds"], 0)
        self.assertEqual(row["mean_active_jobs"], 0)
        self.assertEqual(row["peak_active_jobs"], 0)


    def test_detects_close_same_source_cross_workflow_builds_only(self):
        source = "a" * 40
        other = "b" * 40
        def run(ident, name, sha, start, event="pull_request"):
            return {"id": ident, "name": name, "head_sha": sha,
                    "status": "completed", "conclusion": "success", "event": event,
                    "created_at": start, "run_started_at": start,
                    "updated_at": "2026-10-26T01:30:00Z"}
        runs = {"workflow_runs": [
            run(1, "Windows smoke", source, "2026-10-26T01:00:00Z"),
            run(2, "QA-05/09 wrapper", source, "2026-10-26T01:00:20Z"),
            run(3, "Unrelated branch", other, "2026-10-26T01:00:00Z"),
            run(4, "Missing timed build", source, "2026-10-26T01:02:00Z"),
        ]}
        def job(ident, seconds, name="Build source"):
            return {"run_id": ident, "jobs": [{"steps": [{
                "name": name, "started_at": "2026-10-26T01:01:00Z",
                "completed_at": f"2026-10-26T01:{seconds:02d}:00Z",
            }]}]}
        jobs = {"runs": [job(1, 10), job(2, 8), job(3, 9),
                         job(4, 8, "Print summary")]}
        report = summarize(runs, 72, datetime(2026, 10, 27, tzinfo=timezone.utc),
                           jobs_payload=jobs)
        candidates = report["possible_same_source_cross_workflow_builds"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["head_sha"], source)
        self.assertEqual(candidates[0]["run_ids"], [1, 2])
        self.assertEqual(candidates[0]["runs_observed"], 2)
        self.assertEqual(candidates[0]["timed_build_steps"], 2)
        self.assertIn("manual review only", markdown(report))
        # A build-like label and a shared SHA only flag a possible duplicate,
        # not PE/ZIP equality or removable release coverage.
        self.assertIn("identity_and_coverage_unverified",
                      candidates[0]["status"])

    def test_distant_or_missing_build_times_do_not_create_false_match(self):
        sha = "c" * 40
        payload = {"workflow_runs": [
            {"id": 1, "name": "A", "head_sha": sha, "status": "completed",
             "created_at": "2026-10-25T00:00:00Z", "event": "push"},
            {"id": 2, "name": "B", "head_sha": sha, "status": "completed",
             "created_at": "2026-10-26T00:00:00Z", "event": "push"},
        ]}
        jobs = {"runs": [
            {"run_id": i, "jobs": [{"steps": [{
                "name": "Build native", "started_at": start,
                "completed_at": finish,
            }]}]} for i, start, finish in [
                (1, "2026-10-25T00:00:00Z", "2026-10-25T00:01:00Z"),
                (2, "2026-10-26T00:00:00Z", "2026-10-26T00:01:00Z"),
            ]
        ]}
        report = summarize(payload, 72, datetime(2026, 10, 27, tzinfo=timezone.utc),
                           jobs_payload=jobs)
        self.assertEqual(report["possible_same_source_cross_workflow_builds"], [])
        self.assertEqual(summarize(payload, 72, datetime(2026, 10, 27, tzinfo=timezone.utc))
                         ["possible_same_source_cross_workflow_builds"], [])


if __name__ == "__main__":
    unittest.main()

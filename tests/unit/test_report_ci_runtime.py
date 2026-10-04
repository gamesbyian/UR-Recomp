import unittest
from datetime import datetime, timezone
from tools.report_ci_runtime import summarize

class CiRuntimeReportTest(unittest.TestCase):
    def test_groups_and_sorts_by_total_runtime(self):
        payload = {"workflow_runs": [
            {"name":"A","status":"completed","conclusion":"success","created_at":"2026-10-03T00:00:00Z","run_started_at":"2026-10-03T00:00:00Z","updated_at":"2026-10-03T00:10:00Z"},
            {"name":"B","status":"completed","conclusion":"cancelled","created_at":"2026-10-03T01:00:00Z","run_started_at":"2026-10-03T01:00:00Z","updated_at":"2026-10-03T01:05:00Z"},
            {"name":"A","status":"completed","conclusion":"failure","created_at":"2026-10-03T02:00:00Z","run_started_at":"2026-10-03T02:00:00Z","updated_at":"2026-10-03T02:20:00Z"}
        ]}
        report = summarize(payload, 72, datetime(2026,10,4,tzinfo=timezone.utc))
        self.assertEqual(report["workflows"][0]["workflow"], "A")
        self.assertEqual(report["workflows"][0]["total_wall_seconds"], 1800)
        self.assertEqual(report["workflows"][1]["cancelled_runs"], 1)

if __name__ == "__main__":
    unittest.main()

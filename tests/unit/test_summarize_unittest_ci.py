import tempfile
from pathlib import Path
import unittest
from tools.summarize_unittest_ci import summarize, markdown


class SummarizeUnittestCiTests(unittest.TestCase):
    def test_success_and_failure_remain_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unit-shard-count.txt").write_text("2\n")
            (root / "unit-shard-exits.txt").write_text("shard0=0\nshard1=1\n")
            (root / "unit-shard0.log").write_text(
                "test_one ... ok\n\nRan 1 test in 0.02s\n\nOK\n")
            (root / "unit-shard1.log").write_text(
                "FAIL: test_two (unit.X)\n\nRan 2 tests in 0.25s\n\nFAILED (failures=1)\n")
            report = summarize(root, {"GITHUB_SHA": "abcd"})
            self.assertEqual(report["outcome"], "fail")
            self.assertEqual(report["total_tests_observed"], 3)
            self.assertEqual([r["outcome"] for r in report["shards"]], ["pass", "fail"])
            self.assertIn("test_two", markdown(report))
            self.assertEqual(report["source"]["GITHUB_SHA"], "abcd")

    def test_manifest_requires_all_intended_workers_even_if_no_log_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unit-shard-count.txt").write_text("4\n")
            (root / "unit-shard-exits.txt").write_text("shard0=0\nshard1=0\n")
            for i in (0, 1):
                (root / f"unit-shard{i}.log").write_text(
                    "Ran 5 tests in 0.1s\n\nOK\n")
            result = summarize(root, {})
            self.assertEqual(result["outcome"], "incomplete")
            self.assertEqual(result["expected_shards"], 4)
            self.assertEqual(result["missing_evidence"], ["shard2", "shard3"])

    def test_missing_or_invalid_manifest_never_reports_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unit-shard-exits.txt").write_text("shard0=0\nshard1=0\n")
            for i in (0, 1):
                (root / f"unit-shard{i}.log").write_text(
                    "Ran 1 test in 0.1s\n\nOK\n")
            self.assertEqual(summarize(root, {})["outcome"], "incomplete")
            self.assertIn("shard_manifest", summarize(root, {})["missing_evidence"])
            (root / "unit-shard-count.txt").write_text("100\n")
            self.assertEqual(summarize(root, {})["outcome"], "incomplete")

    def test_missing_or_truncated_logs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unit-shard-exits.txt").write_text("shard0=0\nshard1=1\n")
            (root / "unit-shard0.log").write_text("partial data\n")
            report = summarize(root, {})
            self.assertEqual(report["outcome"], "incomplete")
            self.assertEqual(report["shards"][0]["outcome"], "harness_error")
            self.assertEqual(report["shards"][1]["outcome"], "not_run")
            self.assertEqual(report["missing_evidence"], ["shard0", "shard1"])

    def test_success_log_without_exit_receipt_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unit-shard0.log").write_text("Ran 4 tests in 0.1s\n\nOK\n")
            report = summarize(root, {})
            self.assertEqual(report["shards"][0]["outcome"], "incomplete")
            self.assertNotEqual(report["outcome"], "pass")

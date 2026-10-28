"""Only a complete successful same-source module census may rebalance tests."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.rebalance_unit_test_timings import SCHEMA, calibrate

SHA = "a" * 40


class RebalanceUnitTestTimingsTests(unittest.TestCase):
    def fixture(self, root: Path):
        tests = root / "unit"
        tests.mkdir()
        for n in ("alpha", "beta", "gamma", "delta"):
            (tests / f"test_{n}.py").write_text("pass\n")
        timing = root / "runs"
        timing.mkdir()
        shards = [
            {"tests.unit.test_alpha": 3.2, "tests.unit.test_beta": 0.0},
            {"tests.unit.test_gamma": 5.1, "tests.unit.test_delta": 2.4},
        ]
        for i, times in enumerate(shards):
            payload = {
                "schema": SCHEMA, "diagnostic_only": True,
                "full_test_suite_passed": True,
                "pr_or_test_merge_sha": SHA,
                "observed_modules": len(times),
                "module_timings_seconds": times,
            }
            (timing / f"unit-module-timings-shard{i}.json").write_text(
                json.dumps(payload))
        return tests, timing

    def test_complete_pinned_same_sha_times_qualify(self):
        with tempfile.TemporaryDirectory() as path:
            tests, timing = self.fixture(Path(path))
            out = calibrate(timing, tests, SHA, 2)
            self.assertEqual(len(out), 4)
            self.assertEqual(out["tests.unit.test_alpha"], 3.2)
            self.assertEqual(list(out), sorted(out))

    def test_missing_bad_sha_failure_duplicate_and_unknown_fail_closed(self):
        with tempfile.TemporaryDirectory() as path:
            tests, timing = self.fixture(Path(path))
            first = timing / "unit-module-timings-shard0.json"
            second = timing / "unit-module-timings-shard1.json"
            p = json.loads(first.read_text())
            q = json.loads(second.read_text())
            for edit in (
                lambda x: x.update(full_test_suite_passed=False),
                lambda x: x.update(pr_or_test_merge_sha="b" * 40),
                lambda x: x.update(observed_modules=1),
                lambda x: x["module_timings_seconds"].update(
                    {"tests.unit.test_unknown": 2.2}),
                lambda x: x["module_timings_seconds"].update(
                    {"tests.unit.test_alpha": -1}),
                lambda x: x["module_timings_seconds"].update(
                    {"tests.unit.test_beta": True}),
            ):
                with self.subTest(edit=repr(edit)):
                    broken = json.loads(json.dumps(p))
                    edit(broken)
                    first.write_text(json.dumps(broken))
                    with self.assertRaises(ValueError):
                        calibrate(timing, tests, SHA, 2)
            first.write_text(json.dumps(p))
            duplicate = json.loads(json.dumps(q))
            duplicate["module_timings_seconds"]["tests.unit.test_alpha"] = 0.4
            duplicate["observed_modules"] += 1
            second.write_text(json.dumps(duplicate))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                calibrate(timing, tests, SHA, 2)
            second.write_text(json.dumps(q))
            first.unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                calibrate(timing, tests, SHA, 2)

    def test_wrong_source_count_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            tests, timing = self.fixture(root)
            for sh in ("not-a-sha", "b" * 40):
                with self.subTest(sha=sh), self.assertRaises(ValueError):
                    calibrate(timing, tests, sh, 2)
            with self.assertRaisesRegex(ValueError, "missing"):
                calibrate(timing, tests, SHA, 3)
            target = timing / "unit-module-timings-shard0.json"
            original = target.read_text()
            target.unlink()
            target.symlink_to(timing / "unit-module-timings-shard1.json")
            with self.assertRaisesRegex(ValueError, "redirected"):
                calibrate(timing, tests, SHA, 2)
            target.unlink()
            target.write_text(original)


if __name__ == "__main__":
    unittest.main()

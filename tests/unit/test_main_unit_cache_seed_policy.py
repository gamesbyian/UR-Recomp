"""Fail-closed policy for trusted-main reusable Linux unit C++ cache seed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github/workflows/tooling-unit-tests.yml"
TRIGGERS = ROOT / "tests/unit/test_ci_trigger_policy.py"
CACHE = ROOT / "tools/ci_compile_cache.py"
FULL = ROOT / "tools/ci_select_unit_suite.py"


class MainUnitCacheSeedPolicyTests(unittest.TestCase):
    def test_single_daily_main_schedule_with_exact_trust_guard(self):
        text = WF.read_text(encoding="utf-8")
        before_jobs = text.split("\njobs:\n", 1)[0]
        self.assertIn("  schedule:\n    - cron: '43 6 * * *'", before_jobs)
        self.assertEqual(before_jobs.count("- cron:"), 1)
        self.assertNotIn("\n  push:", before_jobs)
        self.assertIn("  pull_request:", before_jobs)
        self.assertIn("  workflow_dispatch:", before_jobs)
        unit = text.split("\n  unit:\n", 1)[1].split("\n  draft-syntax:\n", 1)[0]
        unit_header = unit.split("\n    steps:\n", 1)[0]
        # Keep the preexisting PR contract verbatim for independent guards.
        self.assertIn("if: github.event_name != 'pull_request' || github.event.pull_request.draft == false", unit_header)
        self.assertIn("runs-on: ubuntu-latest", unit_header)
        self.assertNotIn("runs-on: self-hosted", unit_header)
        guard = unit.split("      - name: Require trusted main for scheduled Linux cache seed\n", 1)[1].split(
            "      - uses: actions/checkout@v4", 1)[0]
        for marker in (
            "if: github.event_name == 'schedule'",
            'test "$GITHUB_REPOSITORY" = "gamesbyian/UR-Recomp"',
            'test "$GITHUB_REF" = "refs/heads/main"',
            'test "$GITHUB_EVENT_NAME" = "schedule"',
            "set -euo pipefail",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, guard)
        # No automatic post-merge push duplicate CI gate.
        self.assertIn("test_pr_validation_is_not_repeated_after_merge", TRIGGERS.read_text())

    def test_daily_seed_runs_same_complete_suite_without_relaxing_any_tests(self):
        text = WF.read_text(encoding="utf-8")
        self.assertIn("steps.unit-scope.outputs.mode != 'ops'", text)
        self.assertIn("Run full dependency-free Python unit tests in timing-balanced shards", text)
        self.assertIn("python3 tools/run_unit_shard.py", text)
        self.assertIn("test \"$rc\" -eq 0", text)
        self.assertIn("Compute reviewable timing weights from all successful measured shards", text)
        self.assertIn("ci-tooling-unit-result", text)
        # No PR number in a daily schedule => full, even if API is unavailable.
        self.assertIn('return "full"', FULL.read_text())
        self.assertIn("cache-hit != 'true'", text)

    def test_schedule_publishes_only_after_successful_full_run(self):
        text = WF.read_text(encoding="utf-8")
        save = text.split("      - name: Save compile cache\n", 1)[1]
        self.assertIn("(github.event_name != 'schedule' || success())", save)
        self.assertIn("steps.unit-scope.outputs.mode != 'ops'", save)
        self.assertIn("actions/cache/save@v4", save)
        self.assertIn("ur-unit-cxx-${{ runner.os }}-${{ github.run_id }}", save)
        restore = text.split("      - name: Restore compile cache\n", 1)[1].split(
            "      - name: Enable content-addressed compile cache", 1)[0]
        self.assertIn("actions/cache/restore@v4", restore)
        self.assertIn("ur-unit-cxx-${{ runner.os }}-", restore)
        self.assertIn("runner.temp", restore)
        self.assertNotIn("reference/roms", restore)

    def test_cache_bytes_are_verified_before_executable_reuse(self):
        script = CACHE.read_text(encoding="utf-8")
        for required in (
            'manifest["key"] == key',
            'hashlib.sha256(contents).hexdigest()',
            'hashlib.sha256(diagnostics).hexdigest()',
            'os.replace(staged_receipt, receipt)',
            'res = subprocess.run([real, *flags, "-c", src, "-o", str(obj)]',
        ):
            with self.subTest(required=required):
                self.assertIn(required, script)
        self.assertNotIn("http", script.lower())


if __name__ == "__main__":
    unittest.main()

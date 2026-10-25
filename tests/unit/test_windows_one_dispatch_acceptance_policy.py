"""ROM-free policy for single-dispatch Windows acceptance."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FANOUT = ROOT / ".github/workflows/windows-acceptance-fanout-pilot.yml"
BUILDER = ROOT / ".github/workflows/windows-exact-build-only.yml"


class WindowsSingleDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FANOUT.read_text(encoding="utf-8")
        cls.build = BUILDER.read_text(encoding="utf-8")

    def test_manual_only_expensive_consumer(self):
        self.assertIn("  workflow_dispatch:", self.source)
        self.assertNotIn("  pull_request:", self.source)
        self.assertNotIn("  push:", self.source)
        self.assertIn("        default: true", self.source)

    def test_single_build_and_two_consumer_groups(self):
        self.assertIn("if: ${{ inputs.build_only == true }}", self.source)
        self.assertIn("uses: ./.github/workflows/windows-exact-build-only.yml", self.source)
        self.assertIn("needs: candidate", self.source)
        self.assertIn("needs.candidate.result == 'success'", self.source)
        self.assertIn("group: [seed-dependent, independent]", self.source)
        self.assertIn("max-parallel: 2", self.source)

    def test_no_rebuild_after_export(self):
        self.assertIn("name: qa-baldosa-native-export", self.source)
        self.assertIn("sha256sum -c SHA256SUMS", self.source)
        self.assertIn('test "$(cat source-commit.txt)" = "$GITHUB_SHA"', self.source)
        self.assertIn("tools/bind_baldosa_candidate_receipt.py", self.source)
        self.assertIn("inputs.build_only == true && github.run_id", self.source)
        self.assertNotIn("cmake --build", self.source)

    def test_all_actual_journeys_and_fail_closed_aggregate_stay(self):
        self.assertIn("tools/qa_windows_acceptance_fanout.py run", self.source)
        self.assertIn("tools/qa_windows_acceptance_fanout.py aggregate", self.source)
        self.assertIn("if: always()", self.source)

    def test_reuse_producer_must_be_real_and_exact_source(self):
        self.assertIn("if: ${{ inputs.build_only != true }}", self.source)
        self.assertIn('r["head_sha"]==os.environ["GITHUB_SHA"]', self.source)
        self.assertIn('r["status"]=="completed"', self.source)
        self.assertIn('r["conclusion"]=="success"', self.source)
        self.assertIn("Exact Baldosa Windows x64 build-only candidate", self.source)

    def test_build_only_still_matches_authoritative_bridge(self):
        self.assertIn("tools/check_windows_build_source_reuse.py", self.build)
        self.assertIn("tools/bind_baldosa_candidate_receipt.py", self.build)
        self.assertIn("SOURCE_DATE_EPOCH", self.build)


if __name__ == "__main__":
    unittest.main()

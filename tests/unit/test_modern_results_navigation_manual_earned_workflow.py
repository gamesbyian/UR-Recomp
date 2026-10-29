"""Manual ONE-03 source-movie witness must remain opt-in and preserve evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/modern-results-navigation-acceptance.yml"


class ManualEarnedWorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_existing_default_routes_remain_the_default(self):
        self.assertRegex(
            self.workflow,
            r"(?s)workflow_dispatch:\s+inputs:\s+results_shard:.*?"
            r"default: all\s+options:\s+- all\s+- earned",
        )
        self.assertIn("\${{ inputs.results_shard || 'all' }}", self.workflow)

    def test_2014_movie_is_opt_in_only_for_earned_shard(self):
        self.assertIn(
            "UR_ONE03_USE_2014_SOURCE_INPUT: "
            "\${{ inputs.results_shard == 'earned' && '1' || '0' }}",
            self.workflow,
        )
        self.assertRegex(
            self.workflow,
            r"(?s)Prove real Modern results routes.*?"
            r"run_modern_results_navigation_acceptance\.sh",
        )

    def test_failed_run_still_retains_source_binary_and_raw_evidence(self):
        self.assertIn('printf "source_sha=%s\\n" "$GITHUB_SHA"', self.workflow)
        self.assertIn('sha256sum "$ROOT/build/UniracersSNESRecomp"', self.workflow)
        self.assertRegex(self.workflow, r"(?s)Upload acceptance evidence\s+if: always\(\)")
        for suffix in (
            "/*.log", "/*-dumps/", "/*-profile/", "/*.srm",
            "/*-profile.txt", "/*.input", "/*.json", "/source-and-binary.txt",
        ):
            with self.subTest(suffix=suffix):
                self.assertIn("results-navigation" + suffix, self.workflow)


if __name__ == "__main__":
    unittest.main()

"""The GHA missed-cron path must reuse trusted main, not PR code or a second policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/owner-hp-opportunistic-research.yml"
FALLBACK = ROOT / "tools/ci/hp_research_fallback.py"


class HpOpportunisticResearchWorkflowTests(unittest.TestCase):
    def test_trusted_main_push_only_with_scoped_actions_token(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("  push:\n    branches: [main]", source)
        self.assertNotIn("  pull_request:", source)
        self.assertNotIn("  workflow_dispatch:", source)
        self.assertNotIn("  issue_comment:", source)
        self.assertNotIn("  schedule:", source)
        self.assertIn("github.repository == 'gamesbyian/UR-Recomp'", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn("github.event_name == 'push'", source)
        self.assertIn("  contents: read", source)
        self.assertIn("  actions: write", source)
        self.assertNotIn("contents: write", source)
        self.assertNotIn("pull-requests: write", source)
        self.assertIn("persist-credentials: false", source)
        self.assertIn("GH_TOKEN: ${{ github.token }}", source)
        self.assertIn("group: owner-hp-opportunistic-research-main", source)
        self.assertIn("cancel-in-progress: false", source)
        self.assertIn("runs-on: ubuntu-latest", source)
        self.assertNotIn("self-hosted", source)
        self.assertNotIn("run_on_hp: true", source)

    def test_current_source_required_before_existing_guarded_dispatcher(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('checked="$(git rev-parse HEAD)"', source)
        self.assertIn('if [[ "$checked" != "$GITHUB_SHA" ]]', source)
        self.assertIn('gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main"', source)
        self.assertIn('if [[ "$live" != "$checked" ]]', source)
        self.assertIn('exit 0\n          fi\n          # Single existing', source)
        self.assertIn("python3 tools/ci/hp_research_fallback.py --once", source)
        self.assertIn('state-dir "$RUNNER_TEMP/hp-opportunistic"', source)
        self.assertNotIn("hp_research_wall_seconds", source)
        self.assertNotIn("research_wall_seconds", source)
        # No second API writer or bypass of fail-closed producer checks:
        # this canonical helper dispatches only the same trusted-main caller.
        fallback = FALLBACK.read_text(encoding="utf-8")
        self.assertIn("COOLDOWN = timedelta(minutes=90)", fallback)
        self.assertIn("if main_sha(request) != sha:", fallback)
        self.assertIn('receipt["decision"] = "skip:priority-census-changed"', fallback)
        self.assertIn('f"repos/{REPO}/actions/workflows/{RESEARCH}/dispatches"', fallback)


if __name__ == "__main__":
    unittest.main()

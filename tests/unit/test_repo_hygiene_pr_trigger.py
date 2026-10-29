"""Keep exact-head repository hygiene available for native/test-only PRs."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/repo-hygiene.yml"


class RepositoryHygieneTriggerTests(unittest.TestCase):
    def test_pull_request_is_not_path_filtered(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("\non:\n", workflow)
        self.assertIn("\n  pull_request:\n", workflow)
        self.assertIn("\n  workflow_dispatch:\n", workflow)
        trigger = workflow.split("\n  pull_request:\n", 1)[1].split(
            "\n  workflow_dispatch:\n", 1
        )[0]
        self.assertIn("synchronize", trigger)
        self.assertIn("ready_for_review", trigger)
        self.assertNotRegex(trigger, r"(?m)^\\s+paths(?:-ignore)?:")

    def test_hygiene_still_checks_tracked_boundaries(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: python3 tools/check_repo_hygiene.py", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("cancel-in-progress: true", workflow)


if __name__ == "__main__":
    unittest.main()

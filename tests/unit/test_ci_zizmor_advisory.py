"""Static safety contract for the opt-in changed-workflow zizmor audit."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ZizmorHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (ROOT / ".github/workflows/repo-hygiene.yml").read_text()

    def test_existing_hygiene_runner_remains_single_job(self):
        self.assertEqual(self.workflow.count("  hygiene:\n"), 1)
        self.assertIn("Advisory actionlint for changed workflow files", self.workflow)
        self.assertIn("Advisory offline zizmor security scan of changed workflow files", self.workflow)
        self.assertNotIn("  zizmor:\n", self.workflow)

    def test_security_pilot_is_advisory_and_only_on_pull_requests(self):
        section = self.workflow.split(
            "      - name: Advisory offline zizmor security scan of changed workflow files\n", 1)[1]
        self.assertIn("if: github.event_name == 'pull_request'", section)
        self.assertIn("continue-on-error: true", section)
        self.assertIn("grep -E '^\\.github/workflows/[^/]+\\.ya?ml$'", section)
        self.assertIn('if [[ -f "$path" ]]', section)

    def test_exact_upstream_release_hash_and_no_online_security_audit(self):
        section = self.workflow.split("      - name: Advisory offline zizmor", 1)[1]
        self.assertIn("version=1.31.1", section)
        self.assertIn("d185f726bdaf92df78273217dfdd24ebcd6b0ef48cf3ce776ff5762b6e138c99", section)
        self.assertIn("sha256sum --check --status", section)
        self.assertIn("--offline --min-severity high", section)
        self.assertNotIn("--fix", section)
        self.assertNotIn("pip install", section)
        self.assertNotIn("sudo ", section)

    def test_github_pr_file_discovery_fails_explicitly_before_filter(self):
        section = self.workflow.split("      - name: Advisory offline zizmor", 1)[1]
        self.assertLess(section.index("--jq '.[].filename' >"),
                        section.index("grep -E '^\\.github/workflows"))
        self.assertIn("set -euo pipefail", section)
        self.assertIn("gh api --paginate", section)


if __name__ == "__main__":
    unittest.main()

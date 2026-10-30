"""Pin every third-party Actions call in owner HP/hosted Windows smoke.

The exact commits are verified against their upstream Git tag refs. Floating
major-version aliases can change the code executed on a self-hosted owner PC.
"""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/windows-native-smoke.yml"
PINS = {
    "actions/checkout": ("11bd71901bbe5b1630ceea73d27597364c9af683", "v4.2.2"),
    "actions/setup-python": ("a26af69be951a213d495a4c3e4e4022e16d87065", "v5.6.0"),
    "actions/upload-artifact": ("ea165f8d65b6e75b540449e92b4886f43607fa02", "v4.6.2"),
}


class HpCanonicalActionPinTests(unittest.TestCase):
    def test_windows_job_has_only_reviewed_exact_action_commits(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        references = re.findall(r"^\s*(?:-\s+)?uses:\s+(actions/[\w-]+)@([^\s#]+)(?:\s+#\s+(v[\d.]+))?",
                                content, flags=re.MULTILINE)
        self.assertEqual(len(references), len(PINS),
                         "unexpected new or deleted third-party action use")
        self.assertEqual({name: (sha, version) for name, sha, version in references}, PINS)
        for name, sha, version in references:
            with self.subTest(action=name):
                self.assertRegex(sha, r"^[0-9a-f]{40}$")
                self.assertNotEqual(version, "")

    def test_owner_runner_trust_boundary_is_unchanged(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.ref == 'refs/heads/main'", content)
        self.assertIn("github.repository == 'gamesbyian/UR-Recomp'", content)
        self.assertIn('inputs.run_on_hp && fromJSON(\'["self-hosted","Windows","X64"]\')', content)
        self.assertIn("candidate_commit_sha:", content)


if __name__ == "__main__":
    unittest.main()

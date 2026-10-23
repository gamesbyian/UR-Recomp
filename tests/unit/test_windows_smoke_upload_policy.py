"""Test the actual Windows artifact-upload source gate in tooling CI."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


class WindowsSmokeUploadPolicyTests(unittest.TestCase):
    def test_normal_workflow_policy_and_mutation_negatives(self):
        check = ROOT / "tools" / "ci" / "check_windows_smoke_upload_policy.py"
        normal = subprocess.run([sys.executable, str(check)], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(normal.returncode, 0, normal.stderr + normal.stdout)
        negative = subprocess.run([sys.executable, str(check), "--self-test"],
                                  cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(negative.returncode, 0, negative.stderr + negative.stdout)
        self.assertIn("test_disallows_unnamed_upload_before_or_after_approved_step",
                      negative.stderr + negative.stdout)


if __name__ == "__main__":
    unittest.main()

"""Exercise the real HP fanout's reusable-workflow event trust boundary."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FANOUT = ROOT / "tools/ci/hp_windows_isolated_boot_fanout.sh"
CHILDREN = (
    "windows_package_special_path.sh",
    "windows_package_readonly_unicode.sh",
    "windows_package_default_appdata.sh",
)


class HpFanoutEventGuardTests(unittest.TestCase):
    def test_trusted_reusable_call_and_direct_events_but_no_pr_or_foreign_ref(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "tools/ci"
            scripts.mkdir(parents=True)
            scratch = root / "scratch"
            scratch.mkdir()
            for filename in CHILDREN:
                (scripts / filename).write_text("#!/usr/bin/env bash\necho child-ok\n", encoding="utf-8")
            base = {
                **os.environ,
                "RUNNER_TEMP": str(scratch),
                "GITHUB_WORKSPACE": str(root),
                "RUNNER_NAME": "hpmini-ur-recomp",
                "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                "GITHUB_REF": "refs/heads/main",
            }

            def run(event: str, **overrides: str) -> subprocess.CompletedProcess[str]:
                env = {**base, "GITHUB_EVENT_NAME": event, **overrides}
                return subprocess.run(
                    [bash, str(FANOUT)], cwd=root, env=env,
                    capture_output=True, text=True, timeout=10, check=False,
                )

            for event in ("workflow_call", "schedule", "workflow_dispatch", "push"):
                with self.subTest(accepted=event):
                    result = run(event)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("HP_BOOT_FANOUT=passed count=3", result.stdout)
                    self.assertEqual(result.stdout.count("child-ok"), 3)
            for event in ("pull_request", "pull_request_target", "workflow_run", ""):
                with self.subTest(refused=event):
                    result = run(event)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("HP_BOOT_FANOUT=refused_event", result.stderr)
                    self.assertNotIn("child-ok", result.stdout)
            for overrides, marker in (
                ({"GITHUB_REF": "refs/pull/99/merge"}, "refused_ref"),
                ({"GITHUB_REPOSITORY": "stranger/fork"}, "refused_repo"),
                ({"RUNNER_NAME": "hosted-windows"}, "refused_runner"),
            ):
                with self.subTest(overrides=overrides):
                    result = run("workflow_call", **overrides)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("HP_BOOT_FANOUT=" + marker, result.stderr)
                    self.assertNotIn("child-ok", result.stdout)


if __name__ == "__main__":
    unittest.main()

"""Scheduled owner HP research must pass boot fanout without widening its trust boundary."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FANOUT = ROOT / "tools/ci/hp_windows_isolated_boot_fanout.sh"
SCRIPTS = (
    "windows_package_special_path.sh",
    "windows_package_readonly_unicode.sh",
    "windows_package_default_appdata.sh",
)


class HpScheduledFanoutTests(unittest.TestCase):
    def test_scheduled_owner_main_and_existing_events_run_all_three_children(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("Bash unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "tools/ci"
            scripts.mkdir(parents=True)
            scratch = root / "scratch"
            scratch.mkdir()
            for index, name in enumerate(SCRIPTS):
                (scripts / name).write_text(
                    '#!/usr/bin/env bash\n'
                    f'echo {index} >> "$RUNNER_TEMP/children"\n', encoding="utf-8")
            env = {**os.environ, "RUNNER_TEMP": str(scratch),
                   "GITHUB_WORKSPACE": str(root), "RUNNER_NAME": "hpmini-ur-recomp",
                   "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                   "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "schedule"}
            for event in ("schedule", "push", "workflow_dispatch"):
                with self.subTest(event=event):
                    (scratch / "children").unlink(missing_ok=True)
                    env["GITHUB_EVENT_NAME"] = event
                    result = subprocess.run([bash, str(FANOUT)], cwd=root, env=env,
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("HP_BOOT_FANOUT=passed count=3", result.stdout)
                    self.assertEqual(sorted((scratch / "children").read_text().splitlines()),
                                     ["0", "1", "2"])

    def test_schedule_cannot_bypass_owner_runner_repo_ref_or_event_guards(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("Bash unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scratch = root / "scratch"
            scratch.mkdir()
            env = {**os.environ, "RUNNER_TEMP": str(scratch),
                   "GITHUB_WORKSPACE": str(root), "RUNNER_NAME": "hpmini-ur-recomp",
                   "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                   "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "schedule"}
            for key, bad, marker in (
                ("RUNNER_NAME", "other-runner", "refused_runner"),
                ("GITHUB_REPOSITORY", "foreign/UR-Recomp", "refused_repo"),
                ("GITHUB_REF", "refs/heads/feature", "refused_ref"),
                ("GITHUB_EVENT_NAME", "pull_request", "refused_event"),
                ("GITHUB_EVENT_NAME", "repository_dispatch", "refused_event"),
            ):
                with self.subTest(key=key, bad=bad):
                    mutated = {**env, key: bad}
                    result = subprocess.run([bash, str(FANOUT)], cwd=root,
                                            env=mutated, capture_output=True,
                                            text=True, timeout=10)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("HP_BOOT_FANOUT=" + marker, result.stderr)
                    self.assertFalse((scratch / "children").exists())


if __name__ == "__main__":
    unittest.main()

"""HP-only isolated offscreen package fanout, with hosted serial parity."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
HP = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
HOSTED = ROOT / ".github/workflows/qa05-qa09-windows-candidate.yml"
FANOUT = ROOT / "tools/ci/hp_windows_isolated_boot_fanout.sh"
SCRIPTS = {
    "special": ("windows_package_special_path.sh", "WINDOWS_PACKAGE_SPECIAL_PATH_ISOLATION ok"),
    "readonly": ("windows_package_readonly_unicode.sh", "WINDOWS_READONLY_UNICODE_TWO_COLD_BOOTS ok"),
    "appdata": ("windows_package_default_appdata.sh", "WINDOWS_PACKAGE_DEFAULT_APPDATA_ROOT ok"),
}


class HpIsolatedBootFanoutTests(unittest.TestCase):
    def test_identical_scripts_are_authoritative_on_hosted_and_hp(self):
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn("      - name: HP bounded independent offscreen package boot fanout\n"
                      "        # The same three source-owned", source)
        self.assertIn("        if: ${{ inputs.run_on_hp }}\n"
                      "        run: bash tools/ci/hp_windows_isolated_boot_fanout.sh", source)
        worker = FANOUT.read_text(encoding="utf-8")
        for filename, marker in SCRIPTS.values():
            step = {
                "windows_package_special_path.sh": "Real packaged game under CMD-special paths",
                "windows_package_readonly_unicode.sh": "Read-only portable directory and Unicode user-data cold boots",
                "windows_package_default_appdata.sh": "Normal Windows APPDATA clean-user launch",
            }[filename]
            self.assertIn("      - name: " + step + "\n"
                          "        if: ${{ !inputs.run_on_hp }}\n"
                          "        run: bash tools/ci/" + filename, source)
            self.assertIn(filename, worker)
            self.assertIn(marker, (ROOT / "tools/ci" / filename).read_text(encoding="utf-8"))
            for trigger in (SMOKE, HP, HOSTED):
                self.assertIn('"tools/ci/' + filename + '"', trigger.read_text())
        for trigger in (SMOKE, HP, HOSTED):
            source = trigger.read_text()
            for path in ("tools/ci/hp_windows_isolated_boot_fanout.sh",
                         "tests/unit/test_hp_isolated_boot_fanout.py"):
                self.assertIn('"' + path + '"', source)

    def test_independent_offscreen_state_and_no_global_focus_overlap(self):
        special = (ROOT / "tools/ci/windows_package_special_path.sh").read_text()
        readonly = (ROOT / "tools/ci/windows_package_readonly_unicode.sh").read_text()
        appdata = (ROOT / "tools/ci/windows_package_default_appdata.sh").read_text()
        self.assertIn('SPECIAL_EXTRACT="$RUNNER_TEMP/package & bang! (installed)"', special)
        self.assertIn('SPECIAL_USER="$SPECIAL_EXTRACT/isolated-user-data"', special)
        self.assertIn('RO_PACKAGE="$RUNNER_TEMP/read-only portable/UR-Recomp-Windows-x64"', readonly)
        self.assertIn('RO_USER="$RUNNER_TEMP/portable user café 雪"', readonly)
        self.assertIn('APPDATA_DIR="$RUNNER_TEMP/default player roaming data"', appdata)
        self.assertIn('DEFAULT_USER_DATA="$APPDATA_DIR/gamesbyian/UR-Recomp"', appdata)
        for source in (special, readonly, appdata):
            self.assertIn("SDL_VIDEODRIVER=offscreen", source)
            self.assertIn("SDL_AUDIODRIVER=dummy", source)
            self.assertNotIn("QA05", source.upper())
            self.assertNotIn("QA09", source.upper())
        workflow = SMOKE.read_text()
        self.assertLess(workflow.index("HP bounded independent offscreen package boot fanout"),
                        workflow.index("Extracted-package Win32 window and default renderer smoke"))
        self.assertLess(workflow.index("HP bounded independent offscreen package boot fanout"),
                        workflow.index("Package refresh preserves user data"))

    def test_runner_and_pending_child_wait_guards(self):
        worker = FANOUT.read_text()
        for key in ("RUNNER_NAME", "GITHUB_REPOSITORY", "GITHUB_REF",
                    "GITHUB_EVENT_NAME", "RUNNER_TEMP", "GITHUB_WORKSPACE",
                    'trap hp_boot_join EXIT', 'wait "$pid" || true',
                    'wait "${pids[$i]}" || rc=$?', 'cat "$log"',
                    "HP_BOOT_FANOUT=failed", "HP_BOOT_FANOUT=passed count=3"):
            self.assertIn(key, worker)
        self.assertNotIn("kill -9", worker)
        self.assertNotIn("taskkill", worker)
        self.assertIn('"tools/ci/windows_package_special_path.sh"', worker)
        self.assertNotIn('"$GITHUB_WORKSPACE/tools/ci/', worker)
        self.assertEqual(worker.count('pids+=("$!")'), 1)

    def test_real_bash_syntax(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash not installed")
        for path in (FANOUT, *(ROOT / "tools/ci" / fn for fn, _ in SCRIPTS.values())):
            with self.subTest(path=path):
                self.assertEqual(subprocess.run([bash, "-n", str(path)]).returncode, 0)

    def test_complete_fanout_and_fail_closed_join(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash not installed")
        source = FANOUT.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "tools/ci"
            scripts.mkdir(parents=True)
            scratch = root / "scratch"
            scratch.mkdir()
            for failure in (None, "special", "readonly", "appdata"):
                for label, (filename, _) in SCRIPTS.items():
                    code = ('#!/usr/bin/env bash\n'
                            'sleep 0.10\n'
                            'echo ' + label + ' >> "$RUNNER_TEMP/joined"\n'
                            + ('exit 9\n' if label == failure else 'exit 0\n'))
                    (scripts / filename).write_text(code)
                (scratch / "joined").unlink(missing_ok=True)
                env = {**os.environ, "GITHUB_WORKSPACE": str(root),
                       "RUNNER_TEMP": str(scratch), "RUNNER_NAME": "hpmini-ur-recomp",
                       "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                       "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "push"}
                result = subprocess.run([bash, "-c", source], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=9)
                observed = sorted((scratch / "joined").read_text().splitlines())
                self.assertEqual(observed, sorted(SCRIPTS.keys()),
                                 result.stdout + result.stderr)
                self.assertEqual(result.returncode == 0, failure is None,
                                 result.stdout + result.stderr)
                self.assertIn("HP_BOOT_FANOUT=passed count=3" if failure is None
                              else "HP_BOOT_FANOUT=failed", result.stdout + result.stderr)
            # Same runner must refuse PR code, even with a fake complete script set.
            env["GITHUB_EVENT_NAME"] = "pull_request"
            refused = subprocess.run([bash, "-c", source], cwd=root, env=env,
                                     capture_output=True, text=True, timeout=9)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("HP_BOOT_FANOUT=refused_event", refused.stderr)


if __name__ == "__main__":
    unittest.main()

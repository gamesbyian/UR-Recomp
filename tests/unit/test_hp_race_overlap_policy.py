"""Exact acceptance and fail-closed policy for HP race/QA05 overlap."""
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
HOSTED = ROOT / ".github/workflows/qa05-qa09-windows-candidate.yml"
HP = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
RACE = ROOT / "tools/ci/windows_package_race_result.sh"


class HpRaceOverlapPolicyTests(unittest.TestCase):
    def test_exact_package_race_witness_preserved(self):
        script = RACE.read_text()
        for marker in (
            "set -euo pipefail", 'rm -rf -- "$DUMPS"',
            'rm -f -- "$RUNNER_TEMP/package-race-result.log"',
            "SDL_VIDEODRIVER=offscreen", "SDL_AUDIODRIVER=dummy",
            "timeout 600 powershell.exe", 'test "$RC" -eq 0',
            "tools/check_result_screen_time.py", "--checkpoint race-results",
            "Config/saves anchored to user data", 'grep -Fq "$USER_DATA_WIN"',
            'python tools/assemble_windows_package.py verify --package "$TEST_PACKAGE"',
            'echo "WINDOWS_PACKAGE_RACE_RESULT ok"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_hp_only_overlap_joins_before_fallback_and_later_state(self):
        source = SMOKE.read_text()
        i = source.index("      - name: Extracted-package race-result acceptance")
        j = source.index("      - name: Extracted-package Win32", i)
        k = source.index("      - name: QA-05 packaged", j)
        finish = source.index("      - name: Package refresh", k)
        serial = source[i:j]
        self.assertIn("if: ${{ !inputs.run_on_hp }}", serial)
        self.assertIn("run: bash tools/ci/windows_package_race_result.sh", serial)
        work = source[k:finish]
        for marker in (
            "UR_QA05_HP_PARALLEL_PILOT: ${{ inputs.run_on_hp && '1' || '0' }}",
            'RACE_PID="$!"', "trap hp_race_cleanup EXIT",
            'if ! wait "${pids[$idx]}"; then', 'wait "$RACE_PID" || race_rc=$?',
            "trap - EXIT", 'cat "$RUNNER_TEMP/hp-race-overlap.log"',
            'if [[ "$race_rc" -ne 0 ]]; then',
            "HP_RACE_OVERLAP=failed; serial fallback required",
            "HP_RACE_OVERLAP=serial_fallback_passed",
            "HP_RACE_OVERLAP=passed",
            "HP_QA05_PARALLEL_FALLBACK=serial_5_of_5",
            "WINDOWS_QA05_DEFAULT_RETURN_AUDIO=5/5",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, work)
        self.assertLess(work.index('if ! wait "${pids[$idx]}"; then'),
                        work.index('wait "$RACE_PID" || race_rc=$?'))
        self.assertLess(work.index('wait "$RACE_PID" || race_rc=$?'),
                        work.index('if [[ "$parallel_failed" -ne 0 ]]; then'))
        self.assertEqual(work.count('RACE_PID="$!"'), 1)

    def test_exact_hosted_and_hp_source_invalidation(self):
        for path in (SMOKE, HOSTED, HP):
            with self.subTest(path=path.name):
                src = path.read_text()
                self.assertIn('      - "tools/ci/windows_package_race_result.sh"', src)
                self.assertIn('      - "tests/unit/test_hp_race_overlap_policy.py"', src)
        self.assertIn("test_hp_compiler_profile: true", HOSTED.read_text())
        self.assertIn("cancel-in-progress: false", HP.read_text())

    def test_real_bash_syntax(self):
        bash = shutil.which("bash")
        if bash:
            subprocess.run([bash, "-n", str(RACE)], check=True)

    @unittest.skipIf(os.name == "nt", "POSIX descendant-process harness")
    def test_abnormal_qa_exit_joins_race_descendants_before_returning(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash missing")
        smoke = SMOKE.read_text()
        i = smoke.index("            hp_race_cleanup() {")
        j = smoke.index("            trap hp_race_cleanup EXIT", i)
        # Execute the actual source-owned cleanup function, not a synthetic
        # imitation. A fake race Bash wrapper starts a real sleep child,
        # then writes its evidence marker. Early QA failure must not return
        # before that descendant has exited and the wrapper has joined.
        cleanup = "\n".join(
            line[12:] for line in smoke[i:j].splitlines()
            if line.startswith("            ")
        ) + "\n"
        self.assertIn('wait "$RACE_PID" || true', cleanup)
        self.assertNotIn('kill "$RACE_PID"', cleanup)
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "race-completed"
            env = dict(os.environ, OWNED_MARKER=str(marker))
            source = (
                "set -euo pipefail\n"
                "RACE_PID=''\n"
                "bash -c 'sleep 0.3; printf complete > \"$OWNED_MARKER\"' &\n"
                'RACE_PID="$!"\n'
                + cleanup +
                "trap hp_race_cleanup EXIT\n"
                "false\n"
            )
            start = time.monotonic()
            run = subprocess.run(
                [bash, "-c", source], env=env, capture_output=True,
                text=True, timeout=8,
            )
            elapsed = time.monotonic() - start
            self.assertNotEqual(run.returncode, 0)
            self.assertTrue(marker.exists(), run.stdout + run.stderr)
            self.assertEqual(marker.read_text(), "complete")
            self.assertGreaterEqual(elapsed, 0.2)

    @unittest.skipIf(os.name == "nt", "POSIX stub harness; real Windows checks remain separate")
    def test_no_stale_success_on_failure_or_missing_checkpoint(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash missing")
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            stubs = d / "stubs"
            stubs.mkdir()
            commands = {
                "cygpath": '#!/usr/bin/env bash\nprintf "%s\\n" "$2"\n',
                "powershell.exe": '#!/usr/bin/env bash\nprintf "Config/saves anchored to user data %s\\n" "$UR_RECOMP_USER_DATA_ROOT"\nif [[ "$FAKE_GAME_FAIL" == 1 ]]; then exit 9; fi\n',
                "python": '#!/usr/bin/env bash\nif [[ "$1" == "tools/check_result_screen_time.py" && "$FAKE_CHECK_FAIL" == 1 ]]; then exit 7; fi\nif [[ "$1" == "tools/assemble_windows_package.py" && "$FAKE_PACKAGE_FAIL" == 1 ]]; then exit 8; fi\n',
            }
            for filename, content in commands.items():
                stub = stubs / filename
                stub.write_text(content)
                stub.chmod(0o755)
            env = dict(os.environ, RUNNER_TEMP=temp, GITHUB_WORKSPACE=temp,
                       TEST_PACKAGE=str(d / "package"), PACKAGE_USER_DATA=str(d / "user"),
                       FAKE_GAME_FAIL="0", FAKE_CHECK_FAIL="0",
                       FAKE_PACKAGE_FAIL="0",
                       PATH=str(stubs) + os.pathsep + os.environ.get("PATH", ""))
            command = [bash, str(RACE)]
            good = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            self.assertIn("WINDOWS_PACKAGE_RACE_RESULT ok", good.stdout)
            stale = d / "package-race-result-dumps" / "old"
            stale.write_text("stale")
            bad = subprocess.run(command, cwd=ROOT, env=dict(env, FAKE_GAME_FAIL="1"),
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertNotIn("WINDOWS_PACKAGE_RACE_RESULT ok", bad.stdout)
            self.assertFalse(stale.exists())
            for flag in ("FAKE_CHECK_FAIL", "FAKE_PACKAGE_FAIL"):
                bad = subprocess.run(command, cwd=ROOT, env=dict(env, **{flag: "1"}),
                                     capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0)
                self.assertNotIn("WINDOWS_PACKAGE_RACE_RESULT ok", bad.stdout)


if __name__ == "__main__":
    unittest.main()

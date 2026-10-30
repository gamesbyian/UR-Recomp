"""Source-level policy for isolated real Windows QA-05 parallel HP pilot.

The actual Win32/SDL acceptance still requires a real Windows runner; these
tests prevent unsafe process, output and dispatch regressions in CI routing.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools" / "ci" / "qa05_restart_attempt.sh"
SMOKE = ROOT / ".github" / "workflows" / "windows-native-smoke.yml"
HP = ROOT / ".github" / "workflows" / "owner-hp-main-windows-smoke.yml"


class HpQa05ParallelPolicyTests(unittest.TestCase):
    def test_worker_bash_syntax(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash unavailable (source assertions remain active)")
        subprocess.run([bash, "-n", str(WORKER)], check=True)

    def test_each_attempt_owns_its_process_evidence_and_user_state(self):
        source = WORKER.read_text(encoding="utf-8")
        for expected in (
            '[[ "$#" -ne 3 || ! "$1" =~ ^[1-5]$ ]]',
            '"$RUNNER_TEMP/qa05-restart-user-$attempt"',
            '"$RUNNER_TEMP/qa05-restart-$attempt.log"',
            '"$RUNNER_TEMP/qa05-restart-$attempt.raw"',
            '"$RUNNER_TEMP/qa05-restart-$attempt.json"',
            "pause_on_focus_loss=0",
            "SDL_AUDIO_DISK_OUTPUT_FILE=",
            "UR_ONBOARDING_STATE_PATH=",
            "UR_RECOMP_USER_DATA_ROOT=",
            "python -m tools.capture_modern_restart_audio",
            "recovery_confirmed",
            'rm -f -- "$LOG" "$PCM" "$JSON"',
            'test -s "$LOG" && test -s "$PCM" && test -s "$JSON"',
            "python -m tools.qa05_restart_input_guard",
            "UR_FOCUS_PAUSE APPLIED",
            'rm -f "$PCM"',
            'UR_QA05_RESTART_AUDIBLE_ATTEMPT=$attempt/5 passed',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)
        self.assertNotIn("taskkill /F /IM", source)
        self.assertNotIn("Get-Process", source)

    @unittest.skipIf(os.name == "nt", "POSIX stub harness; Windows native journey is separate")
    def test_serial_fallback_cannot_accept_stale_capture_evidence(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash unavailable")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stubs = root / "stubs"
            stubs.mkdir()
            cygpath = stubs / "cygpath"
            cygpath.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "${@: -1}"\n')
            python = stubs / "python"
            python.write_text(
                '#!/usr/bin/env bash\n'
                'if [[ "${1:-}" == "-m" && "${2:-}" == "tools.capture_modern_restart_audio" '
                '&& "${FAKE_CAPTURE_MODE:-}" == "fresh" ]]; then\n'
                '  printf "UR_HOST_STATE LOADED pause_on_focus_loss=0 valid " '
                '> "$RUNNER_TEMP/qa05-restart-1.log"\n'
                '  printf "\\nUR_ONBOARDING HIDDEN first_run=0\\n" '
                '>> "$RUNNER_TEMP/qa05-restart-1.log"\n'
                '  printf "PCM" > "$RUNNER_TEMP/qa05-restart-1.raw"\n'
                "  printf '{\"recovery_confirmed\":true}\\n' "
                '> "$RUNNER_TEMP/qa05-restart-1.json"\n'
                'fi\nexit 0\n'
            )
            for stub in (cygpath, python):
                stub.chmod(0o755)
            for suffix, content in (
                (".log", "UR_HOST_STATE LOADED pause_on_focus_loss=0 valid "
                         "\nUR_ONBOARDING HIDDEN first_run=0\n"),
                (".raw", "old-pcm"),
                (".json", '{"recovery_confirmed":true}\n'),
            ):
                (root / ("qa05-restart-1" + suffix)).write_text(content)
            env = dict(os.environ, RUNNER_TEMP=str(root),
                       PATH=str(stubs) + os.pathsep + os.environ.get("PATH", ""))
            command = [bash, str(WORKER), "1", "launcher", "script"]
            rejected = subprocess.run(command, env=dict(env, FAKE_CAPTURE_MODE="none"),
                                      capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0, rejected.stdout)
            self.assertNotIn("AUDIBLE_ATTEMPT=1/5 passed", rejected.stdout)
            for suffix in (".log", ".raw", ".json"):
                self.assertFalse((root / ("qa05-restart-1" + suffix)).exists())
            fresh = subprocess.run(command, env=dict(env, FAKE_CAPTURE_MODE="fresh"),
                                   capture_output=True, text=True)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertIn("AUDIBLE_ATTEMPT=1/5 passed", fresh.stdout)
            self.assertTrue((root / "qa05-restart-1.json").is_file())
            self.assertFalse((root / "qa05-restart-1.raw").exists())

    def test_hp_only_parallel_waits_for_every_child_and_falls_back_to_serial(self):
        source = SMOKE.read_text(encoding="utf-8")
        for expected in (
            "UR_QA05_ALLOW_HIDDEN_WINDOW: ${{ inputs.run_on_hp && '1' || '0' }}",
            "UR_QA05_HP_PARALLEL_PILOT: ${{ inputs.run_on_hp && '1' || '0' }}",
            "if [[ \"$UR_QA05_HP_PARALLEL_PILOT\" == '1' ]]; then",
            "pids+=(\"$!\")",
            'if ! wait "${pids[$idx]}"; then',
            "parallel_failed=1",
            "HP_QA05_PARALLEL_PILOT=failed",
            "HP_QA05_PARALLEL_FALLBACK=serial_5_of_5",
            "HP_QA05_PARALLEL_PILOT=passed 5/5",
            'echo "WINDOWS_QA05_DEFAULT_RETURN_AUDIO=5/5"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)
        # Parallel and authoritative fallback launch five discrete workers.
        self.assertGreaterEqual(source.count('bash "$WORKER" "$attempt"'), 3)
        self.assertEqual(source.count('pids+=("$!")'), 1)
        self.assertIn("if [[ \"$parallel_failed\" -ne 0 ]]; then", source)

    def test_both_windows_routers_invalidate_for_changed_worker(self):
        for path in (SMOKE, HP):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn('      - "tools/ci/qa05_restart_attempt.sh"', source)
                self.assertIn('      - "tests/unit/test_hp_qa05_parallel_policy.py"', source)


if __name__ == "__main__":
    unittest.main()

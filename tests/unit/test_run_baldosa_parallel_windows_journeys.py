"""ROM-free contracts for the parallel Windows journey pilot, not release QA."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from threading import Event
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_baldosa_parallel_windows_journeys as p


class WindowsParallelJourneysTest(unittest.TestCase):
    def test_existing_exact_thirteen_original_workflow_scripts_are_reused(self):
        yaml = p.WORKFLOW.read_text(encoding="utf-8")
        scripts = p.extract_commands(yaml)
        self.assertEqual(len(scripts), 13)
        self.assertEqual(len(p.STEPS), 13)
        for script in scripts:
            self.assertTrue(script.startswith("set -euo pipefail\n"))
            self.assertIn('--exe "baldosa/build-ur-win/UniracersSNESRecomp.exe"', script)
            self.assertEqual(len(p.OUT_RE.findall(script)), 1)
        self.assertIn("native_real_1p_records", scripts[1])
        self.assertIn("native_real_2p_records", scripts[2])
        self.assertIn('baseline/Modern Player Data With Spaces/saves/save.srm', scripts[1])
        self.assertIn('baseline/Modern Player Data With Spaces/saves/save.srm', scripts[2])
        self.assertIn("--recover-interrupted-catalog", scripts[6])
        self.assertIn("native_source_practice_dragster", scripts[7])
        self.assertIn("native_player_created_2p_records", scripts[8])

    def test_no_vanishing_case_or_scope_expansion(self):
        yaml = p.WORKFLOW.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing existing"):
            p.extract_commands(yaml.replace(
                "Native controller selects existing P1 both directions across cold game processes",
                "A different name", 1
            ))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            p.extract_commands(yaml.replace(
                "Real stock 1P result and newly saved Records reopened by fresh native game",
                p.STEPS[0], 1
            ))
        with self.assertRaisesRegex(ValueError, "new per-step environment"):
            p.extract_commands(yaml.replace(
                "      - name: " + p.STEPS[1] + "\n",
                "      - name: " + p.STEPS[1] + "\n"
                '        env:\n          EXTRA: "1"\n',
                1
            ))
        with self.assertRaisesRegex(ValueError, "output roots"):
            source = yaml.replace(
                'native_first_racer_andrew"',
                'native_first_racer"',
                1
            )
            p.extract_commands(source)

    def test_workflow_keeps_serial_fallback_and_all_strict_artifacts(self):
        yaml = p.WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(
            yaml.count("github.event_name != 'pull_request' && inputs.parallel_journeys != true"),
            len(p.STEPS)
        )
        self.assertIn("baseline owns its root", yaml)
        self.assertIn("Pilot parallel authentic Windows journeys", yaml)
        self.assertIn("default: false", yaml)
        self.assertIn("baldosa-win32-parallel-journey-timing", yaml)
        self.assertIn("--workers 3 --overlap-baseline", yaml)
        self.assertIn('--workers 2 --out "$RUNNER_TEMP/baldosa-parallel-journeys"', yaml)
        self.assertIn('if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then', yaml)
        for artifact in (
            "baldosa-modern-windows-x64-romless-candidate",
            "baldosa-win32-candidate-binding",
            "baldosa-win32-native-pause-evidence",
            "baldosa-win32-pre-records-pair-evidence",
            "baldosa-win32-native-p2-catalog-recovery-smoke",
            "baldosa-win32-native-p2-catalog-raw-stages",
            "baldosa-win32-native-practice-lifecycle",
            "qa-baldosa-native-export",
        ):
            self.assertIn("name: " + artifact, yaml)

    def test_measured_long_running_practice_runs_before_short_independent_routes(self):
        commands = p.extract_commands(p.WORKFLOW.read_text(encoding="utf-8"))
        schedule = p.independent_priority_indices(len(commands))
        # The previous FIFO submitted the longest original route at the end.
        # Only submission order changes: every real original command and
        # independent case remains present with exactly its original index.
        self.assertEqual(len(schedule), 10)
        self.assertEqual(sorted(schedule), list(range(3, len(p.STEPS))))
        self.assertEqual(schedule[0], 12)
        self.assertEqual(
            p.STEPS[schedule[0]],
            "Native Practice enters ten original courses across both unlock states",
        )
        self.assertEqual(schedule[1:4], (8, 7, 9))
        self.assertFalse(any("baseline/" in commands[i] for i in schedule))
        with self.assertRaisesRegex(ValueError, "priority no longer matches"):
            p.independent_priority_indices(len(commands) - 1)
        with mock.patch.object(p, "INDEPENDENT_PRIORITY", (12,) * 10):
            with self.assertRaisesRegex(ValueError, "priority no longer matches"):
                p.independent_priority_indices(len(commands))

    def test_overlap_starts_only_independent_cases_before_real_sram_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            exe, fixture = root / "game.exe", root / "fixture.exe"
            exe.write_bytes(b"game")
            fixture.write_bytes(b"fixture")
            shared = root / "UR Baldosa Win32 Pause Route"
            seed = shared / "baseline" / "Modern Player Data With Spaces" / "saves" / "save.srm"
            baseline_finished = Event()
            overlap_seen = Event()
            summary = root / "summary.md"
            env = dict(GITHUB_SHA="a"*40, RUNNER_TEMP=str(root),
                       GITHUB_STEP_SUMMARY=str(summary))
            def pretend(index, script, work, env):
                if index == 0:
                    shared.mkdir(parents=True, exist_ok=False)
                    self.assertTrue(overlap_seen.wait(3), "independent run never overlapped baseline")
                    seed.parent.mkdir(parents=True)
                    seed.write_bytes(b"s"*8192)
                    baseline_finished.set()
                elif index in (1, 2):
                    self.assertTrue(baseline_finished.is_set(),
                                    "a Records test consumed unfinished SRAM")
                    self.assertEqual(seed.stat().st_size, 8192)
                else:
                    if not baseline_finished.is_set():
                        overlap_seen.set()
                (work / f"step-{index:02d}.log").write_text("simulated unit-only receipt\\n")
                (work / f"step-{index:02d}.md").write_text("unit-only\\n")
                return dict(name=p.STEPS[index], index=index, exit_code=0,
                            elapsed_seconds=1, error=None,
                            log=f"step-{index:02d}.log", summary=f"step-{index:02d}.md")
            with mock.patch.object(p, "EXE", exe), \
                 mock.patch.object(p, "FIXTURE", fixture), \
                 mock.patch.object(p, "run_one", side_effect=pretend):
                outcome = p.run_all(workers=3, work=root / "work", env=env,
                                    overlap_baseline=True)
            self.assertTrue(overlap_seen.is_set())
            self.assertEqual(outcome["executed_cases"], 13)
            self.assertEqual([case["index"] for case in outcome["cases"]], list(range(13)))
            self.assertEqual(outcome["missing_cases"], [])
            self.assertTrue(outcome["overlap_baseline"])
            self.assertFalse(outcome["identity_changed"])
            self.assertEqual(outcome["release_gate_credit"], 0)

    def test_overlap_missing_source_seed_blocks_both_dependent_records(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            exe, fixture = root / "game.exe", root / "fixture.exe"
            exe.write_bytes(b"game")
            fixture.write_bytes(b"fixture")
            shared = root / "UR Baldosa Win32 Pause Route"
            env = dict(GITHUB_SHA="a"*40, RUNNER_TEMP=str(root),
                       GITHUB_STEP_SUMMARY=str(root / "summary.md"))
            def pretend(index, script, work, env):
                if index == 0:
                    shared.mkdir(parents=True, exist_ok=False)
                (work / f"step-{index:02d}.log").write_text("synthetic unit receipt\\n")
                return dict(name=p.STEPS[index], index=index, exit_code=0,
                            elapsed_seconds=1, error=None,
                            log=f"step-{index:02d}.log", summary=f"step-{index:02d}.md")
            with mock.patch.object(p, "EXE", exe), \
                 mock.patch.object(p, "FIXTURE", fixture), \
                 mock.patch.object(p, "run_one", side_effect=pretend):
                outcome = p.run_all(workers=3, work=root / "work", env=env,
                                    overlap_baseline=True)
            self.assertEqual(outcome["executed_cases"], 11)
            self.assertEqual(outcome["missing_cases"], list(p.STEPS[1:3]))
            self.assertEqual(outcome["cases"][0]["exit_code"], 1)
            self.assertEqual(outcome["cases"][0]["error"],
                             "missing_exact_real_8192_byte_baseline_sram")
            self.assertEqual(outcome["release_gate_credit"], 0)
            with self.assertRaisesRegex(ValueError, "requires three"):
                p.run_all(workers=2, work=root / "unused", env=env,
                          overlap_baseline=True)

    def test_overlap_refuses_a_new_undeclared_baseline_dependency(self):
        commands = p.extract_commands(p.WORKFLOW.read_text(encoding="utf-8"))
        commands[3] += "\\n# consumed baseline/save.srm unexpectedly\\n"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "baseline seed dependency"):
                p.run_overlapping_baseline(commands, Path(folder) / "work",
                                           {"RUNNER_TEMP": folder})

    def test_windows_uses_pinned_git_bash_not_wsl_shim(self):
        with tempfile.TemporaryDirectory() as directory:
            git_bash = Path(directory) / "Git" / "bin" / "bash.exe"
            git_bash.parent.mkdir(parents=True)
            git_bash.write_bytes(b"runner Git Bash fixture")
            self.assertEqual(p.find_git_bash(windows=True, program_files=directory),
                             str(git_bash))
            self.assertEqual(p.find_git_bash(windows=False), "bash")
            git_bash.unlink()
            with self.assertRaisesRegex(RuntimeError, "installed Git Bash"):
                p.find_git_bash(windows=True, program_files=directory)

    def test_parallel_runner_keeps_source_identity_and_fail_closed_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            exe = root / "candidate.exe"
            fixture = root / "fixture.exe"
            exe.write_bytes(b"native-candidate")
            fixture.write_bytes(b"native-fixture")
            summary = root / "summary.md"
            env = dict(GITHUB_SHA="a"*40, RUNNER_TEMP=str(root),
                       GITHUB_STEP_SUMMARY=str(summary))
            calls = []
            def pretend(index, script, work, env):
                calls.append(index)
                (work / f"step-{index:02d}.log").write_text("dummy real probe log\n")
                (work / f"step-{index:02d}.md").write_text("sample summary\n")
                return dict(name=p.STEPS[index], index=index,
                            exit_code=1 if index == 7 else 0,
                            elapsed_seconds=3.0, error=None,
                            log=f"step-{index:02d}.log",
                            summary=f"step-{index:02d}.md")
            with mock.patch.object(p, "EXE", exe), \
                 mock.patch.object(p, "FIXTURE", fixture), \
                 mock.patch.object(p, "run_one", side_effect=pretend):
                outcome = p.run_all(workers=2, work=root / "work", env=env)
            self.assertEqual(outcome["expected_cases"], 13)
            self.assertEqual(outcome["executed_cases"], 13)
            self.assertEqual(sorted(calls), list(range(13)))
            self.assertEqual(outcome["release_gate_credit"], 0)
            self.assertFalse(outcome["identity_changed"])
            self.assertFalse(outcome["missing_cases"])
            self.assertEqual(outcome["exe_sha256"], p.sha256_file(exe))
            self.assertEqual([i["exit_code"] for i in outcome["cases"]].count(1), 1)
            self.assertIn("FAIL", summary.read_text())
            self.assertEqual(json.loads(
                (root / "work/pilot-result.json").read_text()
            )["source_sha"], "a"*40)
            with self.assertRaisesRegex(ValueError, "2/3"):
                p.run_all(workers=4, work=root / "should-not-exist", env=env)


if __name__ == "__main__":
    unittest.main()

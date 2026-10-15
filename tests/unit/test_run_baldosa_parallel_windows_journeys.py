"""ROM-free contracts for the parallel Windows journey pilot, not release QA."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_baldosa_parallel_windows_journeys as p


class WindowsParallelJourneysTest(unittest.TestCase):
    def test_existing_exact_eleven_original_workflow_scripts_are_reused(self):
        yaml = p.WORKFLOW.read_text(encoding="utf-8")
        scripts = p.extract_commands(yaml)
        self.assertEqual(len(scripts), 11)
        self.assertEqual(len(p.STEPS), 11)
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
        self.assertIn("remaining isolated journeys fan out", yaml)
        self.assertIn("Pilot parallel authentic Windows journeys", yaml)
        self.assertIn("default: false", yaml)
        self.assertIn("baldosa-win32-parallel-journey-timing", yaml)
        self.assertIn('options: ["2", "3"]', yaml)
        self.assertIn("github.event_name == 'pull_request' && '3'", yaml)
        self.assertIn("inputs.parallel_workers || '2'", yaml)
        self.assertEqual(yaml.count("      parallel_workers:"), 2)
        self.assertEqual(yaml.count('default: "2"'), 2)
        self.assertEqual(len(p.extract_commands(yaml)), len(p.STEPS))
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
                outcome = p.run_all(workers=3, work=root / "work", env=env)
            self.assertEqual(outcome["workers"], 3)
            self.assertEqual(outcome["expected_cases"], 11)
            self.assertEqual(outcome["executed_cases"], 11)
            self.assertEqual(sorted(calls), list(range(11)))
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

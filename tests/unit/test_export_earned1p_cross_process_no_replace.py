"""Real subprocess contention for earned-run export; synthetic ROM-free inputs.

Recovered and narrowly adapted from first-party H26 source:
Drive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ,
  evidence/agent2-h25.zip -> evidence/agent2-h24.zip ->
  prior-bundles/20261020T23-agent2-five-line-recovery.zip ->
  evidence/agent2-h22-recovery.zip -> evidence/agent2-h20.zip ->
  evidence/agent3-h19-recovery.zip ->
  upstream/20261020T1835Z-agent3-five-line-h18-recovery.zip ->
  pr2044/tests/unit/test_export_earned1p_process_contention.py
Original leaf SHA-256:
  49c10d021a6c9ce36837dfa4057d89291988237eba5cde77201295862bf80a80

Archive test passed 2/2 normal and -OO with its archived exporter.
This test only preserves the missing two-real-process no-replace contract,
not a Windows physical, disk-full, authentic earned run or release gate.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from export_baldosa_earned_1p_run import SOURCE_SCOPE


class CrossProcessEarnedRunPublication(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux") or os.name == "nt",
                         "atomic no-replace publisher only qualified on Linux and Windows")
    def test_competing_processes_publish_once_without_staging_leaks(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            journey = root / "source journey"
            runs = journey / "Brand New Player With Spaces" / "runs" / "mike"
            runs.mkdir(parents=True)
            payload = b"synthetic record bytes; never a game-earned run"
            (runs / "source.urrun").write_bytes(payload)
            report = {
                "scope": SOURCE_SCOPE,
                "first_game_created_first_named_racer": True,
                "second_game_loaded_named_sram_and_finished_real_source_race": True,
                "third_game_reopened_exact_earned_run_read_only": True,
                "active_selector_and_catalog_preserved": True,
                "anonymous_sram_preserved": True,
                "physical_gamepad_verified": False,
                "strict_original_native_event_pass": False,
                "release_gate_credit": 0,
                "one_canonical_run_sha256": hashlib.sha256(payload).hexdigest(),
            }
            (journey / "report.json").write_text(json.dumps(report), encoding="utf-8")
            destination = root / "published"
            command = [
                sys.executable,
                str(ROOT / "tools" / "export_baldosa_earned_1p_run.py"),
                "--journey", str(journey), "--out", str(destination),
            ]
            # Separate interpreters, real OS directory publication, and one
            # shared output path. A preflight exists() alone cannot win this.
            processes = [
                subprocess.Popen(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
                for _ in range(2)
            ]
            try:
                outputs = [p.communicate(timeout=20) for p in processes]
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                        process.communicate(timeout=5)
            codes = sorted(p.returncode for p in processes)
            self.assertEqual(codes, [0, 1], outputs)
            self.assertEqual(
                sum("UR_CI_EARNED_1P_RUN_EXPORTED" in stdout for stdout, _ in outputs),
                1, outputs)
            self.assertEqual(
                set(p.name for p in destination.iterdir()),
                {"earned.urrun", "source-report.json", "manifest.json"})
            self.assertEqual((destination / "earned.urrun").read_bytes(), payload)
            manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["members"]["earned.urrun"]["sha256"],
                hashlib.sha256(payload).hexdigest())
            self.assertFalse(manifest["independent_release_acceptance"])
            self.assertFalse(list(root.glob(".pending-earned-1p-*")),
                             "losing process leaked a partially published staging directory")


if __name__ == "__main__":
    unittest.main()

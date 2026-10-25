"""ROM-free tests for fail-closed controller replay reduction."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_input
import reduce_controller_fixture as tool

FAKE_ORACLE = """
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--candidate',required=True,type=Path)
p.add_argument('--receipt',required=True,type=Path)
p.add_argument('--bad-hash',action='store_true')
p.add_argument('--invalid-original',action='store_true')
a=p.parse_args()
data=a.candidate.read_bytes()
rows=data.decode().splitlines()
valid='0:100:001' in rows and not a.invalid_original
success=valid and '100:10:002' in rows
result=dict(schema='ur-controller-reducer-oracle/1',
    candidate_sha256=('0'*64 if a.bad_hash else hashlib.sha256(data).hexdigest()),
    source_sha='a'*40,original_rom_sha256='b'*64,native_binary_sha256='c'*64,
    reference_engine='snes9x',discrepancy_id='nmi-test',semantic_phase='test-return',
    original_valid=valid,native_valid=True,
    result=('reproduced' if success else 'not_reproduced'))
a.receipt.write_text(json.dumps(result))
"""


class ReducerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.oracle = self.root / "oracle.py"
        self.oracle.write_text(FAKE_ORACLE)
        self.fixture = self.root / "fixture.script"
        self.fixture.write_text("0:100:001\n100:10:002\n120:10:004\n140:10:008\n")

    def run_case(self, extra=(), max_calls=60):
        return tool.reduce(
            controller_input.load_controller_runs(self.fixture),
            hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
            100, [sys.executable, str(self.oracle), *extra], max_calls=max_calls,
        )

    def test_shrinks_and_preserves_entry_and_timestamps(self):
        runs, evidence = self.run_case()
        self.assertEqual(tool.encode(runs), b"0:100:001\n100:10:002\n")
        self.assertEqual(evidence["removed_runs"], 2)
        self.assertEqual(evidence["protected_runs"], 1)
        self.assertFalse(evidence["release_gate_accepted"])

    def test_budget_stops_without_unverified_output(self):
        runs, evidence = self.run_case(max_calls=4)
        self.assertTrue(evidence["budget_exhausted"])
        self.assertEqual(len(runs), 4)
        self.assertEqual(evidence["oracle_calls"], 4)

    def test_exact_candidate_mismatch_aborts(self):
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            self.run_case(["--bad-hash"])

    def test_unqualified_original_cannot_seed_reducer(self):
        with self.assertRaisesRegex(ValueError, "does not reproduce"):
            self.run_case(["--invalid-original"])

    def test_cli_writes_report_and_reduced_script(self):
        import subprocess
        output = self.root / "min.script"
        report = self.root / "min.json"
        subprocess.run([
            sys.executable, str(ROOT / "tools" / "reduce_controller_fixture.py"),
            "--input", str(self.fixture), "--output", str(output),
            "--report", str(report), "--protected-before-frame", "100",
            "--oracle", sys.executable, str(self.oracle),
        ], check=True, capture_output=True, text=True, timeout=30)
        self.assertEqual(output.read_bytes(), b"0:100:001\n100:10:002\n")
        self.assertEqual(json.loads(report.read_text())["removed_runs"], 2)


if __name__ == "__main__":
    unittest.main()

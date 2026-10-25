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
p.add_argument('--need-tail',action='store_true')
p.add_argument('--obs-frame',type=int,default=110)
a=p.parse_args()
data=a.candidate.read_bytes()
rows=data.decode().splitlines()
valid='0:100:001' in rows and not a.invalid_original
success=valid and '100:10:002' in rows and (not a.need_tail or '140:10:008' in rows)
result=dict(schema='ur-controller-reducer-oracle/1',
    candidate_sha256=('0'*64 if a.bad_hash else hashlib.sha256(data).hexdigest()),
    source_sha='a'*40,original_rom_sha256='b'*64,native_binary_sha256='c'*64,
    reference_engine='snes9x',discrepancy_id='nmi-test',semantic_phase='test-return',
    original_valid=valid,native_valid=True,
    guest_clocks=dict(reference_observation_frame=a.obs_frame),
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

    def test_exact_observation_horizon_verifies_late_tail_first(self):
        runs, receipt = tool.reduce(
            controller_input.load_controller_runs(self.fixture),
            hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
            100, [sys.executable, str(self.oracle)],
            max_calls=4, observation_frame=110,
        )
        self.assertEqual(tool.encode(runs), b"0:100:001\n100:10:002\n")
        self.assertTrue(receipt["post_observation_trial"])
        self.assertEqual(receipt["post_observation_removed_runs"], 2)
        self.assertEqual(receipt["observation_frame"], 110)
        self.assertEqual(receipt["oracle_calls"], 4)
        self.assertEqual(receipt["removed_runs"], 2)
        self.assertTrue(receipt["budget_exhausted"])

    def test_unreproduced_tail_removal_keeps_exact_original_route(self):
        runs, receipt = tool.reduce(
            controller_input.load_controller_runs(self.fixture),
            hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
            100, [sys.executable, str(self.oracle), "--need-tail"],
            max_calls=4, observation_frame=110,
        )
        self.assertEqual(tool.encode(runs), self.fixture.read_bytes())
        self.assertTrue(receipt["post_observation_trial"])
        self.assertEqual(receipt["post_observation_removed_runs"], 0)
        self.assertTrue(receipt["budget_exhausted"])

    def test_observation_boundary_and_legacy_mode(self):
        with self.assertRaisesRegex(ValueError, "authenticated original"):
            tool.reduce(controller_input.load_controller_runs(self.fixture),
                        "0" * 64, 100, [sys.executable, str(self.oracle)],
                        observation_frame=99)
        # The run starting exactly at the observation frame is retained.
        runs, receipt = tool.reduce(
            controller_input.load_controller_runs(self.fixture),
            hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
            100, [sys.executable, str(self.oracle), "--obs-frame", "100"],
            max_calls=4, observation_frame=100,
        )
        self.assertIn(b"100:10:002", tool.encode(runs))
        self.assertEqual(receipt["post_observation_removed_runs"], 2)
        with self.assertRaisesRegex(ValueError, "differs from horizon"):
            tool.reduce(
                controller_input.load_controller_runs(self.fixture),
                hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
                100, [sys.executable, str(self.oracle)],
                max_calls=4, observation_frame=109,
            )
        _, legacy = self.run_case(max_calls=4)
        self.assertIsNone(legacy["observation_frame"])
        self.assertFalse(legacy["post_observation_trial"])
        self.assertEqual(legacy["post_observation_removed_runs"], 0)

    def test_unexecuted_native_never_counts_as_reproduced(self):
        receipt = dict(
            schema=tool.SCHEMA, candidate_sha256="d" * 64,
            source_sha="a" * 40, original_rom_sha256="b" * 64,
            native_binary_sha256="c" * 64, reference_engine="snes9x",
            discrepancy_id="zoo", semantic_phase="source+5040",
            original_valid=False, native_valid=False,
            native_executed=False, native_skip_reason="original_stage_invalid",
            result="invalid_route")
        tool.verify_receipt(receipt, "d" * 64)
        receipt["native_valid"] = True
        with self.assertRaisesRegex(ValueError, "unexecuted native"):
            tool.verify_receipt(receipt, "d" * 64)
        receipt["native_valid"] = False
        receipt["result"] = "reproduced"
        with self.assertRaisesRegex(ValueError, "unexecuted native"):
            tool.verify_receipt(receipt, "d" * 64)
        receipt["result"] = "invalid_route"
        receipt["native_skip_reason"] = "invented"
        with self.assertRaisesRegex(ValueError, "unexecuted native"):
            tool.verify_receipt(receipt, "d" * 64)
        receipt["native_executed"] = True
        receipt["native_skip_reason"] = "original_stage_invalid"
        with self.assertRaisesRegex(ValueError, "executed native"):
            tool.verify_receipt(receipt, "d" * 64)

    def test_exact_candidate_mismatch_aborts(self):
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            self.run_case(["--bad-hash"])

    def test_unqualified_original_cannot_seed_reducer(self):
        with self.assertRaisesRegex(ValueError, "does not reproduce"):
            self.run_case(["--invalid-original"])

    def test_cli_observation_frame_bounded_tail(self):
        import subprocess
        output = self.root / "tail-minimal.script"
        report = self.root / "tail-minimal.json"
        subprocess.run([
            sys.executable, str(ROOT / "tools" / "reduce_controller_fixture.py"),
            "--input", str(self.fixture), "--output", str(output),
            "--report", str(report), "--protected-before-frame", "100",
            "--observation-frame", "110", "--max-calls", "4",
            "--oracle", sys.executable, str(self.oracle),
        ], check=True, capture_output=True, text=True, timeout=30)
        self.assertEqual(output.read_bytes(), b"0:100:001\n100:10:002\n")
        self.assertEqual(json.loads(report.read_text())["post_observation_removed_runs"], 2)

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

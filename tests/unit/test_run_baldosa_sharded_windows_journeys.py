"""Synthetic contracts for the two-VM Windows source-bound acceptance pilot."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_baldosa_sharded_windows_journeys as f

SHA = "a" * 40
EXE_HASH, FIXTURE_HASH, ZIP_HASH = ("1" * 64, "2" * 64, "3" * 64)


def receipt(shard):
    indices = list(f.EXPECTED[shard])
    return f.signed({
        "schema": f.SCHEMA,
        "shard": shard, "source_sha": SHA,
        "exe_sha256": EXE_HASH, "fixture_sha256": FIXTURE_HASH,
        "zip_sha256": ZIP_HASH,
        "expected_cases": indices, "observed_cases": indices,
        "missing_cases": [],
        "cases": [
            {"index": i, "name": f.original.STEPS[i],
             "exit_code": 0, "elapsed_seconds": 2.0, "error": None}
            for i in indices
        ],
        "launcher_verified": True if shard == "independent" else None,
        "elapsed_seconds": 20.0,
        "disposition": "produced_not_independently_adjudicated",
        "release_gate_credit": 0,
        "physical_hardware_verified": False,
    })


def populate(root):
    for shard in f.EXPECTED:
        path = root / ("fanout-win32-" + shard)
        path.mkdir()
        (path / "result.json").write_text(
            json.dumps(receipt(shard)), encoding="utf-8"
        )


class WindowsTwoVMFanoutContracts(unittest.TestCase):
    def test_whole_source_population_is_fixed_and_disjoint(self):
        self.assertEqual(f.EXPECTED["baseline-records"], (0, 1, 2))
        self.assertEqual(f.EXPECTED["independent"], tuple(range(3, 11)))
        self.assertEqual(
            sorted(i for indices in f.EXPECTED.values() for i in indices),
            list(range(len(f.original.STEPS)))
        )
        self.assertIn("Real stock 1P result", f.original.STEPS[1])
        self.assertIn("Real named P1/P2 ordinary race", f.original.STEPS[2])
        self.assertIn("Native shared Quick Practice", f.original.STEPS[7])
        source = f.original.WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(len(f.original.extract_commands(source)), 11)

    def test_valid_two_shard_aggregate_is_research_transport_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            populate(root)
            r = f.validate_shards(root, SHA)
            self.assertEqual(r["executed_cases"], 11)
            self.assertEqual(r["expected_cases"], 11)
            self.assertEqual(r["exe_sha256"], EXE_HASH)
            self.assertEqual(r["zip_sha256"], ZIP_HASH)
            self.assertEqual(r["release_gate_credit"], 0)
            self.assertFalse(r["physical_hardware_verified"])
            self.assertEqual(r["disposition"],
                             "produced_not_independently_adjudicated")

    def test_missing_duplicate_tampered_incomplete_and_false_credit_fail(self):
        alterations = ("missing", "additional", "tampered", "source",
                       "binary", "receipt", "cases", "missing-case", "failure",
                       "launcher", "credit", "hardware", "disposition")
        for change in alterations:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                populate(root)
                path = root / "fanout-win32-independent/result.json"
                row = json.loads(path.read_text(encoding="utf-8"))
                if change == "missing":
                    path.unlink()
                elif change == "additional":
                    (root / "fanout-win32-unknown").mkdir()
                else:
                    if change == "tampered":
                        row["cases"][0]["exit_code"] = 123
                    if change == "source":
                        row["source_sha"] = "b" * 40
                    if change == "binary":
                        row["zip_sha256"] = "c" * 64
                    if change == "receipt":
                        row["receipt_sha256"] = "0" * 64
                    if change == "cases":
                        row["observed_cases"][0] = 3
                    if change == "missing-case":
                        row["cases"].pop()
                    if change == "failure":
                        row["cases"][0]["exit_code"] = 1
                    if change == "launcher":
                        row["launcher_verified"] = False
                    if change == "credit":
                        row["release_gate_credit"] = 1
                    if change == "hardware":
                        row["physical_hardware_verified"] = True
                    if change == "disposition":
                        row["disposition"] = "completed_positive"
                    if change not in ("receipt", "tampered"):
                        row = f.signed(row)
                    path.write_text(json.dumps(row), encoding="utf-8")
                with self.assertRaises(ValueError):
                    f.validate_shards(root, SHA)

    def test_source_bound_bundle_refuses_wrong_missing_or_replaced_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bundle = root / "bundle"
            bundle.mkdir()
            items = {"UniracersSNESRecomp.exe": b"exe-real",
                     "ur-baldosa-modern-profile-fixture.exe": b"fixture-real",
                     f.PREFIX: b"fake zip only in synthetic unit"}
            for key, value in items.items():
                (bundle / key).write_bytes(value)
            (bundle / "source-commit.txt").write_text(SHA + "\n")
            hashes = {k: f.checksum(bundle / k) for k in items}
            (bundle / "SHA256SUMS").write_text(
                "".join(v + "  " + k + "\n" for k, v in hashes.items())
            )
            with mock.patch.object(f.binding, "bind", return_value={
                    "journey_and_packaged_executable_sha256": hashes["UniracersSNESRecomp.exe"],
                    "zip_sha256": hashes[f.PREFIX]
            }):
                self.assertEqual(f.inspect_bundle(bundle, SHA, root), hashes)
                (bundle / "UniracersSNESRecomp.exe").write_bytes(b"modified!")
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    f.inspect_bundle(bundle, SHA, root)
                (bundle / "UniracersSNESRecomp.exe").write_bytes(items["UniracersSNESRecomp.exe"])
                (bundle / "source-commit.txt").write_text("b" * 40)
                with self.assertRaisesRegex(ValueError, "source revision"):
                    f.inspect_bundle(bundle, SHA, root)

    def test_workflow_candidate_only_is_strictly_opt_in(self):
        native = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        pilot = (ROOT / ".github/workflows/baldosa-windows-fanout-pilot.yml").read_text()
        self.assertIn("candidate_only: true", pilot)
        self.assertIn("export_campaign_inputs: true", pilot)
        self.assertIn("max-parallel: 2", pilot)
        self.assertIn("shard: [baseline-records, independent]", pilot)
        self.assertIn("pattern: fanout-win32-*", pilot)
        self.assertNotIn("\n  schedule:", pilot)
        self.assertNotIn("\n  push:", pilot)
        self.assertEqual(native.count(
            "github.event_name != 'pull_request' && inputs.parallel_journeys != true && inputs.candidate_only != true"
        ), len(f.original.STEPS))
        self.assertIn("inputs.candidate_only != true", native)
        self.assertIn("inputs.export_campaign_inputs == true", native)
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
            self.assertIn("name: " + artifact, native)


if __name__ == "__main__":
    unittest.main()

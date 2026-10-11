"""Synthetic QA-02/03 recovery batch transport tests, not OS-process witnesses."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_recovery_campaign as c  # noqa: E402

SHA = "a" * 40
SEED = 20261011


class RecoveryCohortContractTests(unittest.TestCase):
    def test_campaign_reuses_original_production_source_and_checks_all_five_cases(self):
        sources = c.existing_sources()
        self.assertIn("completed_run_store.cpp", sources)
        self.assertIn("local_tournament_session_coordinator.cpp", sources)
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(set(c.IMPLEMENTATIONS), set(c.SUITES))
        self.assertEqual(len(c.SUITES), 5)
        self.assertIn("hardkill-owner", c.SUITES)
        self.assertIn("c16-storage-outage", c.SUITES)

    def _populate(self, dest: Path):
        exe = dest / "compiled-fixture"
        exe.write_bytes(b"exact-boundary-fixture-dummy-do-not-run")
        digest = c.digest(exe)
        receipts = dest / "receipts"
        receipts.mkdir()
        with mock.patch.dict(c.IMPLEMENTATIONS, {
                case: lambda binary, root, jitter: None for case in c.SUITES
        }):
            for index, case in enumerate(c.SUITES):
                result = c.run_suite(
                    exe=exe, source_sha=SHA, binary_sha256=digest,
                    suite=case, iterations=10, seed=SEED + index * 1009,
                    work=dest / f"work-{index}")
                output = receipts / f"qa02-recovery-{case}" / "result.json"
                c.save(output, result)
        return exe, digest, receipts

    def test_all_five_shards_and_fifty_real_process_contract_slots_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, binary_hash, receipts = self._populate(root)
            report = c.aggregate(receipts, SHA, binary_hash, 10, SEED)
            self.assertEqual(report["disposition"], "completed_positive")
            self.assertEqual(report["completed_suite_count"], 5)
            self.assertEqual(report["requested_iterations"], 50)
            self.assertEqual(report["observed_iterations"], 50)
            self.assertEqual(report["passed_iterations"], 50)
            self.assertEqual(report["release_gate_credit"], 0)
            self.assertFalse(report["actual_guest_gameplay_covered"])
            self.assertFalse(report["physical_hardware_covered"])
            self.assertIn("not a shipped Windows ZIP", report["scope"])

    def test_corruption_missingness_and_false_release_credit_fail_closed(self):
        for bad in ("missing", "digest", "binary", "seed", "credit", "count",
                    "claim", "unexpected"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _, binary_hash, receipts = self._populate(root)
                target = receipts / "qa02-recovery-c16-storage-outage" / "result.json"
                if bad == "missing":
                    target.unlink()
                elif bad == "unexpected":
                    (receipts / "qa02-recovery-ghost-cohort").mkdir()
                else:
                    row = json.loads(target.read_text())
                    if bad == "digest":
                        row["receipt_sha256"] = "0" * 64
                    elif bad == "binary":
                        row["binary_sha256"] = "b" * 64
                    elif bad == "seed":
                        row["seed"] += 1
                    elif bad == "credit":
                        row["release_gate_credit"] = 1
                    elif bad == "count":
                        row["passed_iterations"] = 11
                    elif bad == "claim":
                        row["actual_guest_gameplay_covered"] = True
                    if bad != "digest":
                        unsigned = {k: v for k, v in row.items()
                                    if k != "receipt_sha256"}
                        row["receipt_sha256"] = c.json_hash(unsigned)
                    c.save(target, row)
                report = c.aggregate(receipts, SHA, binary_hash, 10, SEED)
                self.assertNotEqual(report["disposition"], "completed_positive")
                self.assertTrue(report["issues"])
                self.assertEqual(report["release_gate_credit"], 0)

    def test_three_failures_stops_early_but_retains_bounded_failure_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "producer"
            exe.write_bytes(b"test-only-executable-identity")
            def fail(_exe, _root, _jitter):
                raise c.TrialError("real process failed safe-store assertion")
            with mock.patch.dict(c.IMPLEMENTATIONS, {"c09-orphan": fail}):
                result = c.run_suite(
                    exe=exe, source_sha=SHA, binary_sha256=c.digest(exe),
                    suite="c09-orphan", iterations=100, seed=SEED,
                    work=root / "work")
            self.assertEqual(result["disposition"], "invariant_violation")
            self.assertEqual(result["attempted_iterations"], 3)
            self.assertEqual(result["failed_iterations"], 3)
            self.assertEqual(result["passed_iterations"], 0)
            self.assertEqual(len(result["failures"]), 3)
            self.assertEqual(result["release_gate_credit"], 0)

    def test_explicit_bounds_and_no_stale_or_symlink_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "bin"
            binary.write_bytes(b"dummy")
            with self.assertRaisesRegex(ValueError, "stale"):
                c.run_suite(exe=binary, source_sha=SHA, binary_sha256="b"*64,
                            suite="c09-orphan", iterations=10, seed=SEED,
                            work=root / "run")
            with self.assertRaisesRegex(ValueError, "unbounded"):
                c.run_suite(exe=binary, source_sha=SHA,
                            binary_sha256=c.digest(binary),
                            suite="c09-orphan", iterations=501, seed=SEED,
                            work=root / "run")
            with self.assertRaisesRegex(ValueError, "refuse"):
                c.build(binary)

    def test_manual_only_workflow_and_read_only_release_boundaries(self):
        wf = (ROOT / ".github/workflows/qa02-recovery-cohort.yml").read_text()
        self.assertIn("workflow_dispatch:", wf)
        self.assertNotIn(chr(92) + "${{", wf)
        self.assertIn("group: qa02-process-recovery-cohort-${{ github.ref }}", wf)
        self.assertIn("binary_sha256: ${{ steps.digest.outputs.binary_sha256 }}", wf)
        self.assertNotIn("\n  push:", wf)
        self.assertNotIn("\n  pull_request:", wf)
        self.assertNotIn("schedule:", wf)
        self.assertIn("cancel-in-progress: false", wf)
        self.assertIn("max-parallel: 2", wf)
        self.assertIn("timeout-minutes: 240", wf)
        for case in c.SUITES:
            self.assertIn(f"suite: {case}", wf)
        self.assertIn("qa02_recovery_campaign.py build", wf)
        self.assertIn("qa02_recovery_campaign.py run", wf)
        self.assertIn("qa02_recovery_campaign.py aggregate", wf)
        self.assertIn("if: always()", wf)
        self.assertIn("name: qa02-store-fixture-shared-binary", wf)
        self.assertNotIn("qa02-recovery-shared-binary", wf)
        self.assertIn("pattern: qa02-recovery-*", wf)
        self.assertNotIn("recovery-work/trial-", wf)  # no real private roots uploaded
        self.assertIn("release_gate_credit", (ROOT / "tools/qa02_recovery_campaign.py").read_text())


if __name__ == "__main__":
    unittest.main()

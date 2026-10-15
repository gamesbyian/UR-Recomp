"""Synthetic contracts for Windows Baldosa reliability batches, never a gameplay pass."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_baldosa_windows_reliability_batch as c

SOURCE = "a" * 40
IDENTITY = dict(source_commit=SOURCE, exe_sha256="b"*64,
                fixture_sha256="c"*64, archive_sha256="d"*64,
                rom_sha256=c.ROM_SHA, script_sha256="e"*64)


def populate(dest: Path, trials: int = 1) -> Path:
    receipts = dest / "receipts"
    receipts.mkdir()
    # A successfully completed real producer owns/creates its trial root.
    # Mock that contract so cleanup is tested rather than treating a fake
    # nonexistent directory as an actual failed Windows process.
    def simulated_success(*args):
        args[6].mkdir()
    with mock.patch.object(c, "identity_for", return_value=dict(IDENTITY)), \
         mock.patch.object(c, "run_one", side_effect=simulated_success) as runner:
        for shard in c.SHARDS:
            row = c.run_shard(
                source_sha=SOURCE, shard=shard, trials=trials,
                exe=dest/"exe", fixture=dest/"fixture", archive=dest/"zip",
                rom=dest/"rom", script=dest/"script", work=dest/f"work-{shard}")
            c.save(receipts / f"qa-win32-batch-{shard}/result.json", row)
        assert runner.call_count == 4 * trials
    return receipts


class WindowsBatchTests(unittest.TestCase):
    def test_four_real_producer_cohorts_required(self):
        with tempfile.TemporaryDirectory() as folder:
            receipts = populate(Path(folder), 3)
            data = c.aggregate(receipts, SOURCE, 3)
            self.assertEqual(data["disposition"], "completed_positive")
            self.assertEqual(data["requested_trials"], 12)
            self.assertEqual(data["passed_trials"], 12)
            self.assertEqual(data["input_identity"], IDENTITY)
            self.assertEqual(data["release_gate_credit"], 0)
            self.assertFalse(data["independent_original_native_oracle"])
            self.assertFalse(data["physical_hardware_witness"])
            self.assertFalse(data["integrated_complete_1p_2p_event_certified"])

    def test_long_running_windows_populations_stay_bounded_and_receipted(self):
        wf = (ROOT/".github/workflows/baldosa-windows-reliability-campaign.yml").read_text()
        self.assertIn('options: ["1", "3", "10", "30", "60"]', wf)
        self.assertEqual(c.TRIAL_POPULATIONS, (1, 3, 10, 30, 60))
        self.assertIn("timeout-minutes: 240", wf)
        for trials in (30, 60):
            with self.subTest(trials=trials), tempfile.TemporaryDirectory() as folder:
                receipts = populate(Path(folder), trials)
                result = c.aggregate(receipts, SOURCE, trials)
                self.assertEqual(result["disposition"], "completed_positive")
                self.assertEqual(result["passed_trials"], 4 * trials)
                self.assertEqual(result["requested_trials"], 4 * trials)
                self.assertEqual(result["observed_shards"], 4)
                self.assertEqual(result["release_gate_credit"], 0)
                for row in result["shards"]:
                    self.assertEqual(row["expected_trials"], trials)
                    self.assertEqual(row["attempted_trials"], trials)
                    self.assertEqual(row["failed_trials"], 0)
        for invalid in (0, 2, 20, 61, 100, 500):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    c.aggregate(Path("unused"), SOURCE, invalid)

    def test_fail_closed_on_missing_altered_extra_and_false_claims(self):
        for kind in ("missing", "extra", "receipt_hash", "source",
                     "candidate", "credit", "count", "status", "hardware"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                receipts = populate(Path(folder))
                target = receipts / "qa-win32-batch-guest-1/result.json"
                if kind == "missing":
                    target.unlink()
                elif kind == "extra":
                    (receipts / "qa-win32-batch-guest-2").mkdir()
                else:
                    data = json.loads(target.read_text())
                    if kind == "receipt_hash": data["receipt_sha256"] = "0"*64
                    elif kind == "source": data["identity"]["source_commit"] = "f"*40
                    elif kind == "candidate": data["identity"]["exe_sha256"] = "f"*64
                    elif kind == "credit": data["release_gate_credit"] = 1
                    elif kind == "count": data["passed_trials"] = 2
                    elif kind == "status": data["disposition"] = "invariant_violation"
                    elif kind == "hardware": data["physical_hardware_witness"] = True
                    if kind != "receipt_hash":
                        unsigned = {k:v for k,v in data.items() if k != "receipt_sha256"}
                        data["receipt_sha256"] = c.hash_object(unsigned)
                    c.save(target, data)
                aggregate = c.aggregate(receipts, SOURCE, 1)
                self.assertEqual(aggregate["disposition"], "incomplete_or_failed")
                self.assertTrue(aggregate["issues"])
                self.assertEqual(aggregate["release_gate_credit"], 0)

    def test_stop_at_second_failure_without_claiming_full_population(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def fail(*args):
                raise RuntimeError("native CRC mismatch")
            with mock.patch.object(c, "identity_for", return_value=dict(IDENTITY)), \
                 mock.patch.object(c, "run_one", side_effect=fail):
                result = c.run_shard(
                    source_sha=SOURCE, shard="guest-0", trials=10,
                    exe=root/"exe", fixture=root/"fixture", archive=root/"zip",
                    rom=root/"rom", script=root/"script", work=root/"work")
            self.assertEqual(result["attempted_trials"], 2)
            self.assertEqual(result["failed_trials"], 2)
            self.assertEqual(result["disposition"], "invariant_violation")

    def test_existing_guest_validator_keeps_fidelity_and_recovery_guards(self):
        good = {k:True for k in c.GUEST_FLAGS}
        good.update(classification="windows_native_pause_and_named_profile_smoke_only",
                    rom_sha256=c.ROM_SHA, exe_sha256=IDENTITY["exe_sha256"],
                    script_sha256=IDENTITY["script_sha256"], video_driver="windows",
                    guest_frames=2473, course_complete_credit=0,
                    modern_frontend_connected=False, packaged_windows_product=False,
                    physical_gamepad_hardware_tested=False)
        for field in ("native_real_named_modern_profile_boot",
                      "native_existing_modern_profile_fresh_process",
                      "native_two_named_profile_isolation",
                      "modern_root_race_entry_p1", "modern_root_race_entry_p2"):
            good[field] = {"observed": True}
        c.validate_producer("guest", good, IDENTITY)
        for field in ("native_same_boundary_restart_restored",
                      "native_two_named_profile_isolation",
                      "guest_frames", "course_complete_credit"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                c.validate_producer("guest", {**good, field:None}, IDENTITY)

    def test_romless_launcher_requires_real_security_observations(self):
        good = {k:True for k in c.LAUNCHER_FLAGS}
        good["archive_sha256"] = IDENTITY["archive_sha256"]
        c.validate_producer("launcher", good, IDENTITY)
        for field in ("external_junction_to_package_rejected",
                      "rejected_profile_save_unchanged", "native_root_drawn"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                c.validate_producer("launcher", {**good,field:False}, IDENTITY)
        with self.assertRaises(ValueError):
            c.validate_producer("launcher", {**good,"release_gate_credit":1}, IDENTITY)

    def test_manual_cohort_calls_single_existing_windows_build(self):
        wf = (ROOT/".github/workflows/baldosa-windows-reliability-campaign.yml").read_text()
        bridge = (ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertIn("workflow_dispatch:",wf)
        self.assertNotIn("\n  pull_request:",wf)
        self.assertNotIn("\n  push:",wf)
        self.assertNotIn("schedule:",wf)
        self.assertIn("max-parallel: ${{ fromJSON(inputs.max_parallel || '2') }}", wf)
        self.assertIn('options: ["1", "2", "4"]', wf)
        self.assertIn('default: "2"', wf)
        self.assertEqual(wf.count("max_parallel:"), 2)
        self.assertIn("matrix:\n        shard: [guest-0, guest-1, launcher-0, launcher-1]", wf)
        self.assertIn("timeout-minutes: 240",wf)
        self.assertIn("export_campaign_inputs: true",wf)
        self.assertIn("uses: ./.github/workflows/baldosa-windows-native-bridge.yml",wf)
        self.assertIn("workflow_call:",bridge)
        self.assertIn("inputs.export_campaign_inputs == true",bridge)
        self.assertIn("name: qa-baldosa-native-export",bridge)
        self.assertNotIn(chr(92)+chr(36)+"{{",wf)
        self.assertNotIn(chr(92)+chr(36)+"{{",bridge)
        for shard in c.SHARDS:self.assertIn(shard,wf)
        self.assertIn("qa_baldosa_windows_reliability_batch.py run",wf)
        self.assertIn("qa_baldosa_windows_reliability_batch.py aggregate",wf)
        self.assertNotIn("win32-private-work/trial",wf)


if __name__=="__main__":
    unittest.main()

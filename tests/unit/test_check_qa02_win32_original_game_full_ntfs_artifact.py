#!/usr/bin/env python3
"""ROM-free negative tests for exact original Windows game-on-full-NTFS receipts."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_original_game_full_ntfs_artifact.py"
spec = importlib.util.spec_from_file_location("qa02_diskfull_game", SCRIPT)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

QA = "a" * 64
OLD = hashlib.sha256(b"eight kib original").hexdigest()
NEW = hashlib.sha256(b"fresh new guest state").hexdigest()


def good_fixture():
    osr = {
        "schema": "UR-QA02-REAL-WIN32-ISOLATED-NTFS-DISKFULL-PREFLIGHT/1",
        "source_revision": QA, "VHDX_isolated_NTFS": True,
        "actual_Win32_disk_full_observed": True,
        "real_original_8192_bytes_preserved": True,
        "native_game_tested": True,
        "native_game_receipt_is_independent_stage_file": True,
        "game_ROM_used_in_ephemeral_runner": True,
        "user_ROM_or_player_data_used": True,
        "private_player_save_uploaded": False,
        "genuine_second_process_ERROR_DISK_FULL": 112,
        "recovered_new_write_bytes": 8192, "capacity_megabytes": 128,
        "original_free_bytes": 118000000, "accepted_filler_bytes": 104000000,
        "checker_sha256": "b" * 64,
        "power_loss_or_partial_IO_tested": False,
        "physical_operator": False, "release_gate_credit": 0,
    }
    files = {qa.OS: osr}
    for stage, exit_code in (("baseline", 0), ("full", 8), ("restored", 0)):
        files[qa.PREFIX + stage + "-result.json"] = {
            "schema": "UR-QA02-ORIGINAL-PACKAGED-GAME-REAL-NTFS-FULL/1",
            "stage": stage, "tested_product_pr_merge": qa.GAME_SOURCE,
            "tested_PE_SHA256": qa.PE, "tested_CMD_SHA256": qa.CMD,
            "route_SHA256": qa.ROUTE,
            "native_launcher_WindowsPowerShell_modules_normalized": True,
            "tested_demand_for_fresh_sram_allocation": True,
            "timeout": False, "human_hardware_or_power_cut": False,
            "release_gate_credit": 0, "result": "bounded_pass",
            "failure": "", "stdout_SHA256": "c" * 64,
            "stderr_SHA256": "d" * 64,
            "Windows_process_exit": exit_code,
            "original_launcher_bounded_markers": [
                "first frame simulated", *(
                    ["UR-BALDOSA-SAVE-FAILED"] if stage == "full" else []
                )],
            "original_preserved_sram_sha256":
                "" if stage == "restored" else OLD,
            "canonical_receipts":
                ([{"path": "saves/save.srm", "bytes": 8192, "sha256": NEW}]
                 if stage == "restored" else []),
        }
    return files


class OriginalGameOnGenuineDiskFull(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.path = Path(self.root.name) / "source.zip"
        self.records = good_fixture()

    def pack(self, data):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, obj in data.items():
                z.writestr(name, json.dumps(obj).encode("utf-8"))
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_synthetic_contract_passes_with_zero_gate(self):
        h = self.pack(self.records)
        d = qa.validate(self.path, h, QA)
        self.assertTrue(d["native_new_save_allocation_refused_with_exit8"])
        self.assertEqual(d["release_gate_credit"], 0)
        self.assertFalse(d["named_typed_transaction_tested"])

    def test_real_full_failure_and_source_binding_fail_closed(self):
        mutations = (
            (qa.OS, "genuine_second_process_ERROR_DISK_FULL", 5),
            (qa.OS, "native_game_tested", False),
            (qa.OS, "game_ROM_used_in_ephemeral_runner", False),
            (qa.OS, "source_revision", "c" * 64),
            (qa.PREFIX + "full-result.json", "Windows_process_exit", 0),
            (qa.PREFIX + "full-result.json", "original_preserved_sram_sha256", "d" * 64),
            (qa.PREFIX + "full-result.json", "canonical_receipts",
             [{"path": "saves/save.srm", "bytes": 8192, "sha256": OLD}]),
            (qa.PREFIX + "full-result.json", "tested_PE_SHA256", "e" * 64),
            (qa.PREFIX + "restored-result.json", "timeout", True),
            (qa.PREFIX + "restored-result.json", "release_gate_credit", 1),
        )
        for member, field, bad in mutations:
            with self.subTest(member=member, field=field):
                copy = json.loads(json.dumps(self.records))
                copy[member][field] = bad
                with self.assertRaises(ValueError):
                    qa.validate(self.path, self.pack(copy), QA)

    def test_bad_external_hash_missing_member_and_extra_rom(self):
        correct = self.pack(self.records)
        with self.assertRaises(ValueError):
            qa.validate(self.path, "f" * 64, QA)
        with self.assertRaises(ValueError):
            qa.validate(self.path, correct, "c" * 64)
        for broken in (
            {k: v for k, v in self.records.items() if "restored" not in k},
            {**self.records, "Uniracers_USA.sfc": {"payload": "ROM"}},
        ):
            with self.assertRaises(ValueError):
                qa.validate(self.path, self.pack(broken), QA)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Synthetic ROM-free positive and adversarial tests for the independent reader.

These fixtures do not represent executed Windows game evidence.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_named_full_ntfs_original.py"
spec = importlib.util.spec_from_file_location("qa02_full_named", SOURCE)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

PRODUCT = "a" * 40
CMD = "b" * 64
FIXTURE = "c" * 64
ROM = "d" * 64
RAW = bytes((i * 17 + 9) % 256 for i in range(8192))
TYPED = (b"UR-HOST-PROFILE/5\nprofile=native-ci-rider\nstock_sram=" +
         RAW.hex().encode() + b"\n")
DATA = {
    "raw": RAW,
    "typed": TYPED,
    "selector": b"UR-HOST-STATE/6\nprofile=native-ci-rider\n",
    "catalog": b"UR-PROFILE-CATALOG/1\nnative-ci-rider|Tester\n",
}


def fixture():
    files = {}
    receipts = {}
    for stage in qa.STAGES:
        for kind, original in DATA.items():
            member = f"{stage}.{kind}.bin"
            files["source-bytes/" + member] = original
            receipts[member] = {
                "bytes": len(original), "sha256": qa.sha(original),
            }
    files["candidate.json"] = {
        "cmd_sha256": CMD, "fixture_sha256": FIXTURE,
        "seed_sha256": "e" * 64, "original_rom_sha256": ROM,
        "base": {
            k: {"sha256": qa.sha(v), "bytes": len(v)}
            for k, v in DATA.items()
        },
    }
    files["real-ntfs-substrate.json"] = {
        "schema": "ur-product-source-real-win32-ntfs-diskfull-substrate/1",
        "actual_ephemeral_ntfs_vhdx": True,
        "original_source_warm_boot_completed_before_fill": True,
        "original_free_bytes": 118000000,
        "accepted_filler_bytes": 104000000,
        "fresh_process_os_error": 112,
        "capacity_megabytes": 128,
        "tested_commit": PRODUCT,
        "product_not_release_qa": True,
        "power_loss_or_short_write": False,
        "release_gate_credit": 0,
    }
    files["full-process.json"] = {
        "native_cmd_exit": 8,
        "full_original_raw_sha256": qa.sha(RAW),
        "before_raw_sha256": qa.sha(RAW),
        "original_full_ntfs_cmd_sha256": CMD,
        "original_guest_save_message": True,
        "original_game_race_armed": True,
        "canonical_equal_before_after": True,
        "qa_gate_credit": 0,
    }
    files["result.json"] = {
        "schema": "ur-real-original-cmd-ntfs-disk-full/1",
        "actual_isolated_vhd_ntfs_full": True,
        "actual_native_cmd_exit8_during_original_guest_save": True,
        "exact_before_full_two_cold_binary_members": receipts,
        "original_cmd_sha256": CMD,
        "original_fixture_sha256": FIXTURE,
        "human_operator": False,
        "real_power_loss_or_partial_write": False,
        "release_gate_credit": 0,
    }
    files["fixture.log"] = b"original native fixture test, no personal data"
    files["warm.log"] = (
        b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider\n")
    files["full-ntfs-original-CMD.log"] = (
        b"UR_BALDOSA_NATIVE_PAUSE ARMED guest=2200\n"
        b"UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1\n"
        b"UR-BALDOSA-SAVE-FAILED: cannot complete\n")
    for idx in (1, 2):
        files[f"cold-{idx}.log"] = (
            b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider\n")
    return files


class OriginalNamedFullNtfs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "actions-original.zip"
        self.original = fixture()

    def pack(self, files):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as z:
            for path, value in sorted(files.items()):
                if isinstance(value, dict):
                    value = (json.dumps(value, sort_keys=True) + "\n").encode()
                z.writestr(path, value)
        return qa.sha(self.path.read_bytes())

    def test_synthetic_positive_proves_bounded_zero_gate(self):
        external = self.pack(self.original)
        x = qa.audit(self.path, external, PRODUCT, CMD, FIXTURE, ROM)
        self.assertEqual(x["verified_canonical_source_objects"], 16)
        self.assertEqual(x["genuine_second_process_OS_error"], 112)
        self.assertEqual(x["release_gate_credit"], 0)
        self.assertFalse(x["physical_owner_or_power_loss_accepted"])
        self.assertFalse(x["complete_named_typed_CAS_storage_faults_accepted"])

    def test_mutations_fail_closed_even_with_recomputed_wrapper_sha(self):
        corruptions = (
            ("source-bytes/actual-full.raw.bin", b"x" * 8192),
            ("source-bytes/cold2.typed.bin", b"fake"),
            ("source-bytes/before.selector.bin", b"wrong"),
            ("warm.log", b"bogus"),
            ("full-ntfs-original-CMD.log", b"success, not failed"),
            ("cold-2.log", b"startup rejected"),
            ("real-ntfs-substrate.json", {"fresh_process_os_error": 5}),
            ("full-process.json", {"native_cmd_exit": 0}),
            ("result.json", {"release_gate_credit": 1}),
            ("candidate.json", {"cmd_sha256": "0" * 64}),
        )
        for name, corrupted in corruptions:
            with self.subTest(name=name):
                files = fixture()
                if isinstance(corrupted, dict):
                    files[name] = {**files[name], **corrupted}
                else:
                    files[name] = corrupted
                original_sha = self.pack(files)
                with self.assertRaises((ValueError, KeyError)):
                    qa.audit(self.path, original_sha, PRODUCT, CMD, FIXTURE, ROM)

    def test_missing_member_extra_rom_and_incorrect_external_hash(self):
        digest = self.pack(self.original)
        with self.assertRaises(ValueError):
            qa.audit(self.path, "f" * 64, PRODUCT, CMD, FIXTURE, ROM)
        with self.assertRaises(ValueError):
            qa.audit(self.path, digest, "f" * 64, CMD, FIXTURE, ROM)
        for files in (
            {k: v for k, v in self.original.items() if k != "cold-2.log"},
            {**self.original, "Uniracers_USA.sfc": b"ROM"},
        ):
            with self.assertRaises(ValueError):
                qa.audit(self.path, self.pack(files), PRODUCT, CMD, FIXTURE, ROM)


if __name__ == "__main__":
    unittest.main()

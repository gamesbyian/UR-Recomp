#!/usr/bin/env python3
"""Adversarial ROM-free tests for independently pinned original Windows S refusal."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
def load(label: str, filename: Path):
    spec = importlib.util.spec_from_file_location(label, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

qa = load("qa02_invalid_s", ROOT / "tools/check_qa02_win32_invalid_s_original.py")
positive_s = load("qa02_s_fixture", ROOT /
                  "tests/unit/test_check_qa02_win32_interactive_s_original.py")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fixture():
    original, cmd = positive_s.make_fixture()
    before = {
        label: original["source-bytes/before-S." + label + ".bin"]
        for label in qa.LABELS
    }
    files = {}
    receipts = {}
    for stage in qa.STAGES:
        for label, data in before.items():
            name = f"{stage}.{label}.bin"
            files["source-bytes/" + name] = data
            receipts[name] = {"bytes": len(data), "sha256": sha(data)}
    original_c = original["source-bytes/unrelated-C-original-typed.bin"]
    files["source-bytes/unrelated-C-original-typed.bin"] = original_c
    receipts["unrelated-C-original-typed.bin"] = {
        "bytes": len(original_c), "sha256": sha(original_c)}
    report = {
        "schema": "ur-win32-interactive-original-cmd-invalid-s/1",
        "exact_original_extracted_cmd_sha256": cmd,
        "invalid_requested_profile": "native-ci-no-such-racer",
        "real_win32_console_keys": ["S", "literal target+Enter", "cold Q"],
        "no_canonical_data_mutated": True,
        "refusal_before_any_guest_frame": True,
        "second_original_cold_process_rejected_damaged_A_exit_7": True,
        "unrelated_C_typed_remained_absent": True,
        "human_operator": False, "release_gate_credit": 0,
        "source_bytes_sha256": receipts,
    }
    files["invalid-S-result.json"] = (
        json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    files["fixture.log"] = (
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE A\n"
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE B\n"
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE C\n")
    files["invalid-S.log"] = (
        b"UR-BALDOSA-STARTUP-PROFILE-REJECTED: No guest\n"
        b"Explicit recovery choice [R/T/S/Q]: S\n"
        b"Healthy registered profile ID: "
        b"UR_BALDOSA_RECOVERY_CHOICE choice=healthy status=3 "
        b"active_profile=native-ci-rider "
        b"next_profile=native-ci-no-such-racer completed=0\n"
        b"UR-BALDOSA-RECOVERY-REFUSED: No automatic replacement was made.\n")
    files["cold-Q-after-invalid-S.log"] = (
        b"UR-BALDOSA-STARTUP-PROFILE-REJECTED: Still damaged\n"
        b"Explicit recovery choice [R/T/S/Q]: Q\n")
    for name in ("invalid-S-key.injection.log",
                 "invalid-S-profile.injection.log",
                 "cold-Q-key.injection.log"):
        files[name] = b"exit=0\r\n\r\n"
    return files, cmd


class TestOriginalInvalidS(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "original.zip"
        self.files, self.cmd = fixture()

    def pack(self, data):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as output:
            for name, value in data.items():
                output.writestr(name, value)
        return sha(self.path.read_bytes())

    def test_synthetic_good_contract_grants_zero_gate(self):
        digest = self.pack(self.files)
        result = qa.audit(self.path, digest, self.cmd)
        self.assertEqual(result["canonical_before_refused_cold_files_byte_identical"], 21)
        self.assertEqual(result["original_binary_sha_and_length_receipts"], 22)
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertFalse(result["physical_human_operator_tested"])

    def test_all_adversarial_missing_changed_or_forged_evidence_fails_closed(self):
        mutations = {
            "mutated A": ("source-bytes/after-invalid-S.a-raw.bin", b"x" * 8192),
            "changed B": ("source-bytes/cold-Q-after-invalid-S.b-typed.bin", b"bad"),
            "changed selector": ("source-bytes/after-invalid-S.selector.bin", b"bad"),
            "false C archive": ("source-bytes/unrelated-C-original-typed.bin", b"bad"),
            "missing member": ("source-bytes/cold-Q-after-invalid-S.c-raw.bin", None),
            "extra ROM": ("game.sfc", b"ROM"),
            "failed S input": ("invalid-S-key.injection.log", b"exit=1\n"),
            "failed text input": ("invalid-S-profile.injection.log", b"exit=1\n"),
            "failed cold Q": ("cold-Q-key.injection.log", b"exit=1\n"),
            "invented guest": ("invalid-S.log", b"first frame simulated\n"),
            "no refusal": ("invalid-S.log", b"NO"),
            "wrong report": ("invalid-S-result.json", b"{}"),
        }
        for label, (name, value) in mutations.items():
            with self.subTest(label=label):
                files = dict(self.files)
                if value is None:
                    files.pop(name)
                else:
                    files[name] = value
                with self.assertRaises((ValueError, TypeError)):
                    qa.audit(self.path, self.pack(files), self.cmd)

    def test_source_and_launcher_provenance_pins_must_match(self):
        receipt = self.pack(self.files)
        with self.assertRaises(ValueError):
            qa.audit(self.path, "f" * 64, self.cmd)
        with self.assertRaises(ValueError):
            qa.audit(self.path, receipt, "e" * 64)


if __name__ == "__main__":
    unittest.main()

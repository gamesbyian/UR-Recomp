#!/usr/bin/env python3
"""ROM-free adversarial tests for independent original Windows CMD-Q archive."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import hashlib

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_interactive_q_original.py"
spec = importlib.util.spec_from_file_location("qa02q", SCRIPT)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture():
    committed = b"ASJIver3.30" + bytes(8192 - 11)
    raw = bytearray(committed)
    raw[256] ^= 1
    typed = (b"UR-HOST-PROFILE/5\nprofile=native-ci-rider\nstock_sram=" +
             committed.hex().encode() + b"\n")
    original = {"catalog": b"catalog", "raw": bytes(raw),
                "selector": b"selector", "typed": typed}
    files = {f"source-bytes/{stage}.{name}.bin": data
             for stage in ("before-Q", "after-Q") for name, data in original.items()}
    cmd = sha(b"run-baldosa-modern.cmd")
    result = {
        "schema": "ur-win32-interactive-original-cmd-q/1",
        "genuine_win32_console_key_event": "Q", "child_process_exit_code": 7,
        "exact_extracted_cmd_sha256": cmd,
        "original_persisted_bytes_equal_after_Q": True,
        "eight_original_before_after_binary_members": True,
        "legacy_raw_signature_preserved": True,
        "manual_repair_archive_created": False,
        "second_guest_or_default_fallback": False,
        "independent_qa_release_credit": 0,
        "source_bytes_sha256": {
            path.removeprefix("source-bytes/"): {"sha256": sha(data), "bytes": len(data)}
            for path, data in files.items()},
        "typed_raw_selector_catalog_sha256": {
            name: sha(data) for name, data in original.items()},
    }
    files.update({
        "interactive-q-result.json": (json.dumps(result, sort_keys=True, indent=2)+"\n").encode(),
        "interactive-console.log": (
            b"UR-BALDOSA-STARTUP-PROFILE-REJECTED: safe\n"
            b"Q: Exit without changing any saved data.\n"
            b"Explicit recovery choice [R/T/S/Q]: "),
        "key-injection.log": b"exit=0\n\n\n",
        "original-fixture.log": b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE state=1 sram=8192\n",
    })
    return files, cmd


class TestOriginalInteractiveQ(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "original.zip"
        self.files, self.cmd = fixture()

    def archive(self, files=None):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in (files if files is not None else self.files).items():
                z.writestr(name, data)
        return sha(self.path.read_bytes())

    def test_exact_synthetic_contract_no_gate(self):
        digest = self.archive()
        result = qa.audit(self.path, digest, self.cmd)
        self.assertEqual(result["original_binary_snapshots_independently_rehashed"], 8)
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertFalse(result["operator_physically_typed_Q"])

    def test_original_missing_or_modified_evidence_fails_closed(self):
        def raw(files): files["source-bytes/after-Q.raw.bin"] = b"X"*8192
        def inject(files): files["key-injection.log"] = b"exit=1\n"
        def denied(files): files["interactive-console.log"] = b"ERROR: Access is denied.\n"
        def extra(files): files["rom.sfc"] = b"ROM"
        def missing(files): del files["source-bytes/after-Q.typed.bin"]
        def report(files): files["interactive-q-result.json"] = b"{}"
        def typed(files): files["source-bytes/before-Q.typed.bin"] = b"bad-typed"
        for mutation in (raw, inject, denied, extra, missing, report, typed):
            with self.subTest(mutation=mutation.__name__):
                files = dict(self.files)
                mutation(files)
                digest = self.archive(files)
                with self.assertRaises(ValueError):
                    qa.audit(self.path, digest, self.cmd)

    def test_wrong_external_original_artifact_or_cmd_sha_refused(self):
        digest = self.archive()
        with self.assertRaises(ValueError):
            qa.audit(self.path, "f"*64, self.cmd)
        with self.assertRaises(ValueError):
            qa.audit(self.path, digest, "e"*64)


if __name__ == "__main__":
    unittest.main()

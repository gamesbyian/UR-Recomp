#!/usr/bin/env python3
"""ROM-free adversarial unit tests: no Windows/release qualification by fixtures."""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_full_original_fault_archive.py"
spec = importlib.util.spec_from_file_location("qa02full", SCRIPT)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class TestFullOriginalFaultArchive(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.zip"

    def make_zip(self, entries: dict[str, bytes]) -> str:
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in entries.items():
                archive.writestr(name, raw)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_direct_source_binary_receipt_with_missing_and_changed_cases(self):
        root = "native_actual_win32_prewrite_dacl_denial/fault-bytes/"
        data = b"original disposable source"
        metadata = {"srm.before.bin": {
            "sha256": qa.sha(data), "bytes": len(data)}}
        source = {
            root + "srm.before.bin": data,
            root + "file-receipt.json": json.dumps(metadata).encode(),
        }
        self.make_zip(source)
        with zipfile.ZipFile(self.path) as archive:
            self.assertEqual(qa.audit_receipt(
                archive, root + "file-receipt.json"),
                ("native_actual_win32_prewrite_dacl_denial", 1))
        for mutated in (
            {root + "srm.before.bin": b"changed"},
            {root + "file-receipt.json": b'{"srm.before.bin": {"bytes": 0, "sha256": "bad"}}'},
        ):
            source2 = {**source, **mutated}
            self.make_zip(source2)
            with zipfile.ZipFile(self.path) as archive:
                with self.assertRaises(ValueError):
                    qa.audit_receipt(archive, root + "file-receipt.json")

    def test_staged_old_new_raw_source_receipts(self):
        root = "native_post_raw_pre_typed_crash/fault-bytes/"
        first, second = b"old", b"new!"
        receipt = {"raw-sram": {
            "before_sha256": qa.sha(first), "before_bytes": len(first),
            "after_sha256": qa.sha(second), "after_bytes": len(second)}}
        self.make_zip({
            root + "raw-sram.before.bin": first,
            root + "raw-sram.after.bin": second,
            root + "file-receipt.json": json.dumps(receipt).encode()})
        with zipfile.ZipFile(self.path) as z:
            self.assertEqual(qa.audit_receipt(
                z, root + "file-receipt.json"),
                ("native_post_raw_pre_typed_crash", 2))

    def test_second_cold_receipt_uses_original_source_path(self):
        root = "native_intent_restart_recovery/fault-bytes/"
        b = b"confirmed stable"
        self.make_zip({
            root + "raw-sram.second-cold.bin": b,
            root + "second-cold-file-receipt.json":
                json.dumps({"raw-sram": {
                    "bytes": len(b), "sha256": qa.sha(b),
                    "identical_to_first_recovered": True}}).encode()})
        with zipfile.ZipFile(self.path) as z:
            self.assertEqual(qa.audit_receipt(
                z, root + "second-cold-file-receipt.json"),
                ("native_intent_restart_recovery", 1))

    def test_full_archive_wrong_digest_and_missing_inventory_fail_closed(self):
        digest = self.make_zip({"unreviewed-game.sfc": b"ROM"})
        with self.assertRaises(ValueError):
            qa.audit(self.path, "f" * 64)
        with self.assertRaises(ValueError):
            qa.audit(self.path, digest)
        with self.assertRaises(ValueError):
            qa.audit(self.path, "not-a-sha")


if __name__ == "__main__":
    unittest.main()

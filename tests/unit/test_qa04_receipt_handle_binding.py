"""ROM-free QA04 receipt leaf TOCTOU negatives, independent current-main fix.

The existing attachment reader is already descriptor-bound. This tests the
distinct top-level witness.json *read*, which previously called Path.read_text
after separate Path.stat checks. No real Windows reparse/handle acceptance,
physical tester, copyrighted file, or release-gate credit is claimed.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_qa04_physical_windows_packets as qa
from test_check_qa04_physical_windows_packets import (
    SOURCE, ZIP, PE, make_packet,
)


@unittest.skipUnless(sys.platform.startswith("linux"),
                     "rename-while-open synthetic POSIX race, not Win32 QA")
class ReceiptHandleBindingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.receipt = make_packet(root, "pc1")
        self.original_open = qa.os.open

    def _inspect(self):
        return qa.inspect_packet(self.receipt, commit=SOURCE,
                                 zip_sha=ZIP, pe_sha=PE)

    def test_leaf_replaced_with_valid_same_length_receipt_after_handle_open(self):
        replacement = self.receipt.with_name("replacement.json")
        replacement_bytes = self.receipt.read_bytes()
        replacement.write_bytes(replacement_bytes)
        fired = []

        def replace_after_open(path, *args, **kwargs):
            fd = self.original_open(path, *args, **kwargs)
            if Path(path) == self.receipt and not fired:
                fired.append(True)
                os.replace(replacement, self.receipt)
            return fd

        with mock.patch.object(qa.os, "open", side_effect=replace_after_open):
            with self.assertRaisesRegex(ValueError, "receipt.*changed|unsafe receipt"):
                self._inspect()
        self.assertEqual(fired, [True])
        self.assertEqual(self.receipt.read_bytes(), replacement_bytes)

    def test_receipt_swapped_to_symlink_just_before_open(self):
        saved = self.receipt.with_name("saved.json")
        fired = []

        def redirect_before_open(path, *args, **kwargs):
            if Path(path) == self.receipt and not fired:
                fired.append(True)
                self.receipt.rename(saved)
                self.receipt.symlink_to(saved)
            return self.original_open(path, *args, **kwargs)

        with mock.patch.object(qa.os, "open", side_effect=redirect_before_open):
            with self.assertRaisesRegex(ValueError, "unsafe receipt|receipt.*changed"):
                self._inspect()
        self.assertEqual(fired, [True])

    def test_unchanged_receipt_still_valid(self):
        receipt, summary = self._inspect()
        self.assertEqual(receipt["source_commit"], SOURCE)
        self.assertTrue(summary["local_attachment_sha256_verified"])


if __name__ == "__main__":
    unittest.main()

"""H26 recovered QA04 packet receipt and namespace negatives; no physical QA."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_qa04_physical_windows_packets import inspect_packet, safe_member

PINS = {"commit": "a" * 40, "zip_sha": "b" * 64, "pe_sha": "c" * 64}


class QA04ReceiptNamespaceTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "link"), "hardlinks unavailable")
    def test_hardlinked_receipt_refused_before_json_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "receipt.json"
            p.write_text("invalid receipt JSON", encoding="utf-8")
            try:
                os.link(p, Path(tmp) / "receipt-copy.json")
            except OSError as exc:
                self.skipTest(f"hardlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "hardlinked receipt JSON"):
                inspect_packet(p, **PINS)

    def test_regular_receipt_reaches_strict_json_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "receipt.json"
            p.write_text("invalid receipt JSON", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                inspect_packet(p, **PINS)

    @unittest.skipUnless(hasattr(os, "link"), "hardlinks unavailable")
    def test_hardlinked_attachment_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            root.mkdir()
            p = root / "capture.log"
            p.write_bytes(b"synthetic bytes")
            try:
                os.link(p, root / "other.log")
            except OSError as exc:
                self.skipTest(f"hardlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "hardlinked evidence attachment"):
                safe_member(root, "capture.log")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_packet_parent_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "real"
            root.mkdir()
            (root / "capture.log").write_bytes(b"synthetic bytes")
            alias = Path(tmp) / "alias"
            try:
                alias.symlink_to(root, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "symlinked/noncanonical"):
                safe_member(alias, "capture.log")

    def test_legal_unique_regular_attachment_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            root.mkdir()
            p = root / "startup.log"
            p.write_bytes(b"synthetic bytes")
            self.assertEqual(safe_member(root, "startup.log"), p)


if __name__ == "__main__":
    unittest.main()

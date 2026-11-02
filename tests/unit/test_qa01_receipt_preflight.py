"""ROM-free preflight for receipt storage before native WAV publication."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_pcm_at_kon as offline
import qa01_live_kon_pcm as live


class ReceiptPreflightTests(unittest.TestCase):
    def test_missing_parent_created_and_writable(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "nested" / "receipt.json"
            offline.prepare_receipt_destination(receipt)
            self.assertTrue(receipt.parent.is_dir())
            self.assertFalse(receipt.exists())
            self.assertEqual(list(receipt.parent.iterdir()), [])

    def test_existing_receipt_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            receipt.write_bytes(b"FOREIGN")
            with self.assertRaisesRegex(ValueError, "existing evidence JSON"):
                offline.prepare_receipt_destination(receipt)
            self.assertEqual(receipt.read_bytes(), b"FOREIGN")

    def test_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            alias = root / "alias"
            try:
                alias.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError, "real directory"):
                offline.prepare_receipt_destination(alias / "receipt.json")
            self.assertEqual(list(actual.iterdir()), [])

    def test_unusable_receipt_parent_refused_before_server_connection(self):
        for module in (offline, live):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                executable = root / "native.exe"
                executable.write_bytes(b"synthetic")
                blocked = root / "not-a-directory"
                blocked.write_bytes(b"FOREIGN")
                wav = root / "capture.wav"
                receipt = blocked / "receipt.json"
                argv = [module.__name__ + ".py", "--wav-out", str(wav),
                        "--json-out", str(receipt), "--source-sha", "a" * 40,
                        "--native-executable", str(executable)]
                if module is offline:
                    argv += ["--kon-sample-index", "40000"]
                with patch.object(sys, "argv", argv), patch.object(module, "connect") as connect:
                    with self.assertRaises(SystemExit) as cm:
                        module.main()
                    self.assertEqual(cm.exception.code, 2)
                    connect.assert_not_called()
                self.assertFalse(wav.exists())
                self.assertEqual(blocked.read_bytes(), b"FOREIGN")


if __name__ == "__main__":
    unittest.main()

"""Preservation is independently checkable; a ZIP name alone proves nothing."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tools import recovery_preservation as rp


SHA = "a" * 40


class RecoveryPreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools").mkdir()
        (self.root / "tools" / "source.py").write_text("print('recovery')\n",
                                                        encoding="utf-8")
        self.archive = self.root / "archive.zip"

    def stage(self):
        return rp.stage(self.root, ["tools/source.py"], self.archive,
                        "h29-source-candidate", "UR-CPU-01", SHA)

    def test_roundtrip_manifest_and_readback(self):
        item = self.stage()
        self.assertFalse(item["remote_preserved"])
        self.assertEqual(item["payloads"], 2)
        with ZipFile(self.archive) as zip_file:
            handoff = json.loads(zip_file.read("handoff.json"))
            self.assertEqual(handoff["github_outcome"], "not_yet_recorded")
            self.assertEqual(zip_file.read("payload/tools/source.py"),
                             b"print('recovery')\n")
        fetched = self.root / "drive-downloaded.zip"
        fetched.write_bytes(self.archive.read_bytes())
        verified = rp.audit(self.archive, fetched, item["archive_sha256"])
        self.assertTrue(verified["downloaded_bytes_equal"])
        self.assertFalse(verified["provider_drive_id_independently_verified"])

    def test_reject_mutated_readback_even_with_valid_original(self):
        item = self.stage()
        fetched = self.root / "drive-downloaded.zip"
        fetched.write_bytes(self.archive.read_bytes() + b"malformed")
        with self.assertRaises(ValueError):
            rp.audit(self.archive, fetched, item["archive_sha256"])

    def test_reject_original_mismatch(self):
        item = self.stage()
        fetched = self.root / "download.zip"
        fetched.write_bytes(self.archive.read_bytes())
        with self.assertRaises(ValueError):
            rp.audit(self.archive, fetched, "0" * 64)
        self.assertTrue(item["archive_sha256"])

    def test_refuse_overwrite(self):
        self.stage()
        with self.assertRaises(ValueError):
            self.stage()

    def test_reject_symlink_escape(self):
        (self.root / "tools" / "escape.py").symlink_to("/etc/hosts")
        with self.assertRaises(ValueError):
            rp.stage(self.root, ["tools/escape.py"], self.archive,
                     "h29-source-candidate", "UR-CPU-01", SHA)

    def test_reject_credentials_roms_and_traversal(self):
        for name in ["../private.py", "reference/roms/game.sfc",
                     ".env", "tools/secret.key", "tools\\source.py",
                     "tools/./source.py"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                rp.safe_name(name)

    def test_reject_duplicate_and_bad_source(self):
        with self.assertRaises(ValueError):
            rp.stage(self.root, ["tools/source.py", "tools/source.py"],
                     self.archive, "h29-source-candidate", "UR-CPU-01", SHA)
        with self.assertRaises(ValueError):
            rp.stage(self.root, ["tools/source.py"],
                     self.archive, "h29-source-candidate", "UR-CPU-01", "unknown")

    def test_package_is_deterministic(self):
        first = self.stage()
        other = self.root / "other.zip"
        second = rp.stage(self.root, ["tools/source.py"], other,
                          "h29-source-candidate", "UR-CPU-01", SHA)
        self.assertEqual(first["archive_sha256"], second["archive_sha256"])
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                         first["archive_sha256"])


if __name__ == "__main__":
    unittest.main()

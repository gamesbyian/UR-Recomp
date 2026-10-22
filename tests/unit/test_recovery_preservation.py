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

    def test_incident_register_requires_proof_for_verified_state(self):
        record = {"schema": "ur-publication-incidents/1",
                  "scope": "curated_not_exhaustive",
                  "incidents": [{
                      "incident_id": "h29-denied-case", "candidate_id": "h29-denied-case",
                      "work_id": "UR-CPU-01", "source_main_sha": None,
                      "operation": "GitHub create_file", "target_path": "tools/example.py",
                      "original_error": "This tool call was blocked by OpenAI's safety checks.",
                      "classification": "explicit_safety_denial",
                      "vault_file_id": "an-observed-drive-id-xyz",
                      "vault_sha256": None, "byte_readback": "pending",
                      "disposition": "held_for_independent_review",
                      "next_authorized_action": "Independent source review",
                      "release_gate_credit": False
                  }]}
        self.assertEqual(rp.validate_incidents(record)["incidents_validated"], 1)
        record["incidents"][0]["byte_readback"] = "verified"
        with self.assertRaises(ValueError):
            rp.validate_incidents(record)
        record["incidents"][0]["vault_sha256"] = "e" * 64
        self.assertEqual(rp.validate_incidents(record)["incidents_validated"], 1)
        record["incidents"][0]["release_gate_credit"] = True
        with self.assertRaises(ValueError):
            rp.validate_incidents(record)

    def test_committed_incident_register_valid(self):
        registry = (Path(__file__).resolve().parents[2] /
                    "docs/recovery/publication-incidents.json")
        record = json.loads(registry.read_text(encoding="utf-8"))
        self.assertEqual(rp.validate_incidents(record)["incidents_validated"], 2)

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

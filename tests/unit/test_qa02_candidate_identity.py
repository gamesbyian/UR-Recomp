#!/usr/bin/env python3
"""Contract tests for nominated QA-02 identity; no synthetic gate credit."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from qa02_candidate_identity import CandidateIdentity


class IdentityTests(unittest.TestCase):
    def test_exact_archive_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "candidate.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("game.exe", b"PE-fixture")
            receipt = root / "identity.json"
            record = {
                "source_sha": "a" * 40,
                "zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "exe_sha256": hashlib.sha256(b"PE-fixture").hexdigest(),
            }
            receipt.write_text(json.dumps(record), encoding="utf-8")
            identity = CandidateIdentity.from_receipt(receipt)
            self.assertEqual(identity.verify(archive, "game.exe"), b"PE-fixture")
            archive.write_bytes(archive.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "nominated ZIP"):
                identity.verify(archive, "game.exe")
            record["exe_sha256"] = "0" * 64
            receipt.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nominated ZIP"):
                CandidateIdentity.from_receipt(receipt).verify(archive, "game.exe")

    def test_reject_partial_or_untrusted_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "identity.json"
            for bad in (
                {"source_sha": "a" * 7, "zip_sha256": "b" * 64, "exe_sha256": "c" * 64},
                {"source_sha": "a" * 40, "zip_sha256": "b" * 64, "exe_sha256": "c" * 64, "trusted": True},
                {"source_sha": "a" * 40, "zip_sha256": "b" * 64},
            ):
                receipt.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(ValueError):
                    CandidateIdentity.from_receipt(receipt)


if __name__ == "__main__":
    unittest.main()

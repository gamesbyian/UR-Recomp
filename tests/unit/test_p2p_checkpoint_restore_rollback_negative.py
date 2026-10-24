"""Real filesystem rollback negative for signed local P2P SQLite checkpoint CAS.

A copied older database can be restored, re-admitting an already accepted
signed checkpoint. This is an explicit limitation, not an anti-rollback claim.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/p2p"))

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from checkpoint_store_cas import initialize, read_anchor, commit_chain, ZERO
    from signed_checkpoint_anchor_lab import signature_message
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


@unittest.skipUnless(HAS_CRYPTO, "cryptography Ed25519 unavailable")
class ActualLocalDatabaseRollbackNegative(unittest.TestCase):
    def test_restoring_old_database_readmits_signed_second_revision(self):
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        session = "a" * 32

        def signed_receipt(revision, previous):
            raw = json.dumps(
                {"session": session, "revision": revision,
                 "previous_digest": previous, "contacts": []},
                sort_keys=True, separators=(",", ":")).encode()
            digest = hashlib.sha256(raw).hexdigest()
            return (raw, key.sign(signature_message(session, revision, digest))), digest

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "checkpoint.db"
            old_copy = root / "old-copy"
            staged_restore = root / "restore.tmp"
            initialize(db)
            first, d1 = signed_receipt(1, ZERO)
            second, d2 = signed_receipt(2, d1)
            self.assertEqual(commit_chain(db, session, (0, ZERO), [first], public),
                             (1, d1))
            shutil.copyfile(db, old_copy)
            self.assertEqual(commit_chain(db, session, (1, d1), [second], public),
                             (2, d2))
            self.assertEqual(read_anchor(db, session), (2, d2))
            # Attacker is able to replace both the DB file and any untrusted
            # local checkpoint. Signatures still authenticate old state.
            shutil.copyfile(old_copy, staged_restore)
            os.replace(staged_restore, db)
            self.assertEqual(read_anchor(db, session), (1, d1))
            self.assertEqual(commit_chain(db, session, (1, d1), [second], public),
                             (2, d2))
            self.assertEqual(read_anchor(db, session), (2, d2))


if __name__ == "__main__":
    unittest.main()

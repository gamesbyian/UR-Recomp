"""ROM-free, local SQLite signed-finish ledger controls; no WAN/rollback claim."""
import copy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
from authenticated_finish_ledger import (commit_authenticated_finish, initialize,
                                         read_committed)
from signed_completion_receipt_contract import completion_message

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
except ImportError:
    Ed25519PrivateKey = None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(public, message, signature):
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
        return True
    except InvalidSignature:
        return False


@unittest.skipIf(Ed25519PrivateKey is None, "cryptography Ed25519 unavailable")
class AuthenticatedFinishLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "finish.db"
        initialize(self.db)
        self.responder = Ed25519PrivateKey.generate()
        self.attacker = Ed25519PrivateKey.generate()
        pub = self.responder.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()
        self.expected = {
            "expected_responder": pub,
            "invite_sha256": digest(b"invitation"),
            "response_sha256": digest(b"responder challenge"),
            "finish_sha256": digest(b"initiator signed finish"),
            "challenge_nonce": "a5" * 16,
        }
        payload = {"version": 1, "responder": pub,
                   **{k: v for k, v in self.expected.items()
                      if k != "expected_responder"}}
        self.receipt = {"type": "responder_complete", "payload": payload,
                        "signature": self.responder.sign(completion_message(payload)).hex()}

    def commit(self, receipt=None, **changes):
        return commit_authenticated_finish(
            self.db, self.receipt if receipt is None else receipt,
            verify_signature=verify, **(self.expected | changes))

    def test_signed_receipt_commits_once_and_survives_reopen(self):
        self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))
        result = self.commit()
        self.assertEqual(len(result), 64)
        self.assertEqual(read_committed(self.db, self.expected["invite_sha256"]),
                         (self.expected["expected_responder"], result))
        with self.assertRaisesRegex(ValueError, "already completed"):
            self.commit()
        self.assertEqual(read_committed(self.db, self.expected["invite_sha256"])[1],
                         result)

    def test_invalid_or_unsigned_finish_does_not_consume_invite(self):
        for receipt in ({"status": "ok"},
                        {"type": "responder_complete", "payload": self.receipt["payload"]},
                        None):
            with self.subTest(receipt=receipt), self.assertRaises(ValueError):
                commit_authenticated_finish(self.db, receipt, verify_signature=verify,
                                            **self.expected)
            self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))
        forged = copy.deepcopy(self.receipt)
        forged["signature"] = self.attacker.sign(completion_message(forged["payload"])).hex()
        with self.assertRaisesRegex(ValueError, "signature invalid"):
            self.commit(forged)
        self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))
        self.commit()

    def test_transcript_substitution_does_not_consume_invite(self):
        for field in ("invite_sha256", "response_sha256", "finish_sha256", "challenge_nonce"):
            changed = "bb" * (16 if field == "challenge_nonce" else 32)
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "transcript mismatch"):
                self.commit(**{field: changed})
            self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))

    def test_two_concurrent_writers_only_one_commits(self):
        barrier = threading.Barrier(2)
        results = []
        def writer():
            barrier.wait()
            try:
                results.append(("ok", self.commit()))
            except ValueError as exc:
                results.append(("rejected", str(exc)))
        threads = [threading.Thread(target=writer) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sorted(x[0] for x in results), ["ok", "rejected"])
        self.assertIn("already completed", results[0][1] + results[1][1])

    def test_uninitialized_and_alias_paths_do_not_create_or_consume(self):
        missing = Path(self.temp.name) / "missing.db"
        with self.assertRaisesRegex(ValueError, "missing SQLite DB"):
            commit_authenticated_finish(missing, self.receipt,
                                        verify_signature=verify, **self.expected)
        self.assertFalse(missing.exists())
        alias = Path(self.temp.name) / "alias.db"
        alias.symlink_to(self.db)
        with self.assertRaisesRegex(ValueError, "symlink"):
            commit_authenticated_finish(alias, self.receipt,
                                        verify_signature=verify, **self.expected)
        self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))
        with self.assertRaisesRegex(ValueError, "non-durable"):
            initialize(":memory:")

    def test_rejected_bad_schema_does_not_commit(self):
        import sqlite3
        with sqlite3.connect(self.db) as db:
            db.execute("DROP TABLE authenticated_finish")
            db.execute("CREATE TABLE authenticated_finish (invite_sha256 TEXT)")
        with self.assertRaises(sqlite3.OperationalError):
            self.commit()
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM authenticated_finish").fetchone(), (0,))

    def test_private_posix_file_creation(self):
        if os.name == "posix":
            self.assertEqual(self.db.stat().st_mode & 0o077, 0)

    def test_local_database_rollback_is_not_resisted(self):
        # Explicit negative: copying the empty DB and restoring it after a
        # successful commit erases the local replay high-water state.
        before = self.db.read_bytes()
        self.commit()
        self.assertIsNotNone(read_committed(self.db, self.expected["invite_sha256"]))
        self.db.write_bytes(before)
        self.assertIsNone(read_committed(self.db, self.expected["invite_sha256"]))
        self.commit()  # Demonstrates why independent monotonic trust is needed.


if __name__ == "__main__":
    unittest.main()

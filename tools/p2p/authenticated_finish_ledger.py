"""Offline P2P *initiator-side* authenticated-finish replay ledger.

A successful signed completion receipt is required before an invitation is
marked consumed. The ledger composes the existing responder-signed receipt
validator with an SQLite UNIQUE constraint and a serialized transaction.

Research only: this does not authenticate the initiator to the responder,
prove the responder durably committed its token, survive whole-database
rollback, solve lost-acknowledgment recovery, or connect to a real network.
The caller must pin the responder key and provide a genuine Ed25519 verifier.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import os
import sqlite3

from checkpoint_store_cas import _durable_db_path, _same_inode
from signed_completion_receipt_contract import (completion_message,
                                                verify_responder_completion)

COMMIT_DOMAIN = b"UR-P2P-INITIATOR-FINISH-LEDGER/1\x00"


def initialize(path) -> None:
    """Explicitly initialize a local ledger; reads/commits never create one."""
    p = _durable_db_path(path, must_exist=False)
    before = p.lstat() if p.exists() else None
    if before is None:
        # SQLite's default umask can leave a newly created DB world-readable.
        # Create privately and exclusively before handing it to SQLite.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(p, flags, 0o600)
        except FileExistsError as exc:
            raise ValueError("ledger path appeared during initialization") from exc
        else:
            os.close(fd)
    with closing(sqlite3.connect(str(p))) as db:
        _same_inode(p, before)
        db.execute("PRAGMA synchronous=FULL")
        db.execute("CREATE TABLE IF NOT EXISTS authenticated_finish ("
                   "invite_sha256 TEXT PRIMARY KEY, responder TEXT NOT NULL, "
                   "receipt_sha256 TEXT NOT NULL)")
        db.commit()


def read_committed(path, invite_sha256: str) -> tuple[str, str] | None:
    """Return stored responder/receipt digest without mutating the database."""
    if (type(invite_sha256) is not str or len(invite_sha256) != 64 or
            any(c not in "0123456789abcdef" for c in invite_sha256)):
        raise ValueError("invalid invitation digest")
    p = _durable_db_path(path, must_exist=True)
    before = p.lstat()
    with closing(sqlite3.connect(p.as_uri() + "?mode=ro", uri=True)) as db:
        _same_inode(p, before)
        db.execute("PRAGMA query_only=ON")
        row = db.execute(
            "SELECT responder,receipt_sha256 FROM authenticated_finish "
            "WHERE invite_sha256=?", (invite_sha256,)).fetchone()
    if row is None:
        return None
    if (len(row) != 2 or any(type(x) is not str or len(x) != 64 or
                            any(c not in "0123456789abcdef" for c in x)
                            for x in row)):
        raise ValueError("corrupt authenticated-finish row")
    return row


def commit_authenticated_finish(
    path, receipt, *, expected_responder: str, invite_sha256: str,
    response_sha256: str, finish_sha256: str, challenge_nonce: str,
    verify_signature,
) -> str:
    """Verify responder completion, then consume invite exactly once locally.

    Returns a receipt digest after SQLite COMMIT. An invalid signature,
    transcript mismatch or duplicate invitation must never be reported as
    success. A replay following a lost acknowledgment remains a rejection;
    callers must implement a separately authenticated recovery exchange.
    """
    verify_responder_completion(
        receipt, expected_responder=expected_responder,
        invite_sha256=invite_sha256, response_sha256=response_sha256,
        finish_sha256=finish_sha256, challenge_nonce=challenge_nonce,
        verify_signature=verify_signature,
    )
    signed_bytes = (COMMIT_DOMAIN + completion_message(receipt["payload"]) +
                    bytes.fromhex(receipt["signature"]))
    receipt_digest = hashlib.sha256(signed_bytes).hexdigest()
    p = _durable_db_path(path, must_exist=True)
    before = p.lstat()
    db = sqlite3.connect(p.as_uri() + "?mode=rw", uri=True,
                         timeout=5.0, isolation_level=None)
    try:
        _same_inode(p, before)
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute(
                "INSERT INTO authenticated_finish "
                "(invite_sha256,responder,receipt_sha256) VALUES(?,?,?)",
                (invite_sha256, expected_responder, receipt_digest))
        except sqlite3.IntegrityError as exc:
            raise ValueError("invitation already completed") from exc
        db.execute("COMMIT")
        return receipt_digest
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()

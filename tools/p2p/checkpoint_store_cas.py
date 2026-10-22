"""SQLite local P2P signed-checkpoint CAS pilot, NOT rollback-resistant storage.

The caller must independently pin inviter key, session, and trusted high-water
anchor. SQLite transactions prevent concurrent local writers from silently
clobbering a newer checkpoint, but an attacker restoring the entire DB and
external trusted state defeats anti-rollback. No network transport is included.
"""
from pathlib import Path
import os
import stat
import re
import sqlite3
from contextlib import closing
import struct
from checkpoint_chain_audit import verify_chain
from signed_checkpoint_anchor_lab import ZERO

SESSION = re.compile(r'[0-9a-f]{32}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def _validate(session, anchor):
    if (type(session) is not str or SESSION.fullmatch(session) is None or
            type(anchor) is not tuple or len(anchor) != 2 or
            type(anchor[0]) is not int or not 0 <= anchor[0] < 2**64 or
            type(anchor[1]) is not str or DIGEST.fullmatch(anchor[1]) is None or
            (anchor[0] == 0 and anchor[1] != ZERO)):
        raise ValueError('invalid session/trusted checkpoint anchor')


def _revision_blob(revision):
    return struct.pack('>Q', revision)  # SQLite INTEGER is signed 64-bit only.



def _durable_db_path(path, *, must_exist):
    """Reject aliasable local DB paths before SQLite opens a handle.

    Non-atomic against a hostile writer racing path replacement; true durable
    monotonic state still requires an external trust anchor.
    """
    if not isinstance(path, (str,Path)) or not str(path) or str(path).startswith('file:') or str(path)==':memory:':
        raise ValueError('non-durable SQLite path')
    p=Path(path).absolute()
    if not p.name or not p.parent.is_dir():
        raise ValueError('missing SQLite parent')
    for ancestor in (p.parent,*p.parents):
        if ancestor.is_symlink():
            raise ValueError('symlink SQLite ancestor')
    if p.is_symlink():
        raise ValueError('symlink SQLite DB')
    if must_exist and not p.is_file():
        raise ValueError('missing SQLite DB')
    if p.exists():
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:
            raise ValueError('aliased/nonregular SQLite DB')
    return p


def _same_inode(p, before):
    after=p.lstat()
    if (not stat.S_ISREG(after.st_mode) or after.st_nlink!=1 or
            (before is not None and (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino))):
        raise ValueError('SQLite path changed during open')


def initialize(path):
    """Explicit initialization only; never invoked by a read."""
    p=_durable_db_path(path,must_exist=False)
    before=p.lstat() if p.exists() else None
    with closing(sqlite3.connect(str(p))) as db:
        _same_inode(p,before)
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS checkpoint ('
                   'session TEXT PRIMARY KEY, revision BLOB NOT NULL, '
                   'digest TEXT NOT NULL)')
        db.commit()


def read_anchor(path, session):
    _validate(session, (0, ZERO))
    p=_durable_db_path(path,must_exist=True)
    before=p.lstat()
    # Read-only SQLite URI plus query_only prevents a read from creating tables.
    with closing(sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)) as db:
        _same_inode(p,before)
        db.execute('PRAGMA query_only=ON')
        row = db.execute('SELECT revision,digest FROM checkpoint WHERE session=?',
                         (session,)).fetchone()
    if row is None:
        return (0, ZERO)
    revision, digest = row
    if type(revision) is not bytes or len(revision) != 8:
        raise ValueError('corrupt checkpoint revision encoding')
    anchor = (struct.unpack('>Q', revision)[0], digest)
    _validate(session, anchor)
    return anchor


def commit_chain(path, session, trusted_anchor, receipts, pinned_key):
    """Verify signatures, then atomically CAS a pre-initialized local row."""
    _validate(session, trusted_anchor)
    proposed = verify_chain(receipts, pinned_key=pinned_key, session=session,
                            initial_anchor=trusted_anchor)
    # mode=rw refuses a missing store instead of creating a silently
    # uninitialized local trust database during an attempted commit.
    p=_durable_db_path(path,must_exist=True)
    before=p.lstat()
    db = sqlite3.connect(p.as_uri() + '?mode=rw',
                         uri=True, timeout=5.0, isolation_level=None)
    try:
        _same_inode(p,before)
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT revision,digest FROM checkpoint WHERE session=?',
                         (session,)).fetchone()
        if row is None:
            current = (0, ZERO)
        else:
            if type(row[0]) is not bytes or len(row[0]) != 8:
                raise ValueError('corrupt stored revision')
            current = (struct.unpack('>Q', row[0])[0], row[1])
        if current != trusted_anchor:
            raise ValueError('stale or forked local checkpoint anchor')
        db.execute('INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?) '
                   'ON CONFLICT(session) DO UPDATE SET revision=excluded.revision, '
                   'digest=excluded.digest',
                   (session, _revision_blob(proposed[0]), proposed[1]))
        db.execute('COMMIT')
        return proposed
    except BaseException:
        if db.in_transaction:
            db.execute('ROLLBACK')
        raise
    finally:
        db.close()

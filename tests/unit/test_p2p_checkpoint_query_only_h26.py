"""Recovered H26 SQLite read-only invariants, adapted to current checkpoint CAS.

ROM-free, local persistence checks only. These do not establish durable
anti-rollback against an attacker who restores trusted external state.
Original source: H26 source/p2p/test_readonly_query_guard.py.
"""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
import checkpoint_store_cas as store

SESSION = 'a' * 32


class _ReadConnectionObserver:
    """Observe the live connection used by read_anchor before it closes."""

    def __init__(self, db, readings):
        self.db = db
        self.readings = readings

    def execute(self, statement, *args, **kwargs):
        if statement.startswith('SELECT revision,digest FROM checkpoint'):
            query_only = self.db.execute('PRAGMA query_only').fetchone()[0]
            self.readings.append(query_only)
            # Both controls matter: query_only must be set while a read is
            # actually in flight, and the read connection cannot write.
            with unittest.TestCase().assertRaises(sqlite3.OperationalError):
                self.db.execute('CREATE TABLE injected_by_reader(x)')
        return self.db.execute(statement, *args, **kwargs)

    def close(self):
        self.db.close()


class RecoveredCheckpointReadOnlyTests(unittest.TestCase):
    def test_live_read_uses_query_only_and_rejects_write(self):
        with tempfile.TemporaryDirectory(prefix='ur-checkpoint-ro-') as td:
            path = Path(td) / 'anchor.db'
            store.initialize(path)
            before = path.read_bytes()
            observed = []
            real_connect = sqlite3.connect

            def observe_connect(*args, **kwargs):
                db = real_connect(*args, **kwargs)
                if kwargs.get('uri') and str(args[0]).endswith('?mode=ro'):
                    return _ReadConnectionObserver(db, observed)
                return db

            with patch.object(store.sqlite3, 'connect', side_effect=observe_connect):
                self.assertEqual(store.read_anchor(path, SESSION), (0, store.ZERO))
            self.assertEqual(observed, [1], 'read SELECT did not run under query_only')
            self.assertEqual(path.read_bytes(), before, 'read modified stored bytes')
            with sqlite3.connect(path) as db:
                self.assertNotIn('injected_by_reader', {
                    row[0] for row in db.execute("SELECT name FROM sqlite_master")})

    def test_failed_read_of_empty_database_does_not_initialize_schema(self):
        with tempfile.TemporaryDirectory(prefix='ur-checkpoint-ro-') as td:
            path = Path(td) / 'empty.db'
            path.write_bytes(b'')
            with self.assertRaises(sqlite3.OperationalError):
                store.read_anchor(path, SESSION)
            self.assertEqual(path.read_bytes(), b'')

    def test_missing_database_read_never_creates_a_file(self):
        with tempfile.TemporaryDirectory(prefix='ur-checkpoint-ro-') as td:
            path = Path(td) / 'missing.db'
            with self.assertRaises(ValueError):
                store.read_anchor(path, SESSION)
            self.assertFalse(path.exists())

    def test_corrupt_digest_is_rejected_without_read_side_mutation(self):
        with tempfile.TemporaryDirectory(prefix='ur-checkpoint-ro-') as td:
            path = Path(td) / 'anchor.db'
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute('INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)',
                           (SESSION, b'\x00'*8, 'not-a-digest'))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                store.read_anchor(path, SESSION)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

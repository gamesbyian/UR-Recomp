"""H26 SQLite anchor schema-integrity regression adapted to current CAS."""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
import checkpoint_store_cas as store

SESSION = 'a' * 32


class CheckpointSchemaReadOnlyH26(unittest.TestCase):
    def test_unrelated_schema_is_not_repaired_by_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'unrelated.db'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE unrelated(x INTEGER)')
            original = path.read_bytes()
            with self.assertRaises(sqlite3.OperationalError):
                store.read_anchor(path, SESSION)
            self.assertEqual(path.read_bytes(), original)
            with sqlite3.connect(path) as db:
                tables = {name for (name,) in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {'unrelated'})

    def test_malformed_binary_revision_read_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'anchor.db'
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute('INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)',
                           (SESSION, b'\xff', store.ZERO))
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'corrupt checkpoint revision encoding'):
                store.read_anchor(path, SESSION)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

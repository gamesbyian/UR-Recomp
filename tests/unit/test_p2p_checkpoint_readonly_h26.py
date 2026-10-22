"""Recover H26 first-party SQLite checkpoint read-only/corrupt-row regressions.

Adapted from Agent1 H26 source/p2p/test_sqlite_anchor_read_only.py
in source-complete archive SHA 57067026d35a840c7828b59144c753cc68dcdd3239cabee974deed80113f983e.
Original standalone source is superseded by the merged CAS store.
No live P2P transport or rollback-resistance claim follows.
"""
import sqlite3
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
import checkpoint_store_cas as store

SESSION = "a" * 32


class CheckpointReadOnlyH26(unittest.TestCase):
    def test_missing_db_does_not_get_created_by_read(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "absent.sqlite"
            with self.assertRaisesRegex(ValueError, "missing SQLite DB"):
                store.read_anchor(path, SESSION)
            self.assertFalse(path.exists())

    def test_unknown_schema_is_not_modified_by_read(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "other.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE unrelated(x INTEGER)")
                db.commit()
            before = path.read_bytes()
            with self.assertRaises(sqlite3.OperationalError):
                store.read_anchor(path, SESSION)
            self.assertEqual(before, path.read_bytes())
            with sqlite3.connect(path) as db:
                names = {r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertEqual(names, {"unrelated"})

    def test_integer_revision_is_not_silently_coerced_to_unsigned(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "anchor.sqlite"
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute("INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)",
                           (SESSION, -1, store.ZERO))
                db.commit()
            with self.assertRaisesRegex(ValueError, "corrupt checkpoint revision encoding"):
                store.read_anchor(path, SESSION)

    def test_short_revision_blob_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "anchor.sqlite"
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute("INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)",
                           (SESSION, b"\0" * 4, store.ZERO))
                db.commit()
            with self.assertRaisesRegex(ValueError, "corrupt checkpoint revision encoding"):
                store.read_anchor(path, SESSION)

    def test_corrupt_digest_fails_even_with_valid_revision_blob(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "anchor.sqlite"
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute("INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)",
                           (SESSION, struct.pack(">Q", 1), "bogus"))
                db.commit()
            with self.assertRaisesRegex(ValueError, "invalid session/trusted checkpoint anchor"):
                store.read_anchor(path, SESSION)

    def test_valid_read_preserves_exact_database_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "anchor #?.sqlite"
            store.initialize(path)
            with sqlite3.connect(path) as db:
                db.execute("INSERT INTO checkpoint(session,revision,digest) VALUES(?,?,?)",
                           (SESSION, struct.pack(">Q", 0), store.ZERO))
                db.commit()
            before = path.read_bytes()
            self.assertEqual(store.read_anchor(path, SESSION), (0, store.ZERO))
            self.assertEqual(before, path.read_bytes())

    def test_absent_session_read_does_not_insert_genesis_record(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "anchor.sqlite"
            store.initialize(path)
            before = path.read_bytes()
            self.assertEqual(store.read_anchor(path, SESSION), (0, store.ZERO))
            self.assertEqual(before, path.read_bytes())
            with sqlite3.connect(path) as db:
                count = db.execute("SELECT count(*) FROM checkpoint").fetchone()[0]
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

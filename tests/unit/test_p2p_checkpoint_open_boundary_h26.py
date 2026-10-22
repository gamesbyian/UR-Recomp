"""H26 first-party SQLite source-local read/open path race tests.

These are filesystem regressions, not durable anti-rollback or Windows ACL QA.
"""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
import checkpoint_store_cas as store

SESSION='a'*32


class SQLiteOpenBoundary(unittest.TestCase):
    def test_missing_after_validation_does_not_recreate(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'anchor #?.db'
            store.initialize(path)
            original=sqlite3.connect

            def remove_before_open(*args,**kwargs):
                path.unlink()
                return original(*args,**kwargs)

            with patch.object(store.sqlite3,'connect',side_effect=remove_before_open):
                with self.assertRaises((ValueError,sqlite3.OperationalError)):
                    store.read_anchor(path,SESSION)
            self.assertFalse(path.exists())

    def test_escaped_uri_filename_round_trips_without_other_file(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'anchor #?.db'
            store.initialize(path)
            self.assertEqual(store.read_anchor(path,SESSION),(0,store.ZERO))
            self.assertEqual([x.name for x in Path(td).iterdir()],['anchor #?.db'])


if __name__=='__main__':
    unittest.main()

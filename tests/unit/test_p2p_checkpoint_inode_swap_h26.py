"""Recovered H26 SQLite path-substitution regressions, adapted to current CAS.

A source-local test, not a durable anti-rollback or Windows ACL proof.  The
original H26 test_sqlite_anchor_hardlink.py caught a symlink swap during open;
this tests the same invariant against the current checkpoint_store_cas API.
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
import checkpoint_store_cas as store

SESSION = 'a' * 32


@unittest.skipUnless(os.name == 'posix', 'POSIX inode and symlink semantics only')
class CheckpointOpenReplacement(unittest.TestCase):
    def test_symlink_swap_between_precheck_and_open_refused(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'anchor.db'
            target = Path(d) / 'other.db'
            store.initialize(source)
            store.initialize(target)
            real_connect = sqlite3.connect

            def redirect_during_open(*args, **kwargs):
                source.unlink()
                source.symlink_to(target)
                return real_connect(*args, **kwargs)

            with patch.object(store.sqlite3, 'connect', side_effect=redirect_during_open):
                with self.assertRaisesRegex(ValueError, 'changed during open'):
                    store.read_anchor(source, SESSION)
            self.assertTrue(source.is_symlink())
            self.assertEqual(store.read_anchor(target, SESSION), (0, store.ZERO))

    def test_regular_inode_swap_between_precheck_and_open_refused(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'anchor.db'
            replacement = Path(d) / 'replacement.db'
            store.initialize(source)
            store.initialize(replacement)
            real_connect = sqlite3.connect

            def replace_during_open(*args, **kwargs):
                os.replace(replacement, source)
                return real_connect(*args, **kwargs)

            with patch.object(store.sqlite3, 'connect', side_effect=replace_during_open):
                with self.assertRaisesRegex(ValueError, 'changed during open'):
                    store.read_anchor(source, SESSION)
            self.assertFalse(replacement.exists())
            self.assertEqual(store.read_anchor(source, SESSION), (0, store.ZERO))


if __name__ == '__main__':
    unittest.main()

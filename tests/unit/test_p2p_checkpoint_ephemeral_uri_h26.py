"""Recovered H26 refusal of SQLite URIs masquerading as durable anchors.

Source: H26 test_sqlite_anchor_durable_path.py; adapted to current CAS.
This local negative is not a guarantee against restoration of external state.
"""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
import checkpoint_store_cas as store


class DurableSqlitePathH26(unittest.TestCase):
    def test_ephemeral_and_uri_database_names_do_not_initialize(self):
        # SQLite supports several in-memory databases which cannot supply a
        # durable high-water checkpoint, even if the filename looks plausible.
        for path in (':memory:', Path(':memory:'), '',
                     'file::memory:?cache=shared',
                     'file:shared?mode=memory&cache=shared',
                     'file:anchor.db?mode=rwc'):
            with self.subTest(path=str(path)), self.assertRaisesRegex(
                    ValueError, 'non-durable'):
                store.initialize(path)

    def test_missing_database_read_does_not_create_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'missing.db'
            with self.assertRaisesRegex(ValueError, 'missing SQLite DB'):
                store.read_anchor(path, 'a' * 32)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()

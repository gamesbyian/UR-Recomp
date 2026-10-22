"""H26 source-only local POSIX permission constraints for signed SQLite CAS."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
from checkpoint_store_cas import initialize, read_anchor, ZERO

SESSION = 'a' * 32


@unittest.skipUnless(os.name == 'posix', 'POSIX mode bits; Windows ACLs unqualified')
class CheckpointStorePermissionTest(unittest.TestCase):
    def test_private_parent_and_database_work(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'anchor.db'
            initialize(p)
            self.assertEqual(read_anchor(p, SESSION), (0, ZERO))

    def test_group_writable_parent_refused_before_db_creation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'anchor.db'
            os.chmod(d, 0o770)
            with self.assertRaisesRegex(ValueError, 'parent writable'):
                initialize(path)
            self.assertFalse(path.exists())

    def test_world_writable_parent_refused_before_db_creation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'anchor.db'
            os.chmod(d, 0o707)
            with self.assertRaisesRegex(ValueError, 'parent writable'):
                initialize(path)
            self.assertFalse(path.exists())

    def test_group_writable_database_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'anchor.db'
            initialize(path)
            os.chmod(path, 0o664)
            with self.assertRaisesRegex(ValueError, 'database writable'):
                read_anchor(path, SESSION)

    def test_world_writable_database_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'anchor.db'
            initialize(path)
            os.chmod(path, 0o666)
            with self.assertRaisesRegex(ValueError, 'database writable'):
                read_anchor(path, SESSION)


if __name__ == '__main__':
    unittest.main()

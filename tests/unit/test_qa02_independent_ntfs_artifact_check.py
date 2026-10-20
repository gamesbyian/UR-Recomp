"""ROM-free negative tests for externally pinned Windows NTFS source receipts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

TOOL = Path(__file__).resolve().parents[2] / 'tools' / 'qa02_independent_ntfs_artifact_check.py'
spec = importlib.util.spec_from_file_location('ntfs_pinned', TOOL)
ntfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ntfs)
SCHEMA = 'ur-real-original-cmd-ntfs-disk-full/1'


class PinnedNTFSReceipts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'source.zip'
        self.payload = b'actual source bytes in synthetic test only'

    def archive(self, credit=0, extra=False, raw_json=None):
        manifest = {
            'schema': SCHEMA, 'release_gate_credit': credit, 'human_operator': False,
            'actual_source_bytes': {'sample.bin': {
                'sha256': hashlib.sha256(self.payload).hexdigest(),
                'bytes': len(self.payload)}}
        }
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('result.json', raw_json if raw_json is not None else json.dumps(manifest))
            z.writestr('source-bytes/sample.bin', self.payload)
            if extra:
                z.writestr('source-bytes/forged.bin', b'extra')
        return ntfs.sha(self.path.read_bytes())

    def test_authentic_synthetic_receipt_requires_external_pin(self):
        digest = self.archive()
        result, count, actual = ntfs.check(self.path, SCHEMA, digest)
        self.assertEqual((result['release_gate_credit'], count, actual), (0, 1, digest))
        with self.assertRaisesRegex(ValueError, 'external source ZIP SHA'):
            ntfs.check(self.path, SCHEMA, '0' * 64)

    def test_boolean_credit_rejected_despite_zero_equality(self):
        digest = self.archive(credit=False)
        with self.assertRaises(AssertionError):
            ntfs.check(self.path, SCHEMA, digest)

    def test_unlisted_source_member_rejected(self):
        digest = self.archive(extra=True)
        with self.assertRaisesRegex(AssertionError, 'unlisted source'):
            ntfs.check(self.path, SCHEMA, digest)

    def test_duplicate_and_nonfinite_json_rejected(self):
        for bad in (
            '{"schema":"x","schema":"y"}',
            '{"schema":"x","value":1e999}',
            '{"schema":"x","value":NaN}',
        ):
            digest = self.archive(raw_json=bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ntfs.check(self.path, SCHEMA, digest)

    def test_symlinked_ancestor_refused_even_with_valid_sha(self):
        digest = self.archive()
        real = self.root / 'real'
        real.mkdir()
        copy = real / 'source.zip'
        copy.write_bytes(self.path.read_bytes())
        link = self.root / 'redirected-parent'
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'redirected source archive ancestor'):
            ntfs.check(link / 'source.zip', SCHEMA, digest)
        ntfs.check(copy, SCHEMA, digest)

    def test_symlinked_archive_rejected(self):
        digest = self.archive()
        alias = self.root / 'alias.zip'
        alias.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            ntfs.check(alias, SCHEMA, digest)


if __name__ == '__main__':
    unittest.main()

"""Recovered source-archive Git-blob crosswalk never self-awards integration."""
import io
import sys
import unittest
import warnings
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from recovery_member_blob_crosswalk import crosswalk, git_blob, index_git_tree


def archive(entries, *, compression=zipfile.ZIP_DEFLATED):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=compression) as z:
        for key, value in entries:
            z.writestr(key, value)
    return stream.getvalue()


def tree(entries):
    return b''.join((b'100644 blob ' + git_blob(value).encode() + b'\t' +
                     path.encode() + b'\0') for path, value in entries)


class MemberCrosswalk(unittest.TestCase):
    def test_exact_renamed_member_remains_only_a_hint(self):
        src = b'print(1)\n'
        r = crosswalk(archive([('handoff/code.py', src)]),
                      tree([('tools/current.py', src)]))
        self.assertEqual(r['exact_blob_occurrences'], 1)
        self.assertFalse(r['items'][0]['same_path'])
        self.assertEqual(r['items'][0]['git_paths'], ['tools/current.py'])
        self.assertFalse(r['archive_deletion_authorized'])
        self.assertEqual(r['automatic_integration_decisions'], 0)
        self.assertFalse(r['member_manifest_authenticated'])
        self.assertEqual(r['release_gate_credit'], 0)

    def test_exact_member_and_changed_member_are_distinct(self):
        r = crosswalk(archive([('tools/x.py', b'good'), ('tests/test_x.py', b'bad')]),
                      tree([('tools/x.py', b'good')]))
        self.assertEqual([v['status'] for v in r['items']],
                         ['exact_git_blob_observed', 'unmatched_needs_review'])
        self.assertTrue(r['items'][0]['same_path'])
        self.assertEqual(r['unmatched_or_unexamined'], 1)

    def test_nested_members_get_explicit_provenance_prefix(self):
        child = archive([('a.cpp', b'int main() {return 0;}')])
        outer = archive([('child.zip', child)])
        r = crosswalk(outer, tree([('tests/a.cpp', b'int main() {return 0;}')]))
        self.assertEqual(r['nested_archives_encountered'], 1)
        self.assertEqual(r['items'][0]['member'], 'child.zip!/a.cpp')
        self.assertEqual(r['exact_blob_occurrences'], 1)
        limited = crosswalk(outer, tree([]), max_depth=0)
        self.assertEqual(limited['items'][0]['status'], 'nested_unexamined_depth_limit')

    def test_patch_is_never_assumed_applied(self):
        p = b'--- a/x.py\n+++ b/x.py\n'
        r = crosswalk(archive([('delta.patch', p)]), tree([]))
        self.assertEqual(r['items'][0]['kind'], 'patch')
        self.assertEqual(r['items'][0]['status'], 'unmatched_needs_review')

    def test_duplicate_and_traversal_refused(self):
        for name in ('../escape.py', '/tmp/escape.py', 'a/../escape.py'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unsafe'):
                crosswalk(archive([(name, b'x')]), tree([]))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            bad = archive([('a.py', b'a'), ('a.py', b'b')])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            crosswalk(bad, tree([]))

    def test_win32_nonportable_names_refused_even_with_matching_git_blob(self):
        rejected = (
            'CON.txt', 'safe/COM¹.log', 'safe/LPT².txt',
            'safe/stream:ads.py', 'safe/file. ', 'e\u0301.py',
            'control\u0085.py',
        )
        for name in rejected:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unsafe'):
                crosswalk(archive([(name, b'x')]), tree([(name, b'x')]))
        self.assertEqual(
            crosswalk(archive([('safe/résumé.py', b'good'),
                               ('safe/name².py', b'valid')]),
                      tree([]))['source_like_members'], 2)

    def test_portable_file_directory_prefix_collision_refused(self):
        for entries in (
            [('node', b'a'), ('node/leaf.py', b'b')],
            [('NODE', b'a'), ('node/leaf.py', b'b')],
            [('node/leaf.py', b'b'), ('node', b'a')],
        ):
            with self.subTest(names=[x[0] for x in entries]), self.assertRaisesRegex(
                    ValueError, 'prefix collision'):
                crosswalk(archive(entries), tree([]))

    def test_nested_archive_path_must_be_portable_itself(self):
        nested = archive([('safe/CON.txt', b'bad')])
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            crosswalk(archive([('inner.zip', nested)]), tree([]))

    def test_corrupt_zip_is_integrity_failure(self):
        with self.assertRaisesRegex(ValueError, 'invalid or corrupt'):
            crosswalk(b'bad', tree([]))

    def test_bad_git_tree_refused(self):
        with self.assertRaisesRegex(ValueError, 'NUL-terminated'):
            index_git_tree(b'100644 blob ' + b'a'*40 + b'\tx.py')
        with self.assertRaisesRegex(ValueError, 'invalid git'):
            index_git_tree(b'100644 blob nope\tx.py\0')

    def test_crc_failure_refused_even_when_git_source_matches(self):
        data = archive([('code.py', b'PAYLOAD_ONLY_CRC')],
                       compression=zipfile.ZIP_STORED)
        damaged = bytearray(data)
        idx = damaged.find(b'PAYLOAD_ONLY_CRC')
        self.assertGreaterEqual(idx, 0)
        damaged[idx] ^= 1
        with self.assertRaisesRegex(ValueError, 'invalid or corrupt'):
            crosswalk(bytes(damaged), tree([('code.py', b'PAYLOAD_ONLY_CRC')]))


if __name__ == '__main__':
    unittest.main()

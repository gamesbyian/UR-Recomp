"""ROM-free nested recovery provenance checks; not release/source acceptance."""
import hashlib
import io
import json
import sys
import unittest
import warnings
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from recovery_zip_admission import admit


def package(members, *, manifests=True):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,payload in members.items():z.writestr(name,payload)
        if manifests:
            z.writestr('MANIFEST.json',json.dumps({'members':{
                name:{'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}
                for name,value in members.items()}}))
    return output.getvalue()

class RecoveryZipAdmissionTest(unittest.TestCase):
    def test_recursively_authenticates_nested_manifest_members(self):
        inner=package({'source/a.py':b'print(1)\n'})
        outer=package({'nested.zip':inner,'notes.txt':b'no release acceptance'})
        r=admit(outer)
        self.assertEqual(r['members'],2)
        self.assertTrue(r['complete_recursive_admission'])
        self.assertEqual(r['nested'][0]['status'],'manifest_verified')
        self.assertEqual(r['release_gate_credit'],0)

    def test_nested_zip_without_complete_manifest_is_unqualified(self):
        nested=package({'source.py':b'print(1)'},manifests=False)
        r=admit(package({'nested.zip':nested}))
        self.assertFalse(r['complete_recursive_admission'])
        self.assertEqual(r['nested'][0]['status'],'nested_member_manifest_missing')

    def test_member_tampering_is_rejected_after_repacking(self):
        blob=package({'file.txt':b'original'})
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            old_manifest=z.read('MANIFEST.json')
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as z:
            z.writestr('file.txt',b'altered')
            z.writestr('MANIFEST.json',old_manifest)
        with self.assertRaisesRegex(ValueError,'mismatch'):
            admit(output.getvalue())

    def test_duplicate_and_traversal_names_fail_closed(self):
        for name in ('../outside.txt','/absolute.txt'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                admit(package({name:b'bad'}))
        output=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(output,'w') as z:
                z.writestr('file.txt',b'one')
                z.writestr('file.txt',b'two')
        with self.assertRaises(ValueError):admit(output.getvalue())

    def test_nested_members_obey_canonical_win32_portability(self):
        # Valid CRC and internally consistent digests are insufficient.
        rejected = (
            {'CON.txt': b'x'},
            {'safe/LPT².log': b'x'},
            {'bad\u0085.txt': b'x'},
            {'safe/stream:ads': b'x'},
            {'safe/file. ': b'x'},
            {'e\u0301.txt': b'x'},
            {'A.txt': b'a', 'a.TXT': b'b'},
            {'node': b'a', 'node/leaf.py': b'b'},
        )
        for entries in rejected:
            with self.subTest(names=list(entries)), self.assertRaisesRegex(
                    ValueError, 'unsafe ZIP member|portable ZIP'):
                admit(package(entries))
        self.assertEqual(
            admit(package({'safe/résumé.py': b'good',
                           'safe/name².txt': b'also good'}))['members'], 2)

    def test_nonportable_child_rejected_even_with_valid_outer_manifest(self):
        inner = package({'safe/CON.txt': b'invalid'})
        outer = package({'safe/nested.zip': inner})
        with self.assertRaisesRegex(ValueError, 'unsafe ZIP member'):
            admit(outer)

    def test_bad_outer_zip_bytes_are_a_bounded_integrity_failure(self):
        for bad in (b'not a ZIP', b'PK\\x03\\x04'):
            with self.subTest(bad=bad), self.assertRaisesRegex(
                    ValueError, 'invalid or corrupt recovery ZIP'):
                admit(bad)

    def test_corrupt_nested_zip_is_rejected_by_parent(self):
        # Parent's own manifest accurately hashes the invalid nested member.
        # The child must not escape as an unhandled BadZipFile exception.
        outer = package({'nested.zip': b'not a ZIP'})
        with self.assertRaisesRegex(ValueError, 'invalid or corrupt recovery ZIP'):
            admit(outer)

    def test_crc_corruption_has_a_stable_recovery_failure(self):
        payload = b'ZIP_PAYLOAD_CRC_CANARY'
        digest = hashlib.sha256(payload).hexdigest()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as z:
            z.writestr('source.py', payload)
            z.writestr('MANIFEST.json', json.dumps({'members': {
                'source.py': {'bytes': len(payload), 'sha256': digest}
            }}))
        changed = bytearray(stream.getvalue())
        position = changed.find(payload)
        self.assertGreaterEqual(position, 0)
        changed[position] ^= 1
        with self.assertRaisesRegex(ValueError, 'invalid or corrupt recovery ZIP'):
            admit(bytes(changed))

    def test_depth_and_invalid_input_fail_closed(self):
        inner=package({'a.txt':b'a'})
        outer=package({'nested.zip':inner})
        with self.assertRaisesRegex(ValueError,'depth'):
            admit(outer,depth=3,max_depth=2)
        with self.assertRaises(ValueError):admit('not bytes')

if __name__=='__main__':unittest.main()

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

    def test_depth_and_invalid_input_fail_closed(self):
        inner=package({'a.txt':b'a'})
        outer=package({'nested.zip':inner})
        with self.assertRaisesRegex(ValueError,'depth'):
            admit(outer,depth=3,max_depth=2)
        with self.assertRaises(ValueError):admit('not bytes')

if __name__=='__main__':unittest.main()

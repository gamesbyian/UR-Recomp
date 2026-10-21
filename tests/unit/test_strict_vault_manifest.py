"""Portable recovery manifest integrity is not authority for any release gate."""
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from strict_vault_manifest import verify

def pack(data):
    manifest={name:{"bytes":len(value),"sha256":hashlib.sha256(value).hexdigest()}
              for name,value in data.items()}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        for name,value in data.items():z.writestr(name,value)
        z.writestr("MANIFEST.json",json.dumps(manifest))
    return stream.getvalue()

class StrictVaultManifest(unittest.TestCase):
    def test_complete_integrity_only(self):
        raw=pack({"safe/code.py":b"print(1)"})
        result=verify(raw,expected_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["manifested_payloads"],1)
        self.assertEqual(result["release_gate_credit"],0)
        self.assertTrue(result["integrity_only"])

    def test_outer_digest_needed_to_bind_external_identity(self):
        with self.assertRaisesRegex(ValueError,"outer archive SHA"):
            verify(pack({"x":b"x"}),expected_sha256="0"*64)

    def test_reserved_name_and_prefix_collision(self):
        for files in ({"CON":b"no"},{"safe/PRN.txt":b"no"},
                      {"a":b"file","a/b":b"conflict"},
                      {"safe.txt":b"1","SAFE.TXT":b"2"}):
            with self.subTest(files=files),self.assertRaises(ValueError):
                verify(pack(files))

    def test_hash_mismatch_refuses(self):
        raw=pack({"x":b"x"})
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            manifest=json.loads(z.read("MANIFEST.json"))
        manifest["x"]["sha256"]="0"*64
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z:
            z.writestr("x",b"x")
            z.writestr("MANIFEST.json",json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,"hash/size"):
            verify(stream.getvalue())

    def test_unicode_alias_and_control(self):
        for name in ("e\u0301.txt","bad\u202etxt","bad. ","NUL.log"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                verify(pack({name:b"x"}))

if __name__=="__main__":
    unittest.main()

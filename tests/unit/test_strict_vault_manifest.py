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

    def test_extended_win32_aliases_controls_and_utf16_component_lengths(self):
        # These have valid ZIP CRCs and internally consistent manifests but
        # are unsafe/nonportable as Windows extraction member names.
        rejected = (
            "bad\\u0085.txt", "bad\\u007f.txt", "COM¹.txt",
            "COM².log", "LPT³", "CON .txt", "aux .txt",
            "é" * 256 + ".txt", "😀" * 128 + ".txt",
        )
        for name in rejected:
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "unsafe archive member"):
                verify(pack({name: b"x"}))
        for name in ("normal.txt", "résumé/notes.txt",
                     "name².txt", "COM0.txt", "é" * 251 + ".txt"):
            with self.subTest(name=name):
                self.assertEqual(verify(pack({name: b"x"}))["manifested_payloads"], 1)

    def test_unix_nonregular_zip_members_are_not_portable_sources(self):
        # Valid CRC and matching manifest do not make Unix special entries
        # ordinary files. A recovery handoff must not certify such metadata.
        import stat
        payload = b"print(1)"
        manifest = {"safe/source.py": {
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}}
        modes = (stat.S_IFIFO, stat.S_IFCHR, stat.S_IFBLK,
                 stat.S_IFSOCK, stat.S_IFLNK, stat.S_IFDIR, stat.S_IFREG)
        for mode in modes:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as z:
                info = zipfile.ZipInfo("safe/source.py")
                info.create_system = 3
                info.external_attr = (mode | 0o644) << 16
                z.writestr(info, payload)
                z.writestr("MANIFEST.json", json.dumps(manifest))
            with self.subTest(mode=oct(mode)):
                if mode == stat.S_IFREG:
                    self.assertEqual(verify(stream.getvalue())["manifested_payloads"], 1)
                else:
                    with self.assertRaisesRegex(ValueError, "unsafe archive member"):
                        verify(stream.getvalue())

    def test_win32_forbidden_punctuation_components(self):
        # Valid CRC and manifest hashes cannot make these Win32 path names safe.
        for name in (
            "bad<name.txt", "bad>name.txt", 'bad"name.txt',
            "bad|name.txt", "bad?name.txt", "bad*name.txt",
            "safe/bad|nested.txt", "safe/x?y/code.py",
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "unsafe archive member"):
                verify(pack({name: b"first party test bytes"}))

    def test_unicode_alias_and_control(self):
        for name in ("e\u0301.txt","bad\u202etxt","bad. ","NUL.log"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                verify(pack({name:b"x"}))

if __name__=="__main__":
    unittest.main()

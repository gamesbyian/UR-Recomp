"""Independent ROM-free QA01 RF076 ZIP and physical opcode event adversarial gates."""
from __future__ import annotations
import hashlib
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf076_original_fetch_archive as audit

class RF076SourceIntake(unittest.TestCase):
    def make(self, target, names, *, symlink=False, duplicate=False):
        with zipfile.ZipFile(target,"w") as z:
            for name in names:
                if symlink:
                    info=zipfile.ZipInfo(name)
                    info.create_system=3
                    info.external_attr=(stat.S_IFLNK|0o777)<<16
                    z.writestr(info,"other")
                else:
                    z.writestr(name,b"data")
            if duplicate:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",UserWarning)
                    z.writestr(names[0],b"second")
        return hashlib.sha256(target.read_bytes()).hexdigest()

    def test_missing_and_wrong_source_digest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"missing.zip"
            with self.assertRaisesRegex(ValueError,"missing/symlinked"):
                audit.opened_zip(p,audit.CASE_SHA,418,70000000)
            sha=self.make(p,["normal.json"])
            with self.assertRaisesRegex(ValueError,"original ZIP SHA256 mismatch"):
                audit.opened_zip(p,audit.CASE_SHA,1,10000)
            with self.assertRaisesRegex(ValueError,"member population altered"):
                audit.opened_zip(p,sha,2,10000)

    def test_rehashed_cross_platform_aliases_rejected(self):
        for bad in ("../escape","nested//alias","nested/./alias","nested\\alias",
                    "C:ads","nested/trailing./alias","control\nbyte"):
            with self.subTest(bad=bad),tempfile.TemporaryDirectory() as d:
                path=Path(d)/"case.zip"
                sha=self.make(path,["real.json",bad])
                with self.assertRaisesRegex(ValueError,"unsafe"):
                    audit.opened_zip(path,sha,2,10000)

    def test_rehashed_duplicate_member_or_symlink_rejected(self):
        for kind in ("symlink","duplicate"):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                p=Path(d)/"case.zip"
                sha=self.make(p,["safe.json"],symlink=kind=="symlink",
                              duplicate=kind=="duplicate")
                with self.assertRaises(ValueError):
                    audit.opened_zip(p,sha,2 if kind=="duplicate" else 1,10000)

    def test_original_source_fetch_ordinals_strict(self):
        good=b"QA01RF076ORIGPC seq=1 stage=fetch f=1017 actualFetchedPC=82D4EE fetchedOpcode=24 S=01F0 v=132 h=510 wai=0\n"
        rows,stages,mixed=audit.read_events(good,"QA01RF076ORIGPC seq=",1)
        self.assertEqual(stages["fetch"],1)
        self.assertEqual(len(rows),1)
        self.assertFalse(mixed)
        for bad in (good.replace(b"seq=1",b"seq=2"),
                    good.replace(b"f=1017",b"f=999"),
                    good.replace(b"wai=0",b"wai=0 invalid"),
                    good.replace(b"stage=fetch",b"stage=fetch stage=read")):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                audit.read_events(bad,"QA01RF076ORIGPC seq=",1)

    def test_native_physical_interleave_counted_not_silently_cleared(self):
        mixed=(b"QA01RF044NATIVE f=1017 partial "
               b"QA01RF047NATIVE seq=1 stage=read f=1017 addr=01ED value=26\n")
        rows,stages,prefix=audit.read_events(mixed,"QA01RF047NATIVE seq=",1)
        self.assertEqual(rows[0]["seq"],1)
        self.assertEqual(stages["read"],1)
        self.assertEqual(prefix["read"],1)

    def test_double_encoded_native_marker_rejected(self):
        line=(b"QA01RF047NATIVE seq=1 stage=read f=1017 "
              b"QA01RF047NATIVE seq=1 stage=read f=1017")
        with self.assertRaisesRegex(ValueError,"multiple event tags"):
            audit.read_events(line,"QA01RF047NATIVE seq=",1)

if __name__=="__main__":
    unittest.main()

"""Adversarial ROM-free RF079 authentic original/native BIT/BPL archive gates."""
from __future__ import annotations
import hashlib
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf079_bit_bpl_archive as target

class RF079SourceAdmissionTests(unittest.TestCase):
    def zipped(self,path,names,*,symlink=False,duplicate=False):
        with zipfile.ZipFile(path,"w") as z:
            for name in names:
                if symlink:
                    member=zipfile.ZipInfo(name)
                    member.create_system=3
                    member.external_attr=(stat.S_IFLNK|0o777)<<16
                    z.writestr(member,b"symlink target")
                else:
                    z.writestr(name,b"evidence")
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",UserWarning)
                    z.writestr(names[0],b"duplicated")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_source_sha_or_source_population_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"case.zip"
            with self.assertRaisesRegex(ValueError,"missing or symlinked"):
                target.source_zip(p,target.CASE_SHA,199,45000000)
            sha=self.zipped(p,["report.json"])
            with self.assertRaisesRegex(ValueError,"wrong exact source ZIP"):
                target.source_zip(p,target.CASE_SHA,1,1000)
            with self.assertRaisesRegex(ValueError,"wrong genuine original ZIP population"):
                target.source_zip(p,sha,2,1000)

    def test_rehashed_invalid_cross_platform_paths_rejected(self):
        for name in ("../escape","nested//double","nested/./dot","nested\\win",
                     "ADS:payload","trailing./file","bad\ncontrol"):
            with self.subTest(path=name),tempfile.TemporaryDirectory() as d:
                p=Path(d)/"forged.zip"
                sha=self.zipped(p,["clean.txt",name])
                with self.assertRaisesRegex(ValueError,"unsafe special"):
                    target.source_zip(p,sha,2,5000)

    def test_symlinks_duplicate_members_rejected_even_if_rehashed(self):
        for kind in ("symlink","duplicate"):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                p=Path(d)/"case.zip"
                sha=self.zipped(p,["raw.txt"],symlink=kind=="symlink",
                                duplicate=kind=="duplicate")
                with self.assertRaises(ValueError):
                    target.source_zip(p,sha,2 if kind=="duplicate" else 1,5000)

    def test_source_opcode_event_contiguous_ordinals(self):
        good=b"QA01RF079ORIG seq=1 f=1017 before=82D4EE opcode=24 after=82D4F0 D=0000 M=1 Nbyte=00 N=0 phase=after_real_guest_opcode\n"
        ls,events,mixed=target.physical_events(good,target.OTAG,1)
        self.assertEqual(events[0][1]["opcode"],"24")
        self.assertFalse(mixed)
        for bad in (good.replace(b"seq=1",b"seq=2"),
                    good.replace(b"after=82D4F0",b"after=82D4F0 duplicate=1 invalid"),
                    good.replace(b"N=0",b"N=0 N=1"),
                    good+good):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                target.physical_events(bad,target.OTAG,1)

    def test_interleaved_native_logger_rows_are_visible_and_counted(self):
        mixed=(b"QA01RF044NATIVE partial row "
               b"QA01RF047NATIVE seq=1 stage=bit_real_return f=1017 addr=0057 value=FF\n")
        _,events,counts=target.physical_events(mixed,target.NTAG,1)
        self.assertEqual(events[0][1]["value"],"FF")
        self.assertEqual(counts["bit_real_return"],1)
        bad=mixed+mixed
        with self.assertRaisesRegex(ValueError,"ambiguous duplicate source event tag|noncontiguous"):
            target.physical_events(bad.replace(b"\n",b""),target.NTAG,2)

    def test_missing_or_duplicated_real_NMI_anchor_rejected(self):
        lines=["QA01RF076ORIGPC seq=1 stage=nmi_before f=1017 actualFetchedPC=82D4F0",
               "QA01RF079ORIG seq=1 f=1017 before=82D4F0"]
        rows=[(1,{"f":"1017","stage":"post_op"})]
        self.assertEqual(len(target.first_after(lines,rows,"stage=nmi_before",1017,1)),1)
        with self.assertRaisesRegex(ValueError,"missing or duplicate"):
            target.first_after(lines+lines,rows,"stage=nmi_before",1017,1)
        with self.assertRaisesRegex(ValueError,"missing or duplicate"):
            target.first_after(lines,rows,"stage=nmi_before",1018,1)

if __name__=="__main__":
    unittest.main()

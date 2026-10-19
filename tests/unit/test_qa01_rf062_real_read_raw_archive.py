"""RF062 genuine archived native operand consumer, without a proprietary ROM."""
import copy
import hashlib
import io
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_real_read_raw_archive as probe


def fixture():
    rows=[]
    for i in range(10):
        a=0xC770+i
        value="D0" if i==4 else "22"
        master=2000+i*500
        state=(f"addr=11{a:04X} master={master} A={0x5F00+i:04X} "
               f"Y={a:04X} D=0000")
        rows.append(f"QA01RF054NATIVEBUS kind=read8 seq={i+1} frame=6124 {state} "
                    "dp63=00 dp64=00 dp65=11 scope=Snd_UploadBlockList_82EF_M1X0")
        rows.append(f"QA01RF062NATIVE seq={i+1} f=6124 executedPC=8282F0 {state} "
                    f"value={value} dp63=00 dp64=00 dp65=11")
    return "\n".join(rows)+"\n"



def helper_rows(start: int, end: int):
    return [{
        "seq":str(i-start+1), "frame":"6124",
        "kind":"read8", "scope":"Snd_UploadBlockList_82EF_M1X0",
        "addr":f"11{i:04X}", "A":f"{(i+0x10)&65535:04X}",
        "Y":f"{i:04X}", "D":"0000",
        "dp63":"00","dp64":"00","dp65":"11",
        "master":str(i*540),
    } for i in range(start,end)]


class ArchiveIdentityIntegrity(unittest.TestCase):
    def make(self, destination, *, extra=None, duplicate=False, symlink=False):
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("producer-report.json", b'{"admission":0}')
            if extra:
                z.writestr(extra, b"outside the genuine run")
            if duplicate:
                # This is ambiguous even if an attacker rehashes the new ZIP.
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    z.writestr("producer-report.json", b'{"admission":1}')
            if symlink:
                info=zipfile.ZipInfo("substitute-input")
                info.create_system=3
                info.external_attr=(stat.S_IFLNK | 0o777) << 16
                z.writestr(info, b"/another-evidence-file")
        return hashlib.sha256(destination.read_bytes()).hexdigest()

    def test_all_four_real_research_cases_have_separate_immutable_sha_pins(self):
        sha=[probe.BASELINE_SHA,probe.NATIVE_CASE_SHA,
             probe.NATIVE_BINARIES_SHA,probe.RAW_PAIR_CASE_SHA]
        self.assertEqual(len(sha),len(set(sha)))
        self.assertTrue(all(len(x)==64 for x in sha))

    def test_qualified_source_bytes_remain_immutable_if_path_changes(self):
        # The ZIP actually parsed must be the same byte snapshot whose outer
        # digest, complete members and CRCs were qualified, even if another
        # process replaces the pathname between qualification and parsing.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "case.zip"
            original_sha = self.make(path)
            actual, image = probe.qualified_zip_snapshot(path, original_sha, "fixture")
            self.assertEqual(actual, original_sha)
            self.make(path, extra="unqualified-replacement.txt")
            self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                                original_sha)
            with zipfile.ZipFile(io.BytesIO(image)) as z:
                self.assertEqual(z.namelist(), ["producer-report.json"])
                self.assertEqual(z.read("producer-report.json"),
                                 b'{"admission":0}')
            with self.assertRaisesRegex(ValueError, "SHA256 differs"):
                probe.qualified_zip_snapshot(path, original_sha, "fixture")

    def test_altered_even_unconsumed_member_does_not_requalify_zip(self):
        with tempfile.TemporaryDirectory() as d:
            from pathlib import Path
            root=Path(d)
            path=root/"case.zip"
            genuine=self.make(path)
            self.assertEqual(probe.independently_pin_zip(path,genuine,"fixture"),genuine)
            self.make(path,extra="irrelevant.txt")
            with self.assertRaisesRegex(ValueError,"SHA256 differs"):
                probe.independently_pin_zip(path,genuine,"fixture")

    def test_rehashed_duplicate_symlink_or_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            from pathlib import Path
            root=Path(d)
            for fault in ("duplicate","symlink","traversal"):
                with self.subTest(fault=fault):
                    path=root/(fault+".zip")
                    checksum=self.make(
                        path,
                        duplicate=fault=="duplicate",
                        symlink=fault=="symlink",
                        extra="../outside.json" if fault=="traversal" else None)
                    with self.assertRaisesRegex(ValueError,"unsafe, ambiguous"):
                        probe.independently_pin_zip(path,checksum,"fixture")

    def test_rehashed_cross_platform_member_aliases_fail_closed(self):
        # POSIX Path.parts alone does not reject Windows separators, drives or
        # alternate data streams. Even a newly rehashed synthetic ZIP is unsafe.
        bad_names = (
            "nested\\\\..\\\\escape.json", "C:/absolute-on-windows.json",
            "member:alternate-stream", "nested//duplicate-separator.json",
            "nested/./normalized-alias.json", "nested/../escape.json",
            "trailing./member.json", "newline\\nmember.json",
        )
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i, bad in enumerate(bad_names):
                with self.subTest(bad=bad):
                    archive = root / f"alias-{i}.zip"
                    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                        z.writestr("normal.json", b"{}")
                        z.writestr(bad, b"forged")
                    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
                    with self.assertRaisesRegex(ValueError, "unsafe, ambiguous"):
                        probe.independently_pin_zip(archive, checksum, "synthetic alias")

    def test_rehashed_nonregular_unix_zip_entries_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            for kind in (stat.S_IFDIR, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFBLK,
                         stat.S_IFSOCK):
                with self.subTest(kind=kind):
                    archive = Path(d) / f"special-{kind}.zip"
                    info = zipfile.ZipInfo("looks-like-ordinary-file")
                    info.create_system = 3
                    info.external_attr = (kind | 0o644) << 16
                    with zipfile.ZipFile(archive, "w") as z:
                        z.writestr(info, b"forged")
                    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
                    with self.assertRaisesRegex(ValueError, "unsafe, ambiguous"):
                        probe.independently_pin_zip(archive, checksum,
                                                   "synthetic special file")

    def test_rehashed_invalid_member_crc_is_not_original_source_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            from pathlib import Path
            root=Path(d)
            path=root/"case.zip"
            with zipfile.ZipFile(path,"w",zipfile.ZIP_STORED) as z:
                z.writestr("producer-report.json",b"AAAABBBBCCCCDDDD")
            data=path.read_bytes()
            self.assertEqual(data.count(b"AAAABBBBCCCCDDDD"),1)
            path.write_bytes(data.replace(b"AAAABBBBCCCCDDDD",b"AAAABBBBCCCDDDDD"))
            # Even a hash pin chosen by a forger for the corrupt ZIP
            # must not bypass the independently reopened member CRC.
            with self.assertRaisesRegex(ValueError,"CRC"):
                probe.independently_pin_zip(
                    path,hashlib.sha256(path.read_bytes()).hexdigest(),"fixture")

    def test_file_alias_and_absent_zip_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as d:
            from pathlib import Path
            root=Path(d)
            path=root/"case.zip"
            good=self.make(path)
            alias=root/"alias.zip"
            alias.symlink_to(path)
            for target in (alias,root/"missing.zip"):
                with self.subTest(target=str(target)),self.assertRaisesRegex(
                        ValueError,"missing, symlinked"):
                    probe.independently_pin_zip(target,good,"fixture")


class AuthenticNativeOpcodeRead(unittest.TestCase):
    def test_observed_frame_boundary_shift_not_an_interior_missing_read(self):
        base=helper_rows(0xC589,0xC819)
        revised=helper_rows(0xC58B,0xC81A)
        result=probe.compare_native_helper_windows(base,revised)
        self.assertEqual(result["baseline_helper_rows"],656)
        self.assertEqual(result["instrumented_helper_rows"],655)
        self.assertEqual(result["matched_address_and_register_rows_in_order"],654)
        self.assertEqual(result["baseline_rows_not_matched"],2)
        self.assertEqual(result["instrumented_rows_not_matched"],1)
        self.assertTrue(result["all_omissions_additions_confined_to_frame_edges"])
        self.assertEqual([x["change"] for x in result["observed_population_edits"]],
                         ["delete","insert"])
        self.assertFalse(result["wrapper_causal_noninterference_proven"])

    def test_interior_missing_helper_is_never_disguised_as_window_shift(self):
        base=helper_rows(0xC589,0xC595)
        revised=helper_rows(0xC58A,0xC595)
        revised.pop(3)
        revised.append(dict(revised[-1],addr="11C595",Y="C595",A="C5A5"))
        for i,row in enumerate(revised):
            row["seq"]=str(i+1)
        result=probe.compare_native_helper_windows(base,revised)
        self.assertFalse(result["all_omissions_additions_confined_to_frame_edges"])
        self.assertTrue(result["unmatched_interior_population_changes"])

    def test_swapped_register_value_is_real_interior_observation_difference(self):
        base=helper_rows(0xC589,0xC595)
        revised=copy.deepcopy(base)
        revised[5]["A"]="FFFF"
        result=probe.compare_native_helper_windows(base,revised)
        self.assertFalse(result["all_omissions_additions_confined_to_frame_edges"])
        self.assertLess(result["matched_address_and_register_rows_in_order"],len(base))

    def test_forged_clock_sequence_or_helper_type_cannot_be_aligned(self):
        base=helper_rows(0xC589,0xC595)
        for edit in ("seq","kind","frame"):
            new=copy.deepcopy(base)
            new[3][edit]={"seq":"5","kind":"write8","frame":"6125"}[edit]
            with self.subTest(edit=edit),self.assertRaisesRegex(ValueError,
                                                                 "frame-local helper"):
                probe.compare_native_helper_windows(base,new)

    def test_real_helper_join_and_target(self):
        result=probe.observed_native_reads(fixture())
        self.assertEqual(result["source_bound_native_read_count"],10)
        self.assertEqual(result["frame_6124_real_helper_read_count"],10)
        self.assertEqual(result["native_read_rows"][4]["native_returned_byte"],"D0")
        self.assertEqual(result["native_read_rows"][4]["native_read_address"],"11C774")
        self.assertEqual(result["native_read_rows"][4]["independent_native_RF054_helper_ordinal"],5)

    def test_wrong_decoded_pc_rejected(self):
        with self.assertRaisesRegex(ValueError,"native executed PC"):
            probe.observed_native_reads(fixture().replace("executedPC=8282F0",
                                                        "executedPC=0282F0"))

    def test_duplicate_helper_signature_rejected(self):
        log=fixture()
        first=next(x for x in log.splitlines()
                   if x.startswith("QA01RF054NATIVEBUS "))
        with self.assertRaisesRegex(ValueError,"helper population"):
            probe.observed_native_reads(log + first + "\n")

    def test_actual_paced_native_helper_missing_rejected(self):
        log="\n".join(x for x in fixture().splitlines()
                      if not (x.startswith("QA01RF054NATIVEBUS ") and
                              "addr=11C774" in x))
        with self.assertRaisesRegex(ValueError,"helper population"):
            probe.observed_native_reads(log)

    def test_same_value_at_different_clock_not_a_join(self):
        log=fixture().replace("QA01RF062NATIVE seq=5 f=6124 executedPC=8282F0 "
                              "addr=11C774 master=4000",
                              "QA01RF062NATIVE seq=5 f=6124 executedPC=8282F0 "
                              "addr=11C774 master=4001")
        with self.assertRaisesRegex(ValueError,"native executed PC"):
            probe.observed_native_reads(log)

    def test_false_source_byte_and_observation_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError,"ROM value differs"):
            probe.observed_native_reads(fixture().replace("value=D0", "value=D1"))
        with self.assertRaisesRegex(ValueError,"recorder overflow"):
            probe.observed_native_reads(fixture()+"QA01RF062NATIVE_TRUNCATED\n")

    def test_noncontiguous_actual_returns_rejected(self):
        with self.assertRaisesRegex(ValueError,"ten actual native"):
            probe.observed_native_reads(fixture().replace("QA01RF062NATIVE seq=5",
                                                        "QA01RF062NATIVE seq=50"))


if __name__=="__main__":
    unittest.main()

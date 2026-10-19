"""ROM-free adversarial original/native same-input epoch memory census tests."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf066_rf062_full_raw_crosswalk as census


class SourceEpochRawTests(unittest.TestCase):
    def archive(self, where: Path, *, change_native: bool = False,
                omit: bool = False, short: bool = False):
        z = zipfile.ZipFile(where,"w",zipfile.ZIP_DEFLATED)
        with z:
            for guest in ("ref", "native"):
                for kind,size in census.BYTES.items():
                    if omit and guest == "native" and kind == "wram":
                        continue
                    data = bytearray(size)
                    if change_native and guest == "native" and kind == "wram":
                        data[0x63] = 0x7A
                        data[0x1ed] = 0x26
                    if short and guest == "native" and kind == "sram":
                        data.pop()
                    z.writestr(
                        f"{census.ROOT}{guest}/scene-00001.{kind}.bin",data)
        return where

    def test_full_raw_census_only_different_native_wram(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            first=self.archive(root/"a.zip")
            second=self.archive(root/"b.zip",change_native=True)
            with zipfile.ZipFile(first) as a, zipfile.ZipFile(second) as b:
                result=census.crosswalk(a,b,count=4)
            self.assertEqual(
                result["per_guest_memory_type_identical_image_counts"],
                {"ref_wram":1,"ref_sram":1,"native_wram":0,"native_sram":1})
            self.assertEqual(
                result["per_guest_memory_type_changed_image_counts"],
                {"ref_wram":0,"ref_sram":0,"native_wram":1,"native_sram":0})
            self.assertEqual(
                result["per_guest_memory_type_changed_byte_occurrences"],
                {"ref_wram":0,"ref_sram":0,"native_wram":2,"native_sram":0})
            self.assertEqual(result["changed_byte_addresses_across_two_source_epochs"],
                             {"7E:0063":1,"7E:01ED":1})

    def test_missing_or_short_genuine_memory_fails_closed(self):
        for kind in ("missing","short"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
                root=Path(d)
                first=self.archive(root/"a.zip")
                second=self.archive(
                    root/"b.zip",omit=kind=="missing",short=kind=="short")
                with zipfile.ZipFile(first) as a, zipfile.ZipFile(second) as b:
                    with self.assertRaises(ValueError):
                        census.crosswalk(a,b,count=4)

    def test_unknown_physical_byte_type_and_length_fails_closed(self):
        with self.assertRaises(ValueError):
            census.byte_mismatches(b"x",b"x",kind="wram")
        with self.assertRaises(ValueError):
            census.byte_mismatches(b"x",b"x",kind="mystery")
        self.assertEqual(census.physical("wram",0),"7E:0000")
        self.assertEqual(census.physical("wram",65536),"7F:0000")
        self.assertEqual(census.physical("sram",11),"SRAM:000B")

    def test_source_archive_sha_pin_and_zip_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            archive=self.archive(root/"case.zip")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                census.audited_zip(archive,"f"*64,4)
            # A hash of the changed archive is not enough to permit
            # duplicate members or ambiguous authoritative source bytes.
            with zipfile.ZipFile(archive,"a") as z:
                z.writestr(f"{census.ROOT}ref/scene-00001.wram.bin",b"x")
            with self.assertRaisesRegex(ValueError,"unsafe/duplicate"):
                census.audited_zip(
                    archive,census.sha(archive.read_bytes()),5)


if __name__=="__main__":
    unittest.main()

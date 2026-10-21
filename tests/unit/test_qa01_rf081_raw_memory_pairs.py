"""Synthetic tests for source-pinned RF081 sampled memory evidence, no event credit."""
import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf081_raw_memory_pairs as qa


def sample_zip(*, mismatched=True, duplicate=False, omit_native=False):
    output=io.BytesIO()
    a=bytes(131072)
    b=bytearray(a)
    if mismatched:b[0x01f2]=1
    root=qa.ROOT
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(root+"ref/f.wram.bin",a)
        if duplicate:z.writestr(root+"ref/f.wram.bin",a)
        if not omit_native:z.writestr(root+"native/f.wram.bin",bytes(b))
        z.writestr(root+"ref/f.sram.bin",bytes(8192))
        z.writestr(root+"native/f.sram.bin",bytes(8192))
    return output.getvalue()


class RawCensusBoundaries(unittest.TestCase):
    def examine(self,source):
        with patch.object(qa,"ARCHIVE_SHA",hashlib.sha256(source).hexdigest()):
            return qa.census(source)

    def test_bounded_byte_difference_does_not_admit_event(self):
        r=self.examine(sample_zip())
        self.assertEqual(r["observations"]["wram"]["different_offsets_hex"],{"01F2":1})
        self.assertEqual(r["observations"]["sram"]["exact_pairs"],1)
        self.assertEqual(r["accepted_USA_events"],0)
        self.assertEqual(r["adjudication"],"HOLD")
        self.assertFalse(r["continuous_original_native_event_proven"])

    def test_exact_images_do_not_prove_continuous_event(self):
        r=self.examine(sample_zip(mismatched=False))
        self.assertEqual(r["observations"]["wram"]["exact_pairs"],1)
        self.assertFalse(r["sampled_semantic_phase_equivalence_proven"])

    def test_missing_native_pair_rejected(self):
        with self.assertRaisesRegex(ValueError,"incomplete original/native"):
            self.examine(sample_zip(omit_native=True))

    def test_unpinned_archive_rejected_before_zip_read(self):
        with self.assertRaisesRegex(ValueError,"digest mismatch"):
            qa.census(sample_zip())

    def test_duplicate_member_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate ZIP"):
            self.examine(sample_zip(duplicate=True))


if __name__=="__main__":
    unittest.main()

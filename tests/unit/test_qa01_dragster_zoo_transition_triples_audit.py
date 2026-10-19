"""ROM-free QA01 original/native temporal triple and SRAM mapping regressions."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_dragster_zoo_transition_triples_audit as source


class DragsterTripleTests(unittest.TestCase):
    def test_actual_address_old_new_set_intersection_excludes_wrong_values(self):
        old = bytearray(131072)
        new = bytearray(old)
        new[17]=2
        new[0x1003]=3
        a=source.mutations(old,new)
        self.assertEqual(a,{(17,0,2),(0x1003,0,3)})
        other=bytearray(old)
        other[17]=2
        other[0x1003]=4
        b=source.mutations(old,other)
        self.assertEqual(a & b,{(17,0,2)})
        self.assertEqual(len(a-b),1)

    def test_sram_displacement_value_correspondence_never_excludes_bytes(self):
        a=bytearray(131072);b=bytearray(131072)
        ar=bytearray(8192);br=bytearray(8192)
        a[0xC6]=7;b[0xC6]=5
        ar[0xC6+source.CANDIDATE_SRAM_OFFSET]=7
        br[0xC6+source.CANDIDATE_SRAM_OFFSET]=5
        a[0x89]=1;b[0x89]=3
        self.assertEqual(source.sram_correspondences(a,b,ar,br),(2,1,1))
        br[0xC6+source.CANDIDATE_SRAM_OFFSET]=4
        self.assertEqual(source.sram_correspondences(a,b,ar,br),(2,1,0))

    def test_reject_short_raw_images_and_absent_original_archive(self):
        with self.assertRaisesRegex(ValueError,"incomplete 128KiB"):
            source.mutations(bytes(32),bytes(32))
        with self.assertRaisesRegex(ValueError,"battery extent"):
            source.sram_correspondences(bytes(131072),bytes(131072),
                                        bytes(8191),bytes(8191))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"missing original"):
                source.audit(Path(d)/"not-present.zip")

    def test_archive_hash_is_mandatory_and_no_release_credit_is_given(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"dummy.zip"
            p.write_bytes(b"PK\x03\x04not a real source")
            with self.assertRaisesRegex(ValueError,"ZIP SHA"):
                source.audit(p)
        self.assertEqual(source.ARCHIVE_SHA256,
            "f036f80d72000b05a5c2edb42152eb433b89fa44c5fc36238ccc73bd143e2947")


if __name__ == "__main__":
    unittest.main()

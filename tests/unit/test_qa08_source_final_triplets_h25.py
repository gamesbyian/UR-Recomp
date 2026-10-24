"""H25 first-party QA08 source/final triplet admission, synthetic negatives only."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_probe_robustness as qa08


def lines():
    records=[]
    for i in range(88):
        identity=f"frame=5176 x={i} logical_y=41 ppu_line=42"
        records.extend((
            f"UR_QA08_LATE_PPU_SOURCE {identity} sub=0 selected_rgb555=4a52",
            f"UR_QA08_LATE_PPU_SOURCE {identity} sub=1 selected_rgb555=39ce",
            f"UR_QA08_LATE_PPU_FINAL {identity} RGB8=138,138,138",
        ))
    return records


def archive(rows, *, duplicate_member=False):
    data=BytesIO()
    with ZipFile(data,"w") as z:
        body=("\n".join(rows)+"\n").encode("ascii")
        z.writestr("on-source.log",body)
        if duplicate_member:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                z.writestr("on-source.log",body)
    return data.getvalue()


class QA08SourceFinalTripletAdmission(unittest.TestCase):
    def verify(self,rows,*,error=None,duplicate_member=False):
        raw=archive(rows,duplicate_member=duplicate_member)
        with TemporaryDirectory() as d:
            path=Path(d)/"fixture.zip"
            path.write_bytes(raw)
            with patch.object(qa08,"AUTHENTIC_SHA256",sha256(raw).hexdigest()):
                if error is not None:
                    with self.assertRaisesRegex(ValueError,error):
                        qa08.genuine_scale_compatibility(path)
                else:
                    return qa08.genuine_scale_compatibility(path)

    def test_complete_exactly_staged_synthetic_archive(self):
        result=self.verify(lines())
        self.assertEqual(result["source_triplets"],88)
        self.assertEqual(result["compatible_scalings"],{"14/15":True,"187/200":True})
        self.assertFalse(result["chromatic_source_observed"])

    def test_swapped_substage_and_final_rejected(self):
        src=lines()
        src[1],src[2]=src[2],src[1]
        self.verify(src,error="stage order")

    def test_mismatched_second_stage_coordinate_rejected(self):
        src=lines()
        src[1]=src[1].replace("x=0","x=88")
        self.verify(src,error="cross-epoch")

    def test_duplicate_source_identity_rejected_even_with_full_count(self):
        src=lines()
        src[3:6]=src[0:3]
        self.verify(src,error="duplicate QA08 source stage")

    def test_missing_substage_rejected_even_with_original_main_final_counts(self):
        src=lines()
        src[1]="UR_QA08_LATE_PPU_SOURCE frame=5176 x=0 logical_y=41 ppu_line=42 sub=0 selected_rgb555=39ce"
        self.verify(src,error="sub-stage order")

    def test_duplicate_field_and_malformed_rgb_rejected(self):
        src=lines()
        src[0]+=" frame=999"
        self.verify(src,error="duplicate or empty")
        src=lines()
        src[2]=src[2].replace("138,138,138","138,999,138")
        self.verify(src,error="out-of-range")

    def test_missing_rows_and_duplicate_zip_member_rejected(self):
        self.verify(lines()[:-1],error="incomplete")
        self.verify(lines(),duplicate_member=True,error="duplicate or corrupt")

    def test_unpinned_archive_rejected(self):
        raw=archive(lines())
        with TemporaryDirectory() as d:
            path=Path(d)/"wrong.zip"
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"unauthenticated"):
                qa08.genuine_scale_compatibility(path)


if __name__=="__main__":
    unittest.main()

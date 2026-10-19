"""RF071: real read helper must precede one actual source post-call return."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf071_original_real_read_join as tool


def source_fixture(cross=False):
    bv,bh,rv,rh=(31,1360,32,12) if cross else (31,100,31,116)
    return (
        f"QA01RF063ORIGBUS seq=1 f=1017 v={bv} h={bh} kind=rw"
        " bank=00 addr=01F0 width=2 sampled=9141 pc=82:980D S=01EF phase=getset_entry\n"
        f"QA01RF044ORIGBUS f=1017 v={bv} h={bh} kind=rw"
        " bank=00 addr=01F0 w=2 value=9141 pb=82 pc=980D S=01EF\n"
        f"QA01RF064ORIGPULL f=1017 v={rv} h={rh} kind=pullW"
        " base=01F0 width=2 returned=9141 before=0 after=1 unique=1 pc=82:9141\n"
        f"QA01RF066ORIGCONSUMED seq=2 f=1017 v={rv} h={rh}"
        " phase=post_real_stack_getter_return kind=pullW base=01F0"
        " width=2 returned=9141 before=0 after=1 bounded=0 postPB=82 postPC=9141\n"
        f"QA01RF045ORIGSTACK seq=1 f=1017 v={rv} h={rh} kind=pullW"
        " addr=01F0 width=2 value=9141 sp0=01EF sp1=01F1 pc=82:9141\n"
        "QA01RF063ORIGBUS seq=3 f=1017 v=32 h=78 kind=ww"
        " bank=00 addr=01F0 width=2 sampled=914E pc=82:914F S=01F1 phase=getset_entry\n"
        "QA01RF044ORIGBUS f=1017 v=32 h=78 kind=ww"
        " bank=00 addr=01F0 w=2 value=914E pb=82 pc=914F S=01F1\n"
        "QA01RF063ORIGCHECKPOINT seq=4 f=1017 f1=1017"
        " phase=post_real_nmi_push stack=26F0D48226 v=225 h=78 pc=00:8588\n"
        "QA01RF044ORIGNMI f=1017 f1=1017 pc=82D4F0 S0=01F0 S1=01ED"
        " old=8197005526 new=26F0D48226\n"
    )


class SourceRealReadCausality(unittest.TestCase):
    def test_one_REAL_getset_read_is_bound_to_actual_return_without_pretending_opcode(self):
        result=tool.validate_log(source_fixture())
        self.assertEqual(result["executed_source_original_getset_reads"],1)
        self.assertEqual(result["read_entries_uniquely_bound_to_real_return"],1)
        self.assertEqual(result["independent_RF044_RF063_real_getset_bus_entries"],2)
        self.assertFalse(result["real_original_getter_PC_equals_post_call_PC_in_all_cases"])
        self.assertFalse(result["native_stack_first_differing_byte_consumer_proven"])
        self.assertFalse(result["actual_opcode_fetch_PC_at_return_proven"])
        self.assertEqual(result["accepted_USA_events"],0)

    def test_real_getter_return_can_cross_Snes9x_scanline(self):
        result=tool.validate_log(source_fixture(cross=True))
        self.assertEqual(result["genuine_getter_calls_crossing_original_V_scanline"],1)

    def test_getter_and_real_post_return_disagree_is_hard_stop(self):
        raw=source_fixture()
        failures=(
            raw.replace("seq=1 f=1017","seq=5 f=1017"),
            raw.replace("seq=2 f=1017","seq=5 f=1017"),
            raw.replace("seq=3 f=1017","seq=4 f=1017"),
            raw.replace("kind=rw bank=00","kind=rb bank=00",1),
            raw.replace("sampled=9141","sampled=9142"),
            raw.replace("before=0 after=1 unique=1","before=0 after=1 unique=0"),
            raw.replace("width=2 returned=9141","width=2 returned=9142"),
            raw.replace("postPB=82 postPC=9141","postPB=83 postPC=9141"),
            raw.replace("QA01RF044ORIGBUS f=1017 v=31 h=100 kind=rw",
                        "QA01RF044ORIGBUS f=1017 v=31 h=100 kind=rb"),
            raw.replace("QA01RF044ORIGBUS f=1017 v=31 h=100 kind=rw",
                        "QA01RF044MISSING f=1017 v=31 h=100 kind=rw"),
            raw.replace("QA01RF063ORIGCHECKPOINT","QA01RF063OTHER"),
            raw+"QA01RF063ORIGBUS_TRUNCATED\n",
            raw.replace("QA01RF063ORIGBUS seq=1","out_of_scope QA01RF063ORIGBUS seq=1"),
        )
        for i,bad in enumerate(failures):
            with self.subTest(i=i),self.assertRaises(ValueError):
                tool.validate_log(bad)

    def test_original_read_entry_clock_cannot_follow_actual_return(self):
        raw=source_fixture().replace("seq=1 f=1017 v=31 h=100",
                                      "seq=1 f=1017 v=31 h=120").replace(
                                      "QA01RF044ORIGBUS f=1017 v=31 h=100",
                                      "QA01RF044ORIGBUS f=1017 v=31 h=120")
        with self.assertRaisesRegex(ValueError,"clock regressed"):
            tool.validate_log(raw)

    def test_historical_RF066_case_without_getset_reads_does_not_fake_a_transaction(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"impostor.zip"
            p.write_bytes(b"not original authenticated RF069 archive")
            with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
                tool.authenticated_case(p)


if __name__=="__main__":
    unittest.main()

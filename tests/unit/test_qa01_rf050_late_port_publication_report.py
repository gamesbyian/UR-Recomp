"""RF050 late original S9xAPUWritePort report synthetic positives/negatives."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf050_late_port_publication_report as rf

A="QA01RF050ORIGAPU seq=1 age=104350003 v=159 h=1016 port=3 val=D0"
B="QA01RF050ORIGAPU seq=2 age=104350005 v=159 h=1066 port=2 val=63"
C="QA01RF050ORIGAPU seq=3 age=104350007 v=159 h=1100 port=3 val=44"

class LatePortTest(unittest.TestCase):
    def test_bounded_true_original_publication_pair_does_not_register_clock(self):
        result=rf.analyze("\n".join([A,B,C]))
        self.assertEqual(result["late_original_real_apu_port_rows"],3)
        self.assertEqual(len(result["late_source_real_D0_63_adjacent_port_pairs"]),1)
        pair=result["late_source_real_D0_63_adjacent_port_pairs"][0]
        self.assertEqual(pair["source_spc_ages"],[104350003,104350005])
        self.assertFalse(result["source_native_clock_axes_registered"])
        self.assertFalse(pair["source_frame_6124_attested_by_APU_hook"])

    def test_missing_pair_is_explicit_not_a_false_negative(self):
        result=rf.analyze(A.replace("val=D0","val=D1")+"\n"+B)
        self.assertEqual(result["late_source_real_D0_63_adjacent_port_pairs"],[])

    def test_live_port_publication_has_to_fall_within_its_real_STA_instruction(self):
        lda=("QA01RF049LDA ordinal=33703 frame=6124 v=159 h=992 "
             "pc=82:82F0 d=0000 ptr=110000 y=C774 ea=11C774 "
             "a0=630D a1=63D0")
        sta3=("QA01RF049STA target=1 frame=6124 v=159 h=1022 "
              "pc=82:82F2 op=8D a0=63D0 a1=63D0")
        sta2=("QA01RF049STA target=1 frame=6124 v=159 h=1072 "
              "pc=82:82F6 op=8D a0=D063 a1=D063")
        live="\\n".join([lda,A,sta3,B,sta2])
        out=rf.source_instruction_publication_link(live)
        self.assertTrue(out["both_real_port_publications_inside_original_instruction_segments"])
        self.assertEqual(
            [v["source_SPC_age"] for v in
             out["source_original_STA_to_actual_APU_publications"]],
            [104350003,104350005])
        self.assertFalse(out["native_host_clock_registered"])
        absent=rf.source_instruction_publication_link(
            "\\n".join([lda,sta3,sta2]))
        self.assertFalse(absent["both_real_port_publications_inside_original_instruction_segments"])
        self.assertTrue(absent["source_original_STA_to_actual_APU_publications"][0]
                        ["missing_coverage_is_not_no_publication"])
        with self.assertRaisesRegex(ValueError,"multiple source APU publications"):
            rf.source_instruction_publication_link(
                "\\n".join([lda,A,A.replace("seq=1","seq=2"),sta3,B,sta2]))
        with self.assertRaisesRegex(ValueError,"does not match actual STA"):
            rf.source_instruction_publication_link(
                live.replace("port=3 val=D0","port=3 val=D1"))

    def test_truncation_and_spoofed_clock_fail_closed(self):
        good="\n".join([A,B])
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.analyze(good+"\nQA01RF050ORIGAPU_TRUNCATED")
        with self.assertRaisesRegex(ValueError,"sequence lost"):
            rf.analyze(good.replace("seq=2","seq=3"))
        with self.assertRaisesRegex(ValueError,"SPC age regressed"):
            rf.analyze(good.replace("104350005","104349999"))
        with self.assertRaisesRegex(ValueError,"beam gate"):
            rf.analyze(good.replace("h=1066","h=1600"))
        with self.assertRaisesRegex(ValueError,"port/value"):
            rf.analyze(good.replace("port=2","port=4"))
if __name__=="__main__":
    unittest.main()

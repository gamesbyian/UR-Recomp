"""RF050 retrospective alias ordering is not a transaction attribution."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf050_prior_payload_alias_report as rf

O1="QA01RF037ORIGCPU2 bucket=53 age=104162887 v=186 h=1286 port=3 val=D0"
O2="QA01RF037ORIGCPU2 bucket=53 age=104162889 v=186 h=1336 port=2 val=63"
N1="QA01RF037NATIVEUP kind=rtl-apu-enter frame=6105 master=2181986178 reg=2143 val=D0 scope=Snd_UploadBlockList_82EF_M1X0"
N2="QA01RF037NATIVEUP kind=rtl-apu-enter frame=6105 master=2181986228 reg=2142 val=63 scope=Snd_UploadBlockList_82EF_M1X0"
L="QA01RF049LDA ordinal=33703 frame=6124 v=159 h=992 pc=82:82F0 d=0000 ptr=110000 y=C774 ea=11C774 a0=630D a1=63D0"
S1="QA01RF049STA target=1 frame=6124 v=159 h=1022 pc=82:82F2 op=8D a0=63D0 a1=63D0"
S2="QA01RF049STA target=1 frame=6124 v=159 h=1072 pc=82:82F6 op=8D a0=D063 a1=D063"

class EarlierAliasTests(unittest.TestCase):
    def test_equal_bytes_do_not_establish_transaction_identity(self):
        result=rf.analyze("\n".join((O1,O2,L,S1,S2)),"\n".join((N1,N2)))
        self.assertEqual(result["older_D0_63_zero_based_writer_pair_ordinals"],[0,1])
        self.assertTrue(result["original_writer_capture_ends_before_later_LDA"])
        self.assertFalse(result["late_original_real_S9xAPUWritePort_publication_proven_by_this_archive"])
        self.assertFalse(result["source_original_CPU_frame_to_native_host_registered"])

    def test_refuse_missing_duplicate_or_reordered_alias(self):
        src="\n".join((O1,O2,L,S1,S2))
        nat="\n".join((N1,N2))
        with self.assertRaisesRegex(ValueError,"absent or not unique"):
            rf.analyze(src,"\n".join((N1,N2,N1,N2)))
        with self.assertRaisesRegex(ValueError,"prefix ordinals disagree"):
            rf.analyze(src,"\n".join((N1.replace("val=D0","val=10"),N1,N2)))
        with self.assertRaisesRegex(ValueError,"does not precede"):
            rf.analyze("\n".join((L,S1,S2,O1,O2)),nat)
        with self.assertRaisesRegex(ValueError,"do not encode"):
            rf.analyze(src.replace("a0=D063","a0=D064"),nat)
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.analyze(src+"\nQA01RF037ORIGCPU2_TRUNCATED",nat)
if __name__=="__main__":unittest.main()

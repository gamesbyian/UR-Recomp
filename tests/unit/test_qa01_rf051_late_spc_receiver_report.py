"""RF051 independent source/native clocks and genuine late sender gate."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf051_late_spc_receiver_report as rf

L="QA01RF049LDA ordinal=33703 frame=6124 v=159 h=992 pc=82:82F0 d=0000 ptr=110000 y=C774 ea=11C774 a0=630D a1=63D0"
A="QA01RF050ORIGAPU seq=21 age=104485254 v=159 h=1016 port=3 val=D0"
S1="QA01RF049STA target=1 frame=6124 v=159 h=1022 pc=82:82F2 op=8D a0=63D0 a1=63D0"
B="QA01RF050ORIGAPU seq=22 age=104485258 v=159 h=1066 port=2 val=63"
S2="QA01RF049STA target=1 frame=6124 v=159 h=1072 pc=82:82F6 op=8D a0=D063 a1=D063"
F7="QA01RF051ORIGSPC ordinal=1 age=104485261 v=159 h=1130 pc=1234 opcode=52 cycle=2 debt=-5 port=3 val=D0"
F6="QA01RF051ORIGSPC ordinal=2 age=104485263 v=159 h=1160 pc=1235 opcode=53 cycle=3 debt=-2 port=2 val=63"
N1="QA01RF051NATIVE ordinal=1 kind=schedule frame=6124 clock=104485250 target=104485255 pc=0200 port=3 val=D0 queue=1"
N2="QA01RF051NATIVE ordinal=2 kind=apply frame=6124 clock=104485258 target=104485255 pc=0202 port=3 val=D0 queue=0"
N3="QA01RF051NATIVE ordinal=3 kind=spc-read frame=6124 clock=104485263 target=104485263 pc=0204 port=3 val=D0 queue=0"

def orig(*extra):return "\n".join((L,A,S1,B,S2,*extra))
def nat(*extra):return "\n".join(extra)

class SourceNativeReceiverTests(unittest.TestCase):
    def test_positive_both_real_source_receipts_and_native_scope_not_same_clocks(self):
        out=rf.analyze(orig(F7,F6),nat(N1,N2,N3))
        self.assertEqual(out["original_real_late_SPC_F6_F7_reads"],2)
        self.assertEqual(out["original_late_incoming_SPC_after_sender_count"],2)
        self.assertEqual(out["original_matching_value_read_after_sender_count"],2)
        self.assertEqual(out["native_queue_apply_receiver_census"]["spc-read"]["count"],1)
        self.assertFalse(out["source_SPC_age_equals_native_portClock_proven"])
        self.assertFalse(out["end_to_end_original_native_SPC_delivery_parity_proven"])

    def test_observer_absence_is_not_proof_of_no_real_source_spc_reads(self):
        out=rf.analyze(orig(),nat())
        self.assertEqual(out["original_real_late_SPC_F6_F7_reads"],0)
        self.assertTrue(out["original_receipt_absence_is_only_source_window_missingness"])
        self.assertFalse(out["source_original_frame_equals_native_host_frame_proven"])

    def test_missing_sender_truncation_reorder_and_wrong_clock_rejected(self):
        source=orig(F7,F6)
        native=nat(N1,N2,N3)
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.analyze(source+"\nQA01RF051ORIGSPC_TRUNCATED",native)
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.analyze(source,native+"\nQA01RF051NATIVE_TRUNCATED")
        with self.assertRaisesRegex(ValueError,"ordinal gap"):
            rf.analyze(source.replace("ordinal=2 age=104485263","ordinal=3 age=104485263"),native)
        with self.assertRaisesRegex(ValueError,"source original"):
            rf.analyze(source.replace("port=2 val=63","port=2 val=64",1),native)
        with self.assertRaisesRegex(ValueError,"original SPC receiver age outside"):
            rf.analyze(source.replace("age=104485261","age=104485999"),native)
        with self.assertRaisesRegex(ValueError,"native frame outside"):
            rf.analyze(source,native.replace("frame=6124","frame=6200",1))
if __name__=="__main__":unittest.main()

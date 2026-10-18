"""RF053: genuine original/native SPC700 sequence requires unique full-run PC/port/value parity."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf053_real_spc_receiver_sequence_parity as rf

O1="QA01RF051ORIGSPC seq=1 age=104485261 v=159 h=1184 spcpc=1521 port=2 val=63 debt=-1"
O2="QA01RF051ORIGSPC seq=2 age=104485266 v=159 h=1288 spcpc=1525 port=3 val=D0 debt=-1"
N1="QA01RF052NATIVE seq=1 kind=spc-read global_kind_ord=100 frame=6124 clock=104485238 target=104485238 pc=1521 port=2 val=63 q=0"
N2="QA01RF052NATIVE seq=2 kind=schedule global_kind_ord=55 frame=6124 clock=104485239 target=104485247 pc=1525 port=3 val=44 q=1"
N3="QA01RF052NATIVE seq=3 kind=apply global_kind_ord=55 frame=6124 clock=104485241 target=104485241 pc=1525 port=3 val=43 q=0"
N4="QA01RF052NATIVE seq=4 kind=spc-read global_kind_ord=101 frame=6124 clock=104485243 target=104485243 pc=1525 port=3 val=D0 q=0"
END="QA01RF052NATIVE_FINAL clock=104495002 printed=4 overflow=0 schedules=55 applies=55 reads=101"

def fixture(original=None,native=None):
    return (original if original is not None else "\n".join((O1,O2)),
            native if native is not None else "\n".join((N1,N2,N3,N4,END)))

class SourceNativeReceiverTests(unittest.TestCase):
    def test_actual_PC_port_value_uninterrupted_unique_and_clock_domains_separate(self):
        a,b=fixture()
        out=rf.exact_alignment(a,b,expected_count=2)
        self.assertEqual(out["original_real_spc_read_count"],2)
        self.assertEqual(out["native_window_real_spc_read_count"],2)
        self.assertEqual(out["unique_full_source_read_sequence_matches_in_native_window"],1)
        self.assertEqual(out["source_minus_native_same_recipient_local_clock_difference_counts"],{"23":2})
        self.assertEqual(out["native_matched_global_read_ordinals_first_last"],[100,101])
        self.assertTrue(out["same_receiver_read_sequence_but_unregistered_CPU_publication_clocks"])
        self.assertEqual(out["complete_USA_events_accepted"],0)

    def test_full_pc_required_not_just_matching_bytes(self):
        a,b=fixture(native="\n".join((N1,N2,N3,N4.replace("pc=1525","pc=1527"),END)))
        with self.assertRaisesRegex(ValueError,"not uniquely matched"):
            rf.exact_alignment(a,b)

    def test_original_or_native_gap_fails_closed(self):
        a,b=fixture()
        cases={
            "original sequence":(a.replace("seq=2","seq=9"),b,"ordinal/port"),
            "original missing":(O1,b,"count missing/changed"),
            "native lost event":(a,b.replace(N4,""),"trace counts"),
            "native out of order":(a,b.replace("seq=4 kind=spc-read","seq=5 kind=spc-read"),"row order broken"),
            "source truncated":(a+"\nQA01RF051ORIGSPC_TRUNCATED",b,"truncated"),
            "native truncated":(a,b+"\nQA01RF052NATIVE_TRUNCATED","truncated"),
            "missing completion":(a,b.replace(END,""),"terminal census"),
            "duplicate completion":(a,b+"\n"+END,"terminal census"),
            "missing receiver":(a,b.replace(N4,N4.replace("val=D0","val=CD")),"not uniquely matched"),
            "native ordinal gap":(a,b.replace("global_kind_ord=101","global_kind_ord=102"),"not consecutive"),
        }
        for name,(source,native,pattern) in cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError,pattern):
                    rf.exact_alignment(source,native,expected_count=2)

    def test_duplicated_identical_native_receiver_segment_is_ambiguous(self):
        a,b=fixture()
        parts=b.splitlines()
        extra1=N1.replace("seq=1","seq=5").replace("global_kind_ord=100","global_kind_ord=102").replace("clock=104485238","clock=104485250").replace("target=104485238","target=104485250")
        extra2=N4.replace("seq=4","seq=6").replace("global_kind_ord=101","global_kind_ord=103").replace("clock=104485243","clock=104485255").replace("target=104485243","target=104485255")
        n="\n".join(parts[:-1]+[extra1,extra2,END.replace("printed=4","printed=6").replace("reads=101","reads=103")])
        with self.assertRaisesRegex(ValueError,"not uniquely matched"):
            rf.exact_alignment(a,n,expected_count=2)

if __name__=="__main__":
    unittest.main()

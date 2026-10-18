"""RF051 exact source late receiver receipt fail-closed tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf051_late_source_spc_report as rf

W1="QA01RF050ORIGAPU seq=21 age=104485254 v=159 h=1016 port=3 val=D0"
W2="QA01RF050ORIGAPU seq=22 age=104485258 v=159 h=1066 port=2 val=63"
R1="QA01RF051ORIGSPC seq=1 age=104485260 v=159 h=1088 spcpc=02F1 port=2 val=63 debt=-3"
R2="QA01RF051ORIGSPC seq=2 age=104485263 v=159 h=1100 spcpc=02F4 port=3 val=D0 debt=-2"
class SourceSPCReportTests(unittest.TestCase):
    def test_receiver_after_real_source_publications_not_native_clock(self):
        data=rf.examine("\n".join((W1,W2,R1,R2)))
        self.assertEqual(data["real_original_SPC_F6_F7_read_count"],2)
        self.assertEqual(data["true_source_SPC_observations"][0]["relative_to_original_port2_publication"],2)
        self.assertFalse(data["native_corresponding_late_transaction_proven"])
    def test_no_receiver_is_missingness_not_a_negative(self):
        data=rf.examine("\n".join((W1,W2)))
        self.assertTrue(data["source_receiver_capture_missing"])
    def test_truncated_bad_age_and_wrong_source_identity(self):
        lines="\n".join((W1,W2,R1))
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf.examine(lines+"\nQA01RF051ORIGSPC_TRUNCATED")
        with self.assertRaisesRegex(ValueError,"clock outside"):
            rf.examine(lines.replace("104485260","104490000"))
        with self.assertRaisesRegex(ValueError,"sequence/port"):
            rf.examine(lines.replace("seq=1 age=104485260","seq=2 age=104485260"))
        with self.assertRaisesRegex(ValueError,"publication clock changed"):
            rf.examine(lines.replace("104485254","104485253"))
        with self.assertRaisesRegex(ValueError,"unique D0/63 pair"):
            rf.examine(lines.replace("port=3 val=D0","port=3 val=DD"))
if __name__=="__main__":unittest.main()

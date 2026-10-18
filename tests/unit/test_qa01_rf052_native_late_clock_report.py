"""RF052 native APU schedule/apply/receiver log: bounded fail-closed parser."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf052_native_late_clock_report as rf

A="QA01RF052NATIVE seq=1 kind=schedule global_kind_ord=62337 frame=6125 clock=104485200 target=104485208 pc=1521 port=3 val=D0 q=1"
B="QA01RF052NATIVE seq=2 kind=apply global_kind_ord=61001 frame=6125 clock=104485208 target=104485208 pc=1521 port=3 val=D0 q=0"
C="QA01RF052NATIVE seq=3 kind=schedule global_kind_ord=62338 frame=6125 clock=104485212 target=104485220 pc=1521 port=2 val=63 q=1"
D="QA01RF052NATIVE seq=4 kind=spc-read global_kind_ord=150003 frame=6125 clock=104485224 target=104485224 pc=1521 port=2 val=63 q=0"
F="QA01RF052NATIVE_FINAL clock=104495001 printed=4 overflow=0 schedules=63000 applies=62500 reads=151000"

class NativeRF052Report(unittest.TestCase):
    def test_true_candidate_is_separate_native_clock_not_original_identity(self):
        result=rf.analyze_native("\n".join((A,B,C,D,F)))
        self.assertEqual(result["native_window_events"],4)
        self.assertEqual(result["native_D0_63_candidate_count"],1)
        candidate=result["native_D0_63_scheduled_candidate_pairs"][0]
        self.assertEqual(candidate["native_schedule_global_kind_ordinals"],[62337,62338])
        self.assertEqual(candidate["native_local_clock_separation"],12)
        self.assertFalse(candidate["source_original_late_transaction_identity_proven"])
        self.assertFalse(result["clock_epoch_correspondence_proven"])
    def test_require_complete_native_age_window(self):
        s="\n".join((A,B,C,D,F))
        cases={
           "one genuine after-window":s.replace(F,""),
           "truncated":s+"\nQA01RF052NATIVE_TRUNCATED",
           "missing native clock-window event rows":s.replace("printed=4","printed=5"),
           "missing or duplicate native event order":s.replace("seq=3","seq=6"),
           "unknown real native":s.replace("kind=apply","kind=spoof"),
           "per-kind event ordinal regressed":s.replace("global_kind_ord=62338","global_kind_ord=62336"),
           "native local clock sequence regressed":s.replace("clock=104485212","clock=104485207"),
           "final global kind counts shorter":s.replace("schedules=63000","schedules=2"),
        }
        for pattern,text in cases.items():
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ValueError,pattern):rf.analyze_native(text)
    def test_missing_pair_does_not_invent_native_transfer(self):
        result=rf.analyze_native("\n".join((A.replace("val=D0","val=21"),B,C,D,F)))
        self.assertEqual(result["native_D0_63_candidate_count"],0)
if __name__=="__main__":unittest.main()

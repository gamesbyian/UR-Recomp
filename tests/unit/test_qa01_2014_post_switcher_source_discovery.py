"""ROM-free fake trace and honest source-only next-event classification."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_2014_post_switcher_source_discovery as target


class SourceOnlyTests(unittest.TestCase):
    def make_states(self):
        s=[{"menu":0,"track":0,"in_race":0,"tour_row":0}
           for _ in range(target.HORIZON+1)]
        for frame,track,race in target.BASELINE:
            for f in range(frame,frame+10):
                s[f]={"menu":0,"track":track,"in_race":race,"tour_row":0}
        for frame,track,menu in target.RESULTS:
            for f in range(frame,frame+10):
                s[f]={"menu":menu,"track":track,"in_race":0,"tour_row":0}
        return s

    def test_source_only_no_fabricated_next_event_from_menu_selection(self):
        s=self.make_states()
        for f in range(23000,23500):
            s[f]={"menu":0xf6,"track":4,"in_race":0,"tour_row":0}
        x=target.assess(s)
        self.assertEqual(x["new_event_status"],
                         "no_complete_post_switcher_source_attempt_through_horizon")
        self.assertEqual(x["completed_new_unique_source_course_candidates"],0)
        self.assertEqual(x["genuine_original_source_sustained_active_runs_after_switcher"],[])
        self.assertFalse(x["fresh_original_or_native_event_proven"])
        self.assertEqual(x["USA_accepted_event_credit"],0)

    def test_actually_sustained_source_event_and_terminal_required(self):
        s=self.make_states()
        for f in range(23500,23900):
            s[f]={"menu":0,"track":4,"in_race":1,"tour_row":0}
        x=target.assess(s)
        self.assertEqual(x["completed_new_unique_source_course_candidates"],0)
        self.assertEqual(x["genuine_original_source_sustained_active_runs_after_switcher"][0]["start"],23500)
        for f in range(23910,23920):
            s[f]={"menu":0xbc,"track":4,"in_race":0,"tour_row":0}
        x=target.assess(s)
        self.assertEqual(x["completed_new_unique_source_course_candidates"],1)
        self.assertEqual(x["genuine_original_source_sustained_active_runs_after_switcher"][0]
                         ["separately_observed_terminal_result"],
                         {"host_frame":23910,"result_menu":0xbc})
        self.assertEqual(x["USA_accepted_event_credit"],0)

    def test_completed_repeated_dragster_is_not_a_fifth_distinct_usa_course(self):
        s=self.make_states()
        for f in range(22941,25343):
            s[f]={"menu":0,"track":0,"in_race":1,"tour_row":0}
        for f in range(25344,25354):
            s[f]={"menu":0x99,"track":0,"in_race":0,"tour_row":0}
        for f in range(25731,36001):
            s[f]={"menu":0,"track":0,"in_race":1,"tour_row":0}
        x=target.assess(s)
        self.assertEqual(x["completed_post_switcher_source_attempts"],1)
        self.assertEqual(x["completed_repeat_of_previously_sourced_course"],1)
        self.assertEqual(x["completed_new_unique_source_course_candidates"],0)
        self.assertEqual(x["new_event_status"],"post_switcher_repeats_previously_sourced_course")
        self.assertEqual(len(x["genuine_original_source_sustained_active_runs_after_switcher"]),2)
        self.assertEqual(x["USA_accepted_event_credit"],0)

    def test_single_frame_track_scratch_and_nonrace_flag_60_do_not_count(self):
        s=self.make_states()
        s[23000]={"menu":0x16,"track":4,"in_race":1,"tour_row":0}
        for f in range(24000,24100):
            s[f]={"menu":0x3c,"track":4,"in_race":60,"tour_row":0}
        x=target.assess(s)
        self.assertFalse(x["genuine_original_source_sustained_active_runs_after_switcher"])

    def test_baseline_lost_source_proof_fails_closed(self):
        s=self.make_states()
        s[12327]["in_race"]=0
        with self.assertRaisesRegex(target.SourceDiscoveryError,"lost authenticated"):
            target.assess(s)
        s=self.make_states()
        s[17030]["menu"]=0
        with self.assertRaisesRegex(target.SourceDiscoveryError,"lost independently"):
            target.assess(s)

    def test_streamed_original_wram_write_timeline_and_host_ack(self):
        def line(f,addr,value):
            return (json.dumps({"f":f,"adr":f"0x{addr:05x}",
                                "old":"0x00","val":f"0x{value:02x}"},
                               separators=(",",":"))+"\n").encode()
        trace=[line(1,0x009f,0x99),
               line(2,0x0313,1),
               line(23000,0x00ce,4),
               line(23001,0x0313,60),
               line(36000,0x009f,0x3c)]
        states=target.frame_states(trace,target.HORIZON)
        self.assertEqual((states[1]["menu"],states[1]["in_race"]),(0x99,0))
        self.assertEqual(states[2]["in_race"],1)
        self.assertEqual(states[23000]["track"],4)
        self.assertEqual(states[23001]["in_race"],60)
        self.assertEqual(states[36000]["menu"],0x3c)
        self.assertEqual(target.actual_host_frame(
            "script f=36000 dump new-horizon ok\n","new-horizon"),36000)
        with self.assertRaisesRegex(target.SourceDiscoveryError,"unique"):
            target.actual_host_frame("script f=36000 dump new-horizon ok\n"*2,
                                     "new-horizon")
        with self.assertRaisesRegex(target.SourceDiscoveryError,"nonmonotonic"):
            target.frame_states(trace+[line(35999,0x00ce,3)],target.HORIZON)


if __name__=="__main__":
    unittest.main()

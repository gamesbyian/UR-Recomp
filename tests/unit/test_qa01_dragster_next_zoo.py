"""Synthetic-only source, clock, input and raw evidence guards for Dragster→Zoo."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_dragster_zoo_handoff as target
import probe_original_event_complete as producer


class DragsterToZooTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name)
        self.ref,self.native=base/"ref",base/"native"
        self.ref.mkdir();self.native.mkdir()
        self.source_event={"original_entry_frame":794,"original_result_frame":2874,
                           "source_active_frames_to_result":2080}
        self.states={}
        for f in range(2874,2874+350):
            self.states[f]={"menu":0 if f>=3190 else 0x99,
                            "track":1 if f>=2935 else 0,
                            "in_race":1 if f>=3190 else 0,
                            "tour_row":0}
        self.proof=target.source_next_zoo(self.states,self.source_event)
        self.logs={}
        for side,path,entry,result,active_at in (
                ("original",self.ref,945,2081,315),
                ("native",self.native,945,2079,317)):
            lines=[]
            for offset in target.OFFSETS:
                tag=f"dragster-next-zoo-{offset:03d}"
                active=offset>=active_at
                w=bytearray(0x20000)
                w[0x009f]=0 if active else 0x99
                w[0x00ce]=1 if active or offset>=61 else 0
                w[0x0313]=1 if active else 0
                w[0x00d0]=0
                (path/f"{tag}.wram.bin").write_bytes(w)
                (path/f"{tag}.sram.bin").write_bytes(bytes(8192))
                lines.append(f"script f={entry+result+offset} dump {tag} ok")
            self.logs[side]="\n".join(lines)+"\n"

    def observe(self, **kw):
        opts=dict(observed_dump_frame=producer.observed_dump_frame,
                  audit_wram=producer.audit_qa01_wram_pair,
                  validate_course_payload=lambda src,ram: True,
                  zoo_course_payload=b"zoo",
                  decode_sram=producer.decode_qa01_crawler_battery_sram)
        opts.update(kw)
        return target.observe_guest_handoff(
            self.ref,self.native,self.logs["original"],self.logs["native"],
            self.proof,945,945,2081,2079,**opts)

    def test_real_original_source_requires_8_active_frames_not_track_select(self):
        self.assertEqual(self.proof["original_zoo_active_entry_host_frame"],3190)
        self.assertEqual(self.proof["source_dragster_result_to_zoo_active_frames"],316)
        self.assertEqual(self.proof["sample_offsets"],list(target.OFFSETS))
        self.assertFalse(target.is_zoo(self.states[2935]))
        self.assertTrue(target.is_zoo(self.states[3190]))
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"unqualified"):
            target.source_next_zoo(self.states,
                dict(self.source_event,original_result_frame=2875))
        m=dict(self.states)
        m[3192]=dict(m[3192],in_race=0)
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"8 actual"):
            target.source_next_zoo(m,self.source_event)
        m=dict(self.states)
        m[3190]=dict(m[3190],tour_row=1)
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"8 actual"):
            target.source_next_zoo(m,self.source_event)

    def test_three_distinct_clocks_and_sustained_source_result_negative(self):
        x=self.observe()
        self.assertEqual(x["entry_brackets"]["movie"]["exact_adjacent_onset_offset"],316)
        self.assertEqual(x["entry_brackets"]["original"]["exact_adjacent_onset_offset"],315)
        self.assertEqual(x["entry_brackets"]["native"]["exact_adjacent_onset_offset"],317)
        self.assertEqual(x["fresh_original_absolute_zoo_onset_host"],945+2081+315)
        self.assertEqual(x["fresh_native_absolute_zoo_onset_host"],945+2079+317)
        self.assertFalse(x["all_three_guest_result_relative_entry_offsets_equal"])
        self.assertTrue(x["all_full_sram_pairs_equal"])
        self.assertTrue(x["fresh_original_loaded_true_zoo_course_while_active"])
        self.assertTrue(x["fresh_native_loaded_true_zoo_course_while_active"])
        self.assertEqual(x["release_complete_usa_event_credit"],0)

    def test_bad_real_dump_time_short_raw_and_unmasked_byte_fail_or_report(self):
        f=304;path=self.native/f"dragster-next-zoo-{f:03d}.wram.bin"
        w=bytearray(path.read_bytes());w[0x01dd]=42;path.write_bytes(w)
        x=self.observe()
        row=x["samples"][0]["unmasked_full_original_native_wram_difference"]
        self.assertFalse(row["byte_exact"])
        self.assertEqual(row["differing_byte_count"],1)
        self.assertEqual(row["excluded_byte_count"],0)
        path.write_bytes(bytes(131071))
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"truncated"):
            self.observe()
        path.write_bytes(bytes(131072))
        self.logs["native"]=self.logs["native"].replace(
            f"script f={945+2079+304} dump dragster-next-zoo-304",
            f"script f={945+2079+305} dump dragster-next-zoo-304")
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"clock"):
            self.observe()
        self.logs["native"]=self.logs["native"].replace(
            f"script f={945+2079+305} dump dragster-next-zoo-304",
            f"script f={945+2079+304} dump dragster-next-zoo-304")
        wrong=dict(self.proof,release_complete_usa_event_credit=1)
        with self.assertRaisesRegex(target.DragsterZooEvidenceError,"not authenticated"):
            target.observe_guest_handoff(
                self.ref,self.native,self.logs["original"],self.logs["native"],
                wrong,945,945,2081,2079,
                observed_dump_frame=producer.observed_dump_frame,
                audit_wram=producer.audit_qa01_wram_pair,
                validate_course_payload=lambda src,ram:True,
                zoo_course_payload=b"zoo",
                decode_sram=producer.decode_qa01_crawler_battery_sram)

    def test_original_button_masks_and_script_stay_unmodified(self):
        frames=producer.sample_frames("dragster",2080)
        basic=producer.replay_script(1,0x99,frames,False,source_followthrough=True)
        extended=producer.replay_script(
            1,0x99,frames,False,source_followthrough=True,dragster_next_zoo=True)
        self.assertIn("dump original-follow-72\nwait 232\ndump dragster-next-zoo-304",extended)
        self.assertTrue(extended.endswith("dump dragster-next-zoo-336\nquit\n"))
        self.assertEqual([x for x in basic.splitlines() if x.startswith("press ")],
                         [x for x in extended.splitlines() if x.startswith("press ")])
        self.assertNotIn("poke ",extended)
        with self.assertRaisesRegex(producer.CompleteEventError,"requires"):
            producer.replay_script(2,0xBC,frames,False,
                                   source_followthrough=True,dragster_next_zoo=True)

if __name__=="__main__":
    unittest.main()

"""RF060 source CPU entry proof must never be inferred from static symbols."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf060_original_race_entry_cpu_trace_patch as patch
import qa01_rf060_original_race_entry_cpu_report as rf

class OriginalRaceMainEntry(unittest.TestCase):
    def source(self):
        return "void foo(){\n"+patch.PINNED+"\n}"
    def test_unique_opcode_dispatch_and_no_additional_SNESCpuBus_operations(self):
        out=patch.patch(self.source())
        self.assertEqual(patch.patch(out),out)
        self.assertEqual(out.count(patch.PINNED),1)
        self.assertEqual(out.count(patch.BEFORE),1)
        self.assertEqual(out.count(patch.AFTER),1)
        self.assertEqual(out.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertTrue(all(x not in patch.BEFORE+patch.AFTER for x in
            ("S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")))
        with self.assertRaisesRegex(ValueError,"dispatcher changed"):
            patch.patch(self.source().replace("Registers.PCw++;","Registers.PCw += 2;"))
    def heartbeat(self):
        return "\n".join(
            f"QA01RF060HEART frame={frame} pbpc=82:82F9 op=A9 v=0 h=32"
            for frame in rf.FRAMES)
    def row(self,seq,pc,prev,enter=0,frame=4688):
        f={
           "seq":seq,"frame":frame,"pre_v":7,"pre_h":420,
           "pc":pc,"op":"8D","prev":prev,"prevop":"22",
           "prevframe":frame,"prev_v":7,"prev_h":400,
           "enter":enter,"a":"FF01","x":"0001","y":"00A7",
           "s":"01E0","p":"0134","c":1,"z":0,"n":0,"o":0,
           "next":"83:CBE5","post_v":7,"post_h":444,"a1":"FF01",
           "x1":"0001","y1":"00A7","s1":"01E0","c1":1,"z1":0,"n1":0,"o1":0
        }
        return rf.ROW+" ".join(f"{key}={val}" for key,val in f.items())
    def qualified(self):
        rows=[
            self.row(1,"83:C8E0","82:D4EE",enter=1),
            self.row(2,"83:CAC4","83:C8E0"),
            self.row(3,"83:CBE2","83:CAC4"),
            self.row(4,"83:CC1C","83:CBE2"),
            self.row(5,"83:CC47","83:CC1C"),
        ]
        return self.heartbeat()+"\n"+"\n".join(rows)
    def test_actual_source_opcode_and_true_preceding_cross_range_entry(self):
        got=rf.inspect(self.qualified())
        self.assertEqual(got["true_original_Race_Main_range_executed_opcode_rows"],5)
        self.assertEqual(got["all_actual_cross_range_CPU_entry_count"],1)
        self.assertEqual(got["real_cross_range_CPU_entry_rows"][0]["prev"],"82:D4EE")
        self.assertEqual(got["real_source_original_scene_setup_opcode_records"]["83:CC1C"]["a"],"FF01")
        self.assertEqual(got["independent_USA_complete_events_accepted"],0)
    def test_missing_heartbeats_and_invalid_entry_branches_are_rejected(self):
        samples=[
            ("","heartbeat coverage"),
            (self.heartbeat(),"no original"),
            (self.qualified().replace("frame=4694","frame=4695"),"heartbeat coverage"),
            (self.qualified().replace("seq=3","seq=99"),"count/PC"),
            (self.qualified().replace("83:C8E0","83:C700",1),"count/PC"),
            (self.qualified().replace("prev=82:D4EE","prev=83:CA00"),"entry from inside"),
            (self.qualified().replace("prev=83:C8E0","prev=82:8000"),"missed genuine"),
            (self.qualified().replace("83:CC47","83:CC40"),"writer opcode not observed"),
            (self.qualified()+"\nQA01RF060ORIGCPU_TRUNCATED","truncated"),
        ]
        for body,part in samples:
            with self.subTest(part=part):
                with self.assertRaisesRegex(ValueError,part):
                    rf.inspect(body)

if __name__=="__main__":unittest.main()

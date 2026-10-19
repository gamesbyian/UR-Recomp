"""RF058 tests: actual CPU opcode interval, not asserted bus-write or input proof."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf058_source_opcode_wram_transition_patch as patched
import qa01_rf058_original_cpu_wram_mutation_report as rf

class TrueOriginalBowlWRAM(unittest.TestCase):
    def test_only_one_real_original_65816_opcode_dispatch_without_bus_calls(self):
        src="void foo(){\n"+patched.PINNED+"\n}"
        out=patched.patch(src)
        self.assertEqual(out.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(out.count(patched.BEFORE),1)
        self.assertEqual(out.count(patched.AFTER),1)
        self.assertEqual(patched.patch(out),out)
        self.assertTrue(all(
            token not in patched.BEFORE+patched.AFTER for token in
            ("S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")))
        with self.assertRaisesRegex(ValueError,"exact pinned"):
            patched.patch(src.replace("Registers.PCw++;","Registers.PCw += 2;"))
        with self.assertRaisesRegex(ValueError,"partially"):
            patched.patch(out.replace("QA01RF058OPWRAM_TRUNCATED","QA01RF058MARKER_BAD"))
    def heartbeat(self):
        return "\n".join(
            f"QA01RF058CPUHEART frame={f} v=0 h=32 pc=82:8332"
            for f in range(4686,4695))
    def changed(self,seq=1,frame=4689,pc="82:8F95",addr="7E:0057",
                old="E2",new="00"):
        return (
           f"QA01RF058OPWRAM seq={seq} frame={frame} pre_v=51 pre_h=32 "
           f"pc={pc} op=A9 a=0012 x=0040 y=0050 post_v=51 post_h=40 "
           f"nextpc=82:8F97 addr={addr} old={old} new={new}")
    def test_qualified_source_65816_before_after_capture(self):
        r=rf.inspect(self.heartbeat()+"\n"+self.changed())
        self.assertEqual(r["true_original_CPU_dispatch_frame_heartbeats"],9)
        self.assertEqual(r["actual_source_65816_opcode_interval_mutation_count"],1)
        self.assertTrue(r["real_full_frame_original_WRAM_end_state_transitions"]
                         ["7E:0057"]["actual_direct_opcode_delta_with_those_two_values"])
        self.assertFalse(r["unique_CPU_memory_bus_write_by_that_opcode_proven"])
        self.assertEqual(r["accepted_complete_USA_events"],0)
    def test_spoofed_or_missing_capture_never_qualifies(self):
        examples=[
          ("", "dispatch"),
          (self.changed(), "dispatch"),
          (self.heartbeat(), "not captured"),
          (self.heartbeat()+"\n"+self.changed(seq=2),"ordinal gap"),
          (self.heartbeat()+"\n"+self.changed(addr="7E:0099"),"not in exactly"),
          (self.heartbeat()+"\n"+self.changed(old="E2",new="E2"),"malformed"),
          (self.heartbeat()+"\n"+self.changed(frame=4699),"opcode/frame"),
          (self.heartbeat()+"\n"+self.changed().replace("nextpc=","not_next="),"missing context"),
          (self.heartbeat()+"\n"+self.changed()+"\nQA01RF058OPWRAM_TRUNCATED","truncated"),
          (self.heartbeat().replace("frame=4691","frame=4696")+"\n"+self.changed(),"not observed"),
        ]
        for log,msg in examples:
            with self.subTest(description=msg,log=log[:40]):
                with self.assertRaisesRegex(ValueError,msg):
                    rf.inspect(log)
    def test_no_unsourced_full_raw_guest_state(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            p=Path(d)/"spoof.zip"
            p.write_bytes(b"not an authenticated USA Bowl case")
            with self.assertRaisesRegex(ValueError,"reference ZIP changed"):
                rf.case(p,p)

if __name__=="__main__":unittest.main()

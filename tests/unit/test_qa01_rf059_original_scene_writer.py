"""RF059: scene state source opcode dispatch and immutable full-byte negatives."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf059_source_scene_transition_opcode_patch as patch
import qa01_rf059_original_scene_writer_report as rf

class RF059SourceWriter(unittest.TestCase):
    def test_pinned_actual_Snes9x_CPU_dispatch_and_17_exact_addresses(self):
        old="void foo(){\n"+patch.PINNED+"\n}"
        out=patch.patch(old)
        self.assertEqual(patch.patch(out),out)
        self.assertEqual(out.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(out.count("ur_rf059_i<17"),2)
        self.assertEqual(out.count("QA01RF059OPWRAM"),2)
        self.assertEqual(len(patch.SLOTS),17)
        self.assertEqual(set(patch.SLOTS),set(rf.WATCH))
        self.assertTrue(all(x not in patch.BEFORE+patch.AFTER for x in
            ("S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")))
        with self.assertRaisesRegex(ValueError,"exact pinned"):
            patch.patch(old.replace("Registers.PCw++;","Registers.PCw += 2;"))
    def heartbeat(self):
        return "\n".join(
            f"QA01RF059CPUHEART frame={f} v=0 h=28 pc=82:8F95"
            for f in range(4686,4695))
    def change(self,seq=1,pc="82:8F95",frame=4689,addr="7E:121F",
               before="00",after="01"):
        return (f"QA01RF059OPWRAM seq={seq} frame={frame} pre_v=10 pre_h=22 "
            f"pc={pc} op=85 a=0001 x=0001 y=0001 post_v=10 post_h=44 "
            f"nextpc=82:8F97 addr={addr} old={before} new={after}")
    def test_real_original_opcode_before_after_source_census(self):
        out=rf.inspect(self.heartbeat()+"\n"+self.change()+"\n"+
                       self.change(2,addr="7E:2000",before="01",after="02"))
        self.assertEqual(out["actual_source_65816_opcode_interval_mutation_count"],2)
        self.assertEqual(out["actual_memory_change_candidate_address_census"],
                         {"7E:121F":1,"7E:2000":1})
        self.assertEqual(out["actual_CPU_scene_change_first_by_address"]["7E:121F"]["pc"],"82:8F95")
        self.assertFalse(out["unique_CPU_memory_bus_write_by_that_opcode_proven"])
        self.assertEqual(out["accepted_complete_USA_events"],0)
    def test_negative_missing_real_CPU_or_modified_bytes(self):
        examples=[
            ("","dispatch"),
            (self.heartbeat(),"not captured"),
            (self.change(),"dispatch"),
            (self.heartbeat()+"\n"+self.change(seq=2),"ordinal gap"),
            (self.heartbeat()+"\n"+self.change(addr="7E:0099"),"not in exactly"),
            (self.heartbeat()+"\n"+self.change(before="01",after="01"),"malformed"),
            (self.heartbeat()+"\n"+self.change(frame=4695),"opcode/frame"),
            (self.heartbeat()+"\n"+self.change().replace("nextpc=","unknown="),"missing context"),
            (self.heartbeat()+"\n"+self.change()+"\nQA01RF059OPWRAM_TRUNCATED","truncated"),
        ]
        for msg,error in examples:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError,error):
                    rf.inspect(msg)

if __name__=="__main__":unittest.main()

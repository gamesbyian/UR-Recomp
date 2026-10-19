"""RF057: synthetic negative cases cannot masquerade as executed USA instructions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf057_original_bowl_transition_trace_patch as patch
import qa01_rf057_original_bowl_transition_cpu_report as report

class OriginalUSAOpcode(unittest.TestCase):
    def test_disposable_pinned_source_opcode_dispatch_unchanged(self):
        core="void foo(){\n"+patch.DISPATCH+"\n}"
        output=patch.patch(core)
        self.assertEqual(patch.patch(output),output)
        self.assertEqual(output.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(output.count(patch.BEFORE),1)
        self.assertEqual(output.count(patch.AFTER),1)
        self.assertIn('getenv("UR_QA01_RF057_BOWL_CPU_TRACE")',output)
        self.assertIn("ur_rf057_f >= 4686u",output)
        with self.assertRaisesRegex(ValueError,"unknown pinned"):
            patch.patch(core.replace("Registers.PCw++;","Registers.PCw += 2;"))
        with self.assertRaisesRegex(ValueError,"partially"):
            patch.patch(output.replace("QA01RF057ORIGCPU_TRUNCATED","BADMARKER"))
    def line(self,frame=4689,pc="80:C1F5",seq=1):
        fields={
           "frame":frame,"seq":seq,"pc":pc,"next":"80:C1F8",
           "op":"C2","pre_h":180,"pre_v":108,"post_h":186,
           "post_v":108,"a0":"0080","a1":"0080","p0":"0034",
           "p1":"0034","s0":"01FD","s1":"01FD",
           "c0":1,"z0":0,"n0":0,"o0":0,
           "c1":1,"z1":1,"n1":0,"o1":0,
           "joy72":"80","joy73":"A4","joy74":"85","joy75":"80",
           "latch8f":"00","raw30d":"00","raw30f":"00",
        }
        return report.TAG+" ".join(f"{k}={v}" for k,v in fields.items())
    def heartbeats(self):
        return "\n".join(
            f"QA01RF057HEART frame={f} v=225 h=40 pc=80:ADD4 flag=1"
            for f in range(4687,4694))
    def test_no_menu_candidate_requires_verified_full_original_CPU_frame_coverage(self):
        data=report.inspect(self.heartbeats())
        self.assertEqual(data["recorded_original_executed_CPU_instruction_count"],0)
        self.assertTrue(data["no_candidate_PC_executes_despite_confirmed_CPU_window"])
        self.assertTrue(data["source_frame_window_CPU_dispatch_coverage_proven"])
        with self.assertRaisesRegex(ValueError,"no qualified CPU handoff window"):
            report.inspect("QA01RF057HEART frame=128 v=0 h=0 pc=00:0000 flag=1")
        with self.assertRaisesRegex(ValueError,"repeated/reordered"):
            report.inspect(self.heartbeats()+"\n"+self.heartbeats())
        with self.assertRaisesRegex(ValueError,"never evidenced"):
            report.inspect("")
    def test_only_genuinely_recorded_original_PC_and_actual_seq(self):
        r=report.inspect(self.heartbeats()+"\n"+"\n".join(
            (self.line(seq=1),self.line(pc="80:B708",seq=2))))
        self.assertEqual(r["recorded_original_executed_CPU_instruction_count"],2)
        self.assertEqual(r["original_decoded_executed_candidate_group_count"],
                         {"menu-confirm":1,"wait-input":1})
        self.assertEqual(r["first_original_guest_executed_candidate_row"]["z0"],"0")
        self.assertFalse(r["native_generated_PC_executed_witness_proven"])
        self.assertFalse(r["first_transition_writer_predicate_proven"])
        self.assertEqual(r["accepted_complete_USA_events"],0)
    def test_reject_missing_truncated_wrong_pc_clock_and_sequence(self):
        samples=[
            ("", "never evidenced"),
            (self.line()+"\nQA01RF057ORIGCPU_TRUNCATED", "truncated"),
            (self.line(pc="80:82F0"),"PC/frame/sequence"),
            (self.line(pc="82:C1F5"),"PC/frame/sequence"),
            (self.line(frame=6138),"PC/frame/sequence"),
            (self.line(seq=5),"PC/frame/sequence"),
            (self.line().replace("joy72=80","missing=80"),"missing original"),
        ]
        for s,error in samples:
            with self.subTest(s=s[:50]):
                with self.assertRaisesRegex(ValueError,error):
                    report.inspect((self.heartbeats()+"\n"+s) if s else "")

if __name__=="__main__":unittest.main()

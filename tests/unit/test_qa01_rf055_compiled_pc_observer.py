"""RF055 generated opcode identity: exact instruction not broad AOT scope."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_compiled_pc_observer as rf

# Minimal deterministic copy of the emitter's instruction loop, not an emulator.
SOURCE='''bank=0x82
func_name="Snd_UploadBlockList_82EF_M1X0"
skip_emit_idx=set()
emitted=[]
for ii, (di_insn, ir_ops) in enumerate(pairs):
    lines=[]
    if ii in skip_emit_idx:
        continue
            # Axis-2 step C dynamics: charge runtime-only modifiers (D.l != 0,
    for op in ir_ops:
        lines.append("original IR unchanged")
    emitted.append(lines)
'''
class RF055ExecutedInstruction(unittest.TestCase):
    def test_only_three_exact_original_opcode_PCs_are_observed(self):
        before=SOURCE
        after=rf.patch(before)
        self.assertEqual(rf.patch(after),after)
        self.assertEqual(after.count("for op in ir_ops:"),1)
        ctx={"pairs":[(SimpleNamespace(addr=pc),["effect"]) for pc in (
            0x8282EE,0x8282F0,0x8282F2,0x8282F6,0x8282F8,0x8182F0)]}
        exec(compile(after,"<rf055 emitter fixture>","exec"),ctx,ctx)
        recorded=ctx["emitted"]
        self.assertEqual(len(recorded),6)
        for i,pc in ((1,"8282F0"),(2,"8282F2"),(3,"8282F6")):
            self.assertEqual(len(recorded[i]),3)
            self.assertIn("pc="+pc,recorded[i][1])
            self.assertIn('getenv("UR_QA01_RF055_NATIVE_INSN_PC")',recorded[i][1])
            self.assertIn("snes_frame_counter == 6124",recorded[i][1])
            self.assertIn("scope=Snd_UploadBlockList_82EF_M1X0",recorded[i][1])
            self.assertIn(r'\n", snes_frame_counter',recorded[i][1])
        for i in (0,4,5):
            self.assertEqual(recorded[i],["original IR unchanged"])
    def test_rejects_unknown_anchor_and_partial_tampering(self):
        with self.assertRaisesRegex(ValueError,"unknown pinned"):
            rf.patch(SOURCE.replace("Axis-2 step C dynamics","Axis-2 missing"))
        with self.assertRaisesRegex(ValueError,"no native per-instruction IR"):
            rf.patch(SOURCE.replace("for op in ir_ops:","for effect in ir_ops:"))
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf.patch(rf.patch(SOURCE).replace("QA01RF055NATIVEPC","BADREC"))
if __name__=="__main__":unittest.main()

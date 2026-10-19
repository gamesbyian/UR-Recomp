"""RF061: only executing physical bank03 M0X0 block may earn an IPL-return witness."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf061_native_bowl_ipl_call_return_patch as rf

class NativeIPLScope(unittest.TestCase):
    def generated(self):
        return (
          rf.HEADER_MARK+
          "RecompReturn DifferentSound_M0X0(CpuState *cpu) {\n"+
          rf.GEN_PRIOR+"\n}\n\n"+
          rf.GEN_MARK+"\n"+
          "L_CA91_M0X0:\n"+
          rf.GEN_PRIOR+"\n"+
          rf.GEN_RETURN+"\n"+
          "  goto L_CABA_M0X0;\n"+
          "}\n\n"+
          "RecompReturn AnotherSound_M0X0(CpuState *cpu) {\n"+
          rf.GEN_PRIOR+"\n}\n"
        )
    def test_one_mode_qualified_return_without_changing_real_sound_call(self):
        before=self.generated()
        out=rf.patch_generated(before)
        self.assertEqual(rf.patch_generated(out),out)
        self.assertEqual(out.count("QA01RF061NATIVE phase=before"),1)
        self.assertEqual(out.count("QA01RF061NATIVE phase=returned"),1)
        self.assertEqual(out.count("QA01RF061NATIVE phase=cab3"),1)
        self.assertEqual(out.count("Snd_UploadBlockListLong_M0X0(cpu)"),
                         before.count("Snd_UploadBlockListLong_M0X0(cpu)"))
        self.assertEqual(out.count(rf.EXTERN),1)
        self.assertIn("L_CAB3_M0X0:",out)
        self.assertIn("physical=03:CAB3 original=83:CAB3",out)
        self.assertIn("ur_rf061_native_host_frame",out)
    def test_wrong_source_variant_partial_patch_and_alias_are_rejected(self):
        for label,source in (
          ("wrong mode",self.generated().replace("L_CAB3_M0X0:","L_CAB3_M1X0:")),
          ("wrong function",self.generated().replace("Race_Main_CA91_M0X0","Race_Main_CA91_M1X0")),
          ("changed direct M0X0 call",self.generated().replace(
              rf.GEN_PRIOR,"case 0: _r = interp_tier_run_call_frame(cpu,0,0,0,0); break;")),
          ("missing label",self.generated().replace("0x03CAB3","0x03CAC1")),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError,"pinned|not inside"):
                    rf.patch_generated(source)
        broken=rf.patch_generated(self.generated()).replace("QA01RF061NATIVE phase=cab3","BROKEN_PHASE")
        with self.assertRaisesRegex(ValueError,"partially installed"):
            rf.patch_generated(broken)
    def test_only_original_native_input_host_tick_is_stamped(self):
        raw="uint32 helper(void) { return 0; }\n"+rf.HOST_MARK+"  return 0;\n}\n"
        out=rf.patch_host(raw)
        self.assertEqual(rf.patch_host(out),out)
        self.assertEqual(out.count("ur_rf061_native_host_frame = (uint32)snes_frame_counter"),1)
        self.assertEqual(out.count("static uint32 TickScript(void) {"),1)
        with self.assertRaisesRegex(ValueError,"insertion point missing"):
            rf.patch_host(raw.replace("static uint32 TickScript","uint32 TickScript"))

if __name__=="__main__":unittest.main()

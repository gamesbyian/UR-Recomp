"""RF034 strict original SMP debt and native opcode-residual source pin tests."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_rf034_spc_opcode_boundary_observer as m  # noqa: E402

class SourcePin(unittest.TestCase):
    def test_original_source_reuse_and_read_only_semantics(self):
        before=m.rf033.ORIGINAL_NEW
        after=m.patch_original(before)
        self.assertEqual(m.patch_original(after),after)
        self.assertIn("SNES::smp.clock",after)
        self.assertIn("SNES::smp.regs.pc",after)
        self.assertIn("SNES::smp.opcode_number",after)
        self.assertIn("S9xAPUExecute();",after)
        self.assertEqual(after.count("SNES::cpu.port_write(port & 3, byte);"),1)
        with self.assertRaisesRegex(ValueError,"prior source"):
            m.patch_original(m.rf033.ORIGINAL_OLD)
        with self.assertRaisesRegex(ValueError,"partial"):
            m.patch_original(after.replace("SNES::smp.opcode_number","BROKEN"))

    def test_native_source_reuse_and_port_visibility_unchanged(self):
        before=m.rf032.APU_HELPER_NEW+"\n"+m.rf032.APU_APPLY_NEW
        after=m.patch_native(before)
        self.assertEqual(m.patch_native(after),after)
        self.assertIn("apu->cpuCyclesLeft",after)
        self.assertIn("w->target_cycle",after)
        self.assertEqual(after.count(m.rf032.APU_APPLY_OLD),1)
        self.assertIn("apu_writePortNow(apu, w->port, w->val);",after)
        with self.assertRaisesRegex(ValueError,"prior source"):
            m.patch_native(m.rf032.APU_APPLY_OLD)
        with self.assertRaisesRegex(ValueError,"partial"):
            m.patch_native(after.replace("apu->cpuCyclesLeft","OTHER"))

    def test_bounded_opt_in_and_shipping_exclusion(self):
        for source in (m.ORIGINAL_AFTER,m.NATIVE_AFTER):
            self.assertIn('getenv("UR_QA01_RF034_SPC_OPCODE_BOUNDARY")',source)
            self.assertIn("103322420ull",source)
            self.assertIn("103323100ull",source)
        shipping=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf034_spc_opcode_boundary_observer.py",shipping)
        self.assertNotIn("UR_QA01_RF034_SPC_OPCODE_BOUNDARY",shipping)

if __name__=="__main__":
    unittest.main()

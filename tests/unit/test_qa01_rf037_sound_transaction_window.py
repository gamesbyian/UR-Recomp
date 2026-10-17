"""RF037 source-pin, idempotence and no-write-transformation tests."""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa01_rf037_sound_transaction_window as m
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf034_spc_opcode_boundary_observer as rf034
import qa01_ipl_echo_trace_patch as rf030

class RF037(unittest.TestCase):
    def test_original_opcode_dispatch_unchanged(self):
        before = rf035.patch_original(rf035.ORIG_DISPATCH)
        after = m.original_cpu(before)
        self.assertEqual(m.original_cpu(after), after)
        self.assertEqual(after.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertIn("QA01RF037ORIGOP", after)
        with self.assertRaisesRegex(ValueError,"requires RF035"):
            m.original_cpu(rf035.ORIG_DISPATCH)

    def test_original_bus_and_spc_reads(self):
        apu = m.original_apu(rf034.ORIGINAL_AFTER)
        self.assertEqual(m.original_apu(apu), apu)
        self.assertEqual(apu.count("SNES::cpu.port_write(port & 3, byte);"), 1)
        self.assertLess(apu.index("SNES::cpu.port_write(port & 3, byte);"),
                        apu.index("QA01RF037ORIGCPU"))
        spc = m.original_spc(rf030.CORE_REPLACEMENT + rf030.READ_NEW)
        self.assertEqual(m.original_spc(spc), spc)
        self.assertIn("QA01RF037ORIGSPC", spc)
        self.assertEqual(spc.count(m.ORIGINAL_SPC_READ), 1)
        with self.assertRaisesRegex(ValueError,"requires RF034"):
            m.original_apu(m.ORIGINAL_APU_WRITE)

    def test_native_pointer_retains_latch_returns(self):
        before = rf035.patch_native(rf035.NATIVE_HEADER+
                                   rf035.NATIVE_BYTE+rf035.NATIVE_WORD)
        after = m.native_cpu(before)
        self.assertEqual(m.native_cpu(after), after)
        self.assertEqual(after.count("return cpu_latch_read8(cpu, value);"),1)
        self.assertEqual(after.count("return cpu_latch_read16"),1)
        self.assertIn("QA01RF037NATIVEPTR_TRUNCATED",after)
        with self.assertRaisesRegex(ValueError,"requires RF035"):
            m.native_cpu(rf035.NATIVE_HEADER+rf035.NATIVE_BYTE+rf035.NATIVE_WORD)

    def test_native_queue_and_spc_read_unmodified(self):
        before = (rf034.NATIVE_AFTER+rf030.NATIVE_SCHEDULE_NEW+
                  rf030.NATIVE_READ_NEW+m.NATIVE_APU_HEADER)
        after = m.native_apu(before)
        self.assertEqual(m.native_apu(after), after)
        self.assertEqual(after.count(m.NATIVE_APU_APPLY),1)
        self.assertEqual(after.count("apu->portLastTarget = target;"),1)
        self.assertEqual(after.count(m.NATIVE_APU_READ),1)
        self.assertIn("QA01RF037NATIVEBUS_TRUNCATED",after)
        with self.assertRaisesRegex(ValueError,"requires RF034"):
            m.native_apu(m.NATIVE_APU_HEADER)

    def test_no_product_stage(self):
        text = (ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("UR_QA01_RF037_SOUND_BUS",text)
        self.assertNotIn("qa01_rf037_sound_transaction_window.py",text)

if __name__=="__main__": unittest.main()

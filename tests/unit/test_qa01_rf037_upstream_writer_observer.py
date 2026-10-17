"""RF037 actual CPU writer coverage over the same exact emulator source sites."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_rf037_sound_transaction_window as base
import qa01_rf037_upstream_writer_observer as m
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf034_spc_opcode_boundary_observer as rf034

class UpstreamWriterSourcePin(unittest.TestCase):
    def test_original_stored_bus_write_retained_and_idempotent(self):
        staged=base.original_apu(rf034.ORIGINAL_AFTER)
        out=m.original(staged)
        self.assertEqual(m.original(out),out)
        self.assertEqual(out.count("SNES::cpu.port_write(port & 3, byte);"),1)
        self.assertIn("ur_age",out)
        self.assertIn("QA01RF037ORIGCPU2",out)
        self.assertIn("104200000ull",out)
        with self.assertRaisesRegex(ValueError,"requires RF037"):
            m.original(rf034.ORIGINAL_AFTER)
        with self.assertRaisesRegex(ValueError,"requires RF037"):
            m.original(staged.replace(base.ORIGINAL_APU_EXTRA,"broken"))
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            m.original(out.replace("ur_age", "BROKEN", 1))

    def test_native_common_rtl_exact_filter_executes_once(self):
        before=(m.RTL_HEADER+m.RTL_PORT_BRANCH+
                m.RTL_APU_HEADER+
                m.RTL_ACCEPTED)
        out=m.native_rtl(before)
        self.assertEqual(m.native_rtl(out),out)
        self.assertEqual(out.count(m.RTL_ACCEPTED),1)
        self.assertEqual(out.count('ur_rf037_upstream("rtl-apu-enter", adr, val);'),1)
        self.assertEqual(out.count('ur_rf037_upstream("rtl-apu-after-filter", adr, val);'),1)
        self.assertEqual(out.count('ur_rf037_upstream("write-reg", reg, value);'),1)
        self.assertIn("getenv",m.RTL_HELPER)
        with self.assertRaisesRegex(ValueError,"unknown native common RTL"):
            m.native_rtl(m.RTL_HEADER)

    def test_native_cpu_all_existing_byte_word_bus_writes_preserved(self):
        before=base.native_cpu(rf035.patch_native(
            rf035.NATIVE_HEADER+rf035.NATIVE_BYTE+rf035.NATIVE_WORD))
        before=m.CPU_BYTE_HEADER+before+m.CPU_WORD_HEADER
        out=m.native_cpu(before)
        self.assertEqual(m.native_cpu(out),out)
        self.assertEqual(out.count(m.CPU_BYTE_HEADER),1)
        self.assertEqual(out.count(m.CPU_WORD_HEADER),1)
        self.assertIn('QA01RF037NATIVECPU kind=byte',out)
        self.assertIn('QA01RF037NATIVECPU kind=word',out)
        self.assertEqual(out.count("return cpu_latch_read8(cpu, value);"),1)
        with self.assertRaisesRegex(ValueError,"requires RF037"):
            m.native_cpu(m.CPU_BYTE_HEADER+m.CPU_WORD_HEADER)

    def test_no_product_windows_integration(self):
        p=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf037_upstream_writer_observer",p)
        self.assertNotIn("UR_QA01_RF037_SOUND_BUS",p)

if __name__=="__main__":unittest.main()

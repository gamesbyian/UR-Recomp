"""RF033 exact source pin, idempotence, no Windows timing changes."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_rf033_original_native_master_clock as m  # noqa: E402

class SourcePin(unittest.TestCase):
    def test_original_and_native_idempotence(self):
        original=m.ORIGINAL_OLD
        edited=m.patch_original(original)
        self.assertIn("UR_QA01_RF033_MASTER_APU_CLOCK", edited)
        self.assertEqual(m.patch_original(edited),edited)
        self.assertIn("S9xAPUExecute();",edited)
        self.assertIn("SNES::cpu.port_write(port & 3, byte);",edited)
        self.assertIn("S9xAPUGetClock",edited)

        native="static uint64_t rtl_apu_guest_cycle(void) {\nreturn 0;\n}\n"+m.NATIVE_OLD
        patched=m.patch_native(native)
        self.assertIn("g_cpu.master_cycles",patched)
        self.assertEqual(m.patch_native(patched),patched)
        self.assertIn("while (!apu_schedulePortWrite(g_snes->apu, port, val, guest_cycle))",patched)

    def test_missing_partial_or_wrong_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"RF030"):
            m.patch_original("void S9xAPUWritePort(int port, uint8 byte) {\n}")
        with self.assertRaisesRegex(ValueError,"unrecognized"):
            m.patch_original(m.ORIGINAL_OLD.replace("SNES::cpu.port_write","OTHER"))
        native="static uint64_t rtl_apu_guest_cycle(void) {\nreturn 0;\n}\n"+m.NATIVE_OLD
        with self.assertRaisesRegex(ValueError,"partial"):
            m.patch_native(m.patch_native(native).replace("while (!apu_schedulePortWrite","while (!anotherFunction"))
        with self.assertRaisesRegex(ValueError,"unrecognized"):
            m.patch_native(native.replace("apu_cycle(g_snes->apu)","NOT_A_CYCLE(g_snes->apu)"))

    def test_opt_in_and_shipping_exclusion(self):
        for src in (m.ORIGINAL_NEW,m.NATIVE_NEW):
            self.assertIn('getenv("UR_QA01_RF033_MASTER_APU_CLOCK")',src)
            self.assertIn("103322420ull",src)
            self.assertIn("103323100ull",src)
        product=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf033_original_native_master_clock.py",product)
        self.assertNotIn("UR_QA01_RF033_MASTER_APU_CLOCK",product)

if __name__=="__main__":
    unittest.main()

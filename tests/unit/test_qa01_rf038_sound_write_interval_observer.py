"""RF038 source-only actual original opcode / native paced clock probes."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa01_rf038_sound_write_interval_observer as m
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf037_sound_transaction_window as rf037


class SoundWriteIntervalProbe(unittest.TestCase):
    def test_original_stages_after_rf037_and_never_redispatches(self):
        staged = rf037.original_cpu(rf035.patch_original(rf035.ORIG_DISPATCH))
        out = m.patch_original(staged)
        self.assertEqual(m.patch_original(out), out)
        self.assertEqual(out.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertIn("QA01RF038ORIGOP frame=", out)
        self.assertIn("ICPU.Frame == 6073u", out)
        self.assertIn("CPU.V_Counter == 116u", out)
        self.assertIn("pre_h", out)
        self.assertIn("QA01RF038ORIGOP_TRUNCATED", out)
        with self.assertRaisesRegex(ValueError, "requires RF037"):
            m.patch_original(rf035.ORIG_DISPATCH)

    def test_native_four_paced_sites_preserved_single_charge(self):
        # Pinned source contract permits only the named four existing
        # charges; never touch the low-level CPU bus or AOT block charges.
        sample = "/* UR_QA01_RF037_UPSTREAM_WRITER */\n"
        for header, _ in m.HEADERS:
            sample += (header + "\n"
                       "    uint32_t _sp = cpu_region_speed(addr);\n"
                       + m.CHARGE + "    return; \n}\n")
        out = m.patch_native(sample)
        self.assertEqual(m.patch_native(out), out)
        self.assertEqual(out.count("cpu->master_cycles += _sp;"), 4)
        self.assertEqual(out.count("ur_rf038_paced(cpu, "), 4)
        self.assertIn("frame=6091", out)
        self.assertIn("2176886750ull", out)
        self.assertIn("2176887550ull", out)
        with self.assertRaisesRegex(ValueError, "requires RF037"):
            m.patch_native(sample.replace("UR_QA01_RF037_UPSTREAM_WRITER", "missing"))
        with self.assertRaisesRegex(ValueError, "unknown exact pinned"):
            m.patch_native(sample.replace(m.HEADERS[1][0], "missing"))

    def test_truncation_and_both_host_axes_observed(self):
        self.assertIn("QA01RF038ORIGOP_TRUNCATED", m.ORIG_DISPATCH)
        self.assertIn("QA01RF038NATIVEPACE_TRUNCATED", m.NATIVE_HELPER)
        self.assertNotIn("cpu->master_cycles +=", m.NATIVE_HELPER)
        self.assertNotIn("apu_writePortNow", m.NATIVE_HELPER)

    def test_prod_windows_sources_not_targeted(self):
        self.assertEqual(str(m.ORIGINAL), "cpuexec.cpp")
        self.assertEqual(str(m.NATIVE), "snesrecomp/runner/src/cpu_state.c")
        self.assertNotIn("rtl_apu_guest_cycle", m.NATIVE_HELPER)


if __name__ == "__main__":
    unittest.main()

"""RF039 original/native source-only receiver staging guardrail."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf039_target_receiver_observer as m
import qa01_rf037_sound_transaction_window as rf037


class RF039Receiver(unittest.TestCase):
    def test_original_preserves_one_real_mmio_read(self):
        src = "prefix\n" + rf037.ORIGINAL_SPC_EXTRA + "\n"
        out = m.patch_original(src)
        self.assertEqual(out.count("mmio_read(addr)"), src.count("mmio_read(addr)"))
        self.assertEqual(m.patch_original(out), out)
        self.assertIn("103918500ull", out)
        self.assertIn("103920500ull", out)
        self.assertIn(m.ENV, out)
        self.assertIn("QA01RF037ORIGSPC", out)
        self.assertIn("103310000ull", out)

    def test_native_preserves_original_callbacks_and_limit(self):
        src = rf037.NATIVE_APU_HELPER
        out = m.patch_native(src)
        self.assertEqual(m.patch_native(out), out)
        self.assertIn("f == 6091", out)
        self.assertIn("QA01RF037NATIVEBUS", out)
        self.assertIn("QA01RF037NATIVEBUS_TRUNCATED", out)
        self.assertIn("f < 6055 || f > 6064", out)
        for kind in ("schedule", "apply", "spc-read"):
            self.assertIn(kind, out)
        self.assertEqual(out.count("apu_writePortNow("), src.count("apu_writePortNow("))

    def test_refuse_missing_wrong_or_partial_stage(self):
        with self.assertRaisesRegex(ValueError, "requires exactly one"):
            m.patch_original("int fake;")
        with self.assertRaisesRegex(ValueError, "requires exactly one"):
            m.patch_native("int fake;")
        source = rf037.ORIGINAL_SPC_EXTRA
        out = m.patch_original(source)
        with self.assertRaisesRegex(ValueError, "partial/tampered"):
            m.patch_original(out.replace("103920500ull", "103920400ull"))

    def test_scope_never_claims_clock_or_acceptance(self):
        self.assertEqual(str(m.ORIGINAL), "apu/bapu/smp/core.cpp")
        self.assertEqual(str(m.NATIVE), "snesrecomp/runner/src/snes/apu.c")
        self.assertNotIn("master_cycles +=", m.ORIG_SUBSTITUTE + m.NATIVE_SUBSTITUTE)
        self.assertNotIn("cpuCyclesLeft +=", m.ORIG_SUBSTITUTE + m.NATIVE_SUBSTITUTE)


if __name__ == "__main__":
    unittest.main()

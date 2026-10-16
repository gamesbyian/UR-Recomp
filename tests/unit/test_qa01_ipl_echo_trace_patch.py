"""RF-030 installed only in exact disposable observer checkouts, fail closed."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_ipl_echo_trace_patch as m  # noqa: E402

CORE = (m.CORE_HEAD + "\n" + m.TICK_BULK_OLD + "\n" +
        m.READ_OLD + "\n" + m.WRITE_OLD)
ORIG_SMP = m.ORIGINAL_SMP_ANCHOR
ORIG_APU = (m.ORIGINAL_APU_HEADER + m.ORIGINAL_APU_ANCHOR + "\n" + m.CPU_READ_OLD +
            "\n" + m.CPU_WRITE_OLD)
NATIVE_APU = (m.NATIVE_HELPER_ANCHOR + "\n" + m.NATIVE_APPLY_OLD +
              "\n" + m.NATIVE_SCHEDULE_OLD + "\n" +
              m.NATIVE_READ_OLD + "\n" + m.NATIVE_ECHO_OLD)


class PinTests(unittest.TestCase):
    def test_all_stages_are_idempotent(self):
        for source, patch, witness in (
            (CORE, m.patch_original_core, "ur_qa01_rf030_spc_age"),
            (ORIG_SMP, m.patch_original_smp, "../../../cpuexec.h"),
            (ORIG_APU, m.patch_original_apu, "QA01IPLORIG side=cpu"),
            (NATIVE_APU, m.patch_native_apu, "QA01IPLNATIVE kind="),
        ):
            with self.subTest(witness=witness):
                treated = patch(source)
                self.assertIn(m.MARK, treated)
                self.assertIn(witness, treated)
                self.assertEqual(treated, patch(treated))

    def test_unknown_or_tampered_source_fails_closed(self):
        for source, patch, anchor, corrected in (
            (CORE, m.patch_original_core, m.READ_OLD, m.READ_NEW),
            (ORIG_SMP, m.patch_original_smp, m.ORIGINAL_SMP_ANCHOR, m.ORIGINAL_SMP_NEW),
            (ORIG_APU, m.patch_original_apu, m.CPU_READ_OLD, m.CPU_READ_NEW),
            (NATIVE_APU, m.patch_native_apu, m.NATIVE_ECHO_OLD, m.NATIVE_ECHO_NEW),
        ):
            with self.subTest(kind=patch.__name__):
                with self.assertRaisesRegex(ValueError, "unknown pinned"):
                    patch(source.replace(anchor, "OTHER", 1))
                stage = patch(source)
                with self.assertRaisesRegex(ValueError, "partial/tampered"):
                    patch(stage.replace(corrected, "OTHER", 1))

    def test_producer_instrumentation_is_read_only_and_explicit(self):
        for stage in (m.patch_original_core(CORE),
                      m.patch_original_smp(ORIG_SMP),
                      m.patch_original_apu(ORIG_APU),
                      m.patch_native_apu(NATIVE_APU)):
            self.assertIn('getenv("UR_QA01_IPL_ECHO_TRACE")', stage)
            self.assertNotIn("snes_frame_counter =", stage)
            self.assertNotIn("apu->portClock =", stage)
        core = m.patch_original_core(CORE)
        self.assertIn("ICPU.Frame >= 6050 && ICPU.Frame <= 6064", core)
        native = m.patch_native_apu(NATIVE_APU)
        self.assertIn("apu->portClock < 103300000ull", native)
        self.assertIn("apu->portClock > 103345000ull", native)

    def test_no_observer_in_windows_product_workflow(self):
        source = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_ipl_echo_trace_patch.py", source)
        self.assertNotIn("UR_QA01_IPL_ECHO_TRACE", source)


if __name__ == "__main__":
    unittest.main()

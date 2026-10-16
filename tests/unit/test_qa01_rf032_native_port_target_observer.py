"""RF032 native read-only queue/CPU-echo source pin and fail-closed tests."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf032_native_port_target_observer as q  # noqa: E402

APU_SOURCE = (
    'void apu_cycle(Apu* apu) {\n'
    + q.APU_HELPER_OLD + "\n"
    + q.APU_APPLY_OLD + "\n"
    + q.APU_SCHEDULE_OLD + "\n"
)
SNES_SOURCE = q.SNES_READ_OLD


class NativeObserverPins(unittest.TestCase):
    def test_idempotent_and_no_guest_mutations(self):
        # RF030 is always present on an actual guest before this stage.
        apu = APU_SOURCE.replace("void apu_cycle(Apu* apu) {",
                                 'void apu_cycle(Apu* apu) {\n'
                                 '  ur_qa01_rf030_native(apu, "schedule", val);')
        new = q.patch_apu(apu)
        self.assertEqual(q.patch_apu(new), new)
        self.assertIn(q.MARK, new)
        self.assertEqual(new.count(q.MARK), 1)
        self.assertEqual(new.count("  apu_writePortNow(apu, w->port, w->val);"), 1)
        self.assertIn("w->target_cycle", new)
        snes = q.patch_snes(SNES_SOURCE)
        self.assertEqual(q.patch_snes(snes), snes)
        self.assertEqual(snes.count(q.MARK), 1)
        self.assertIn("raw_apu_value = v", snes)
        self.assertEqual(snes.count("RtlApuUnlock();"), 1)

    def test_unknown_and_corrupted_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "RF030"):
            q.patch_apu(APU_SOURCE)
        with self.assertRaisesRegex(ValueError, "unknown pinned"):
            q.patch_snes(SNES_SOURCE.replace("RtlApuUnlock();", "OTHER;"))
        full = q.patch_snes(SNES_SOURCE)
        with self.assertRaisesRegex(ValueError, "partial"):
            q.patch_snes(full.replace("RtlApuUnlock();", "OTHER;"))

    def test_opt_in_bounded_and_no_windows_product_stage(self):
        for s in (q.APU_HELPER_NEW, q.SNES_READ_NEW):
            self.assertIn('getenv("UR_QA01_RF032_TARGET_ECHO")', s)
            self.assertIn("103322420ull", s)
            self.assertIn("103323100ull", s)
        shipping = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf032_native_port_target_observer.py", shipping)
        self.assertNotIn("UR_QA01_RF032_TARGET_ECHO", shipping)


if __name__ == "__main__":
    unittest.main()

"""RF052 native late clock observer: source-only exact callback contract."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf041_zoo_smp_debt_observer as rf041
import qa01_rf052_native_late_clock as rf052

class RF052OriginalNativeSourceContract(unittest.TestCase):
    def test_only_existing_native_queue_hook_is_extended(self):
        original=rf041.NATIVE_AFTER
        result=rf052.patch_native(original)
        self.assertEqual(result.count("apu_writePortNow("),original.count("apu_writePortNow("))
        self.assertEqual(result.count("QA01RF052NATIVE seq="),1)
        self.assertEqual(result.count("QA01RF052NATIVE_FINAL clock="),1)
        self.assertIn("104478000ull",result)
        self.assertIn("104495000ull",result)
        self.assertEqual(result.count("ur_qa01_rf037_port("),original.count("ur_qa01_rf037_port("))
        self.assertEqual(rf052.patch_native(result),result)
    def test_reject_missing_stage_or_partial_patched(self):
        with self.assertRaisesRegex(ValueError,"intact RF041"):
            rf052.patch_native("void callback(){}")
        result=rf052.patch_native(rf041.NATIVE_AFTER)
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf052.patch_native(result.replace("QA01RF052NATIVE_TRUNCATED","QA01RF052NATIVE_INCOMPLETE"))
if __name__=="__main__":unittest.main()

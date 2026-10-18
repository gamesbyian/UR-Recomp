"""RF051 source original SPC receiver preserves exactly one real mmio_read."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf041_zoo_smp_debt_observer as rf041
import qa01_rf051_original_late_spc_receiver as rf051
class LateSourceSMPTests(unittest.TestCase):
    def test_real_read_not_repeated_and_late_source_age(self):
        original=rf041.ORIGINAL_SPC_AFTER
        out=rf051.patch_original(original)
        self.assertEqual(out.count("mmio_read(addr)"),original.count("mmio_read(addr)"))
        self.assertIn("104485200ull",out)
        self.assertIn("104488000ull",out)
        self.assertIn("QA01RF051ORIGSPC seq=",out)
        self.assertIn("QA01RF051ORIGSPC_TRUNCATED",out)
        self.assertEqual(rf051.patch_original(out),out)
    def test_incomplete_source_stage_rejected(self):
        with self.assertRaisesRegex(ValueError,"requires exact source"):
            rf051.patch_original("  return mmio_read(addr);")
        out=rf051.patch_original(rf041.ORIGINAL_SPC_AFTER)
        with self.assertRaisesRegex(ValueError,"partial original"):
            rf051.patch_original(out.replace("QA01RF051ORIGSPC seq=","QA01RF051BROKEN seq="))
if __name__=="__main__":unittest.main()

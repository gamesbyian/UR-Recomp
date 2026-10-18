"""Original Snes9x RF050 source port publication must not duplicate guest IO."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf037_upstream_writer_observer as upstream
import qa01_rf050_original_late_port_publication as rf050

class RF050Tests(unittest.TestCase):
    def test_read_only_source_port_visibility(self):
        source="    SNES::cpu.port_write(port & 3, byte);\n"+upstream.NEW_ORIG
        after=rf050.patch_original(source)
        self.assertEqual(after.count("SNES::cpu.port_write(port & 3, byte);"),1)
        self.assertEqual(after.count("QA01RF050ORIGAPU seq="),1)
        self.assertEqual(after.count("QA01RF050ORIGAPU_TRUNCATED"),1)
        self.assertIn("104200000ull",after)
        self.assertIn("106500000ull",after)
        self.assertIn("CPU.V_Counter == 159u",after)
        self.assertEqual(rf050.patch_original(after),after)

    def test_reject_missing_previously_observed_real_write_or_drift(self):
        source="    SNES::cpu.port_write(port & 3, byte);\n"+upstream.NEW_ORIG
        with self.assertRaisesRegex(ValueError,"exact post-authoritative RF037"):
            rf050.patch_original(source.replace(upstream.NEW_ORIG,""))
        after=rf050.patch_original(source)
        with self.assertRaisesRegex(ValueError,"partly staged"):
            rf050.patch_original(after.replace("QA01RF050ORIGAPU seq=","QA01RF050BAD seq=",1))
        with self.assertRaisesRegex(ValueError,"alter/duplicate"):
            rf050.patch_original(source.replace(
                "    SNES::cpu.port_write(port & 3, byte);\n",
                "    SNES::cpu.port_write(port & 3, byte);\n"*2))
if __name__=="__main__":
    unittest.main()

"""RF070: original-only stack probes must not break Snes9x SA-1 dual compile."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf064_original_post_call_pull as rf64
import qa01_rf066_original_consumed_sequence as rf66
import qa01_rf070_original_sa1_probe_isolation as rf70

def fixture():
    return (rf45.HELPER + "#ifndef SA1_OPCODES\n#define KEEP_UPSTREAM_PREEXISTING_GUARD 1\n#endif\n"
            + rf70.RF066_HELPER
            + "#define W S9xSetWord(a,b,c,d)\n"
            + "#define R S9xGetWord(a,b)\n")

class SourceSa1ObserverIsolation(unittest.TestCase):
    def test_only_original_observer_helpers_excluded_from_SA1(self):
        old=fixture()
        new=rf70.patch(old)
        self.assertEqual(new.count(rf70.STAMP),2)
        self.assertEqual(new.count("#ifndef SA1_OPCODES"),3)
        self.assertEqual(new.count(f"#ifndef SA1_OPCODES /* {rf70.STAMP} */"),2)
        self.assertEqual(new.count(rf70.RF045_SA1_STUB),1)
        self.assertEqual(new.count(rf70.RF064_SA1_STUB),1)
        self.assertIn('ur_rf066_source',new.lower() if False else
                      'UR_QA01_RF066_ORIGINAL_POST_CALL_EXECUTED_READ')
        for op in ("S9xGetByte(","S9xGetWord(","S9xSetByte(",
                   "S9xSetWord(","S9xOpcode_NMI();"):
            self.assertEqual(new.count(op),old.count(op))

    def test_source_main_original_observer_keeps_all_actual_reporters(self):
        new=rf70.patch(fixture())
        self.assertIn('QA01RF045ORIGSTACK seq=',new)
        self.assertIn('QA01RF064ORIGPULL f=',new)
        self.assertIn('QA01RF066ORIGCONSUMED seq=',new)
        self.assertIn('++ur_rf063_source_bus_seq',new)

    def test_missing_rf045_rf064_or_rf066_identity_rejected(self):
        old=fixture()
        for bad in (old.replace(rf45.STAMP,"removed"),
                    old.replace(rf64.STAMP,"removed"),
                    old.replace(rf66.STAMP,"removed"),
                    old.replace("QA01RF064ORIGPULL","RF064_WRONG"),
                    old.replace("QA01RF066ORIGCONSUMED","RF066_WRONG")):
            with self.subTest(bad=bad[:60]),self.assertRaises(ValueError):
                rf70.patch(bad)

    def test_preexisting_main_guard_does_not_break_our_count(self):
        old=fixture()+"\n#ifndef SA1_OPCODES\n#endif\n"
        self.assertEqual(rf70.patch(old).count("#ifndef SA1_OPCODES"),4)

    def test_rejects_duplicate_staging(self):
        first=rf70.patch(fixture())
        with self.assertRaisesRegex(ValueError,"already"):
            rf70.patch(first)

if __name__=="__main__":
    unittest.main()

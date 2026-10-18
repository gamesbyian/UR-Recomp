"""RF049: only exact source-qualified original opcode post-dispatch census."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf048_original_sound_pointer_witness as rf048
import qa01_rf049_sound_operand_census as rf049

class SourceOperandCensusTests(unittest.TestCase):
    @staticmethod
    def staged():
        before=rf035.ORIG_BEFORE+rf035.ORIG_DISPATCH+"\n"+rf035.ORIG_AFTER
        return rf048.patch_original(before)

    def test_all_true_LDA_opcodes_counted_without_extra_dispatch(self):
        original=self.staged()
        result=rf049.patch_original(original)
        self.assertEqual(result.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(result.count("/* UR_QA01_RF049_SOUND_OPERAND:"),1)
        self.assertIn('ur_rf035_pc == 0x82F0u',result)
        self.assertIn('rf049_ea == 0x13C774u',result)
        self.assertIn('rf049_ea == 0x13D0B4u',result)
        self.assertIn('QA01RF049FINAL',result)
        self.assertIn('(unsigned)ICPU.Frame > 6150u',result)
        self.assertIn('QA01RF049STA',result)
        self.assertEqual(rf049.patch_original(result),result)

    def test_reject_original_without_rf048_or_tampered_census(self):
        with self.assertRaisesRegex(ValueError,"intact original RF048"):
            rf049.patch_original(rf035.ORIG_BEFORE+rf035.ORIG_DISPATCH+rf035.ORIG_AFTER)
        patched=rf049.patch_original(self.staged())
        with self.assertRaisesRegex(ValueError,"partially modified"):
            rf049.patch_original(patched.replace("QA01RF049FINAL","QA01RF049BAD",1))

if __name__=="__main__":
    unittest.main()

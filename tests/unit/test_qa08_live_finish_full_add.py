"""Real Win32 original-native finish add-before/after brightness model guards."""
import unittest
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_live_finish_full_add as q

class FinishFullAddMathTest(unittest.TestCase):
    def test_exact_half_conjecture_retraction_and_native_observed_full_add(self):
        self.assertEqual(q.reference_palette_first_full_add((13,0,0),(1,7,1),7),(49,24,0))
        self.assertEqual(q.native_full_add_then_brightness((13,0,0),(1,7,1),7),(57,24,0))
        self.assertEqual(tuple(x+y for x,y in zip(q.MAIN,q.SUB)),q.POST)
        self.assertFalse(0x04 & 0x40)
        self.assertFalse(0x04 & 0x80)

    def test_reject_unqualified_original_and_stale_liveness(self):
        with self.assertRaisesRegex(ValueError,"verified original"):
            q.validate_live({}, {}, {}, {}, b"")
        for v in [(-1,7),(32,7),(10,16)]:
            with self.assertRaises(ValueError):
                q.brightness5(*v)

if __name__=="__main__":
    unittest.main()

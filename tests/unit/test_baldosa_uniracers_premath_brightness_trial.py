"""Adversarial pinned title-only pre-math brightness candidate."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools import baldosa_uniracers_premath_brightness_trial as s
class TestSource(unittest.TestCase):
    def test_formula_512_values_identity_and_source_examples(self):
        for b in range(16):
            for v in range(32):
                self.assertEqual(s.brightness5(v,b),(v*b+7)//15)
        self.assertEqual([s.brightness5(v,7) for v in (14,18,10,9)],
                         [7,8,5,4])
        self.assertEqual(s.brightness5(13,7)+s.brightness5(1,7),6)
        self.assertEqual(s.brightness5(14,7),7)
        self.assertRaises(ValueError,s.brightness5,32,7)
    def test_exact_pinned_legacy_replace_and_second_pass_idempotent(self):
        src=s.START+s.AFTER_SUB+ "".join("r -= "+x+";\n" for x in s.FIXED)+s.OUTPUT
        trial=s.patched(src)
        self.assertEqual(trial,s.patched(trial))
        self.assertIn(s.REPLACEMENT,trial)
        self.assertIn(s.BRIGHTEN,trial)
        self.assertEqual(trial.count(s.MARK),2)
        for source in (src.replace(s.OUTPUT,""),
                       trial.replace(s.MARK,"BAD",1),
                       trial.replace("return (value * brightness + 7) / 15;",
                                     "return (value * brightness) / 15;"),
                       src+src):
            with self.subTest(s=source[:35]),self.assertRaises(ValueError):
                s.patched(source)
if __name__=="__main__":unittest.main()

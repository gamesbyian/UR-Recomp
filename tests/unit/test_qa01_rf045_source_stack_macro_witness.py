"""RF045 stack macro probe preserves one exact Snes9x bus access per macro."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf045_source_stack_macro_witness as m

class StagedStack(unittest.TestCase):
 def fixture(self):
  return ("\n/* authentic source NMI macro anchors */\n" +
          "\n".join(a for a,_ in m.PAIRS)+"\n")
 def test_pinned_macro_exactness_and_idempotence(self):
  old=self.fixture()
  new=m.patch(old)
  self.assertEqual(m.patch(new),new)
  self.assertEqual(new.count(m.HELPER),1)
  for old_macro,new_macro in m.PAIRS:
   self.assertEqual(new.count(new_macro),1)
   for op in ("S9xSetWord(","S9xSetByte(","S9xGetWord(","S9xGetByte("):
    self.assertEqual(old_macro.count(op),new_macro.count(op))
  self.assertIn("QA01RF045ORIGSTACK_TRUNCATED",new)
 def test_one_effective_stack_width_and_address_each_kind(self):
  new=m.patch(self.fixture())
  for op in ('"pushW"','"pushB"','"pullW"','"pullB"'):
   self.assertEqual(new.count(op),1)
  self.assertIn("ur_rf045_sp0 - 1",new)
  self.assertIn("ur_rf045_sp0 + 1",new)
  self.assertIn("++Registers.S.W",new)
  self.assertIn("Registers.S.W--",new)
  self.assertIn("S9xSetWord(ur_rf045_value, Registers.S.W - 1, WRAP_BANK, WRITE_10)",new)
 def test_target_is_strict_and_non_emission_is_not_no_reads(self):
  h=m.HELPER
  self.assertIn("ICPU.Frame<1017u",h)
  self.assertIn("ICPU.Frame>1025u",h)
  self.assertIn("base>0x01f1u",h)
  self.assertIn("base+width-1u<0x01edu",h)
  self.assertNotIn("S9xGetByte(",h)
  self.assertNotIn("S9xGetWord(",h)
 def test_source_drift_and_partial_stage_fail(self):
  with self.assertRaisesRegex(ValueError,"pinned"):m.patch("irrelevant\n")
  with self.assertRaisesRegex(ValueError,"tampered"):
   m.patch(m.patch(self.fixture()).replace('kind=%s','kind=bad'))
if __name__=="__main__":unittest.main()

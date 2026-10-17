"""RF042 native RF026 final-cycle tied-port A/B source contract tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf042_equal_age_queue_trial as m
import baldosa_spc_bus_cycle_patch as rf026

BASE="""static void apu_drainPortQueue(Apu* apu) {
  while (apu->portQHead != apu->portQTail) {
    ApuPortWrite *w = &apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)];
    if (w->target_cycle > apu->portClock)
      break;
    apu_applyPortWrite(apu, w);
    apu->portQHead++;
  }
}
void apu_cycle(Apu* apu) {
""" + rf026.CORRECTED_APU + """  apu->portClock++;
}
"""
class TieTrial(unittest.TestCase):
 def test_real_rf026_cycle_one_opcode_one_tick(self):
  a=m.patch(BASE)
  self.assertEqual(m.patch(a),a)
  for token in ("spc_runOpcode(apu->spc)","apu->portClock++;",
                "apu_applyPortWrite(apu, w);","apu->portQHead++;"):
   self.assertEqual(a.count(token),BASE.count(token))
  self.assertIn("rf042_defer_equal && w->target_cycle == apu->portClock",a)
  self.assertIn("apu_drainPortQueue(apu, rf042_hold);",a)
  self.assertIn("apu_drainPortQueue(apu, false);",a)
  self.assertIn("QA01RF042TIE",a)
  self.assertIn("apu->pad[0] == 1",a)
 def test_missing_rf026_or_tampered_stage_fails(self):
  with self.assertRaisesRegex(ValueError,"pinned RF026"):
   m.patch("void apu_cycle(Apu* apu) {}")
  with self.assertRaisesRegex(ValueError,"tampered"):
   m.patch(m.patch(BASE).replace("phase=after-opcode","phase=wrong"))
 def test_unset_env_retains_native_pre_opcode_drain(self):
  x=m.patch(BASE)
  self.assertIn("getenv(\"UR_QA01_RF042_TIE_AB\") != NULL",x)
  self.assertIn("apu->cpuCyclesLeft == 0 && apu->pad[0] == 1",x)
  self.assertEqual(x.count("spc_runOpcode(apu->spc)"),1)
 def test_no_synthetic_cycles_or_target_rewrites(self):
  x=m.patch(BASE)
  self.assertNotIn("portClock += 7",x)
  self.assertNotIn("target_cycle +=",x)
  self.assertEqual(x.count("apu->portClock++"),BASE.count("apu->portClock++"))
if __name__=="__main__":unittest.main()

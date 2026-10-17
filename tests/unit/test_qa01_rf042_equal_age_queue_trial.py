"""RF042 native-only equal-target queue order: source-anchor and safety tests."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf042_equal_age_queue_trial as m

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
  apu_drainPortQueue(apu);
  if(apu->cpuCyclesLeft == 0) {
    apu->cpuCyclesLeft = spc_runOpcode(apu->spc);
  }
  apu->cpuCyclesLeft--;
  apu->portClock++;
}
"""
class TieTrial(unittest.TestCase):
    def test_once_only(self):
        after=m.patch(BASE)
        self.assertEqual(after,m.patch(after))
        for op in ("spc_runOpcode(apu->spc)","apu->portClock++;",
                   "apu_applyPortWrite(apu, w);","apu->portQHead++;"):
            self.assertEqual(after.count(op),BASE.count(op))
        self.assertIn("rf042_defer_equal && w->target_cycle == apu->portClock",after)
        self.assertIn("apu_drainPortQueue(apu, rf042_opcode_boundary);",after)
        self.assertIn("apu_drainPortQueue(apu, false);",after)
        self.assertIn("QA01RF042TIE",after)
    def test_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"pinned"):
            m.patch("void unrelated(void) {}")
        with self.assertRaisesRegex(ValueError,"tampered"):
            m.patch(m.patch(BASE).replace("phase=after-opcode","phase=wrong"))
    def test_control_is_default(self):
        after=m.patch(BASE)
        self.assertIn("getenv(\"UR_QA01_RF042_TIE_AB\") != NULL",after)
        self.assertIn("rf042_on && apu->cpuCyclesLeft == 0",after)
    def test_never_increments_or_moves_native_clock(self):
        after=m.patch(BASE)
        self.assertNotIn("portClock += 7",after)
        self.assertNotIn("target_cycle +=",after)
        self.assertEqual(after.count("portClock++"),BASE.count("portClock++"))
if __name__=="__main__":unittest.main()

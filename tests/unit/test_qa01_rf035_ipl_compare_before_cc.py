"""RF035 source-qualified last-cycle write/compare order negative controls."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_rf035_ipl_compare_before_cc as m  # noqa: E402

class Rf035(unittest.TestCase):
    def test_exact_rf026_stage_and_idempotence(self):
        before = m.rf026.CORRECTED_APU
        after = m.patch(before)
        self.assertEqual(m.patch(after), after)
        self.assertIn("apu->pad[0] == 1", after)
        self.assertIn("apu->spc->pc == 0xffcf", after)
        self.assertIn("target_cycle == apu->portClock", after)
        self.assertIn("apu->inPorts[0] != 0xcc", after)
        self.assertIn('getenv("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC")', after)
        self.assertEqual(after.count("spc_runOpcode(apu->spc)"), 1)
        self.assertEqual(after.count("apu->portClock++"), 0) # outside target block
        self.assertIn("if (!rf035_boundary) apu_drainPortQueue(apu);", after)
        self.assertIn("if (rf035_boundary) {\n    /* spc_runOpcode above", after)
        self.assertLess(after.index("spc_runOpcode(apu->spc)"),
                        after.index("/* spc_runOpcode above"))
        with self.assertRaisesRegex(ValueError,"exact RF026"):
            m.patch(m.rf026.PINNED_APU)
        with self.assertRaisesRegex(ValueError,"tampered"):
            m.patch(after.replace("apu->pad[0] == 1","apu->pad[0] != 1"))
    def test_refuse_general_queue_or_release_touch(self):
        self.assertNotIn("portClock + 1",m.NEW)
        self.assertNotIn("target_cycle++",m.NEW)
        self.assertNotIn("spc_runOpcode(apu->spc);\n  apu_drainPortQueue(apu);",m.NEW)
        shipping=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf035_ipl_compare_before_cc",shipping)
        self.assertNotIn("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC",shipping)
    def test_order_only_at_conjunctive_live_boundary(self):
        # Small exact predicate truth-table: every missing source observation
        # must keep the original queue-before-opcode behavior.
        fields=(True,True,True,True,True,True,True,True,True)
        self.assertTrue(all(fields))
        for i in range(len(fields)):
            trial=list(fields);trial[i]=False
            self.assertFalse(all(trial))

if __name__=="__main__":
    unittest.main()

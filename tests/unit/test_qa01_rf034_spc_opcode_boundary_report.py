"""RF034 actual original/native SPC opcode clock/debt witness must bind RF033."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"tests"/"unit"))
import qa01_rf034_spc_opcode_boundary_report as m  # noqa: E402
from test_qa01_rf033_cpu_master_clock_report import ORIG,NATIVE  # noqa: E402

O=ORIG+"\nQA01RF034ORIG before=103322545 after=103322546 debtbefore=2 debtafter=1 pcbefore=FFCF pcafter=FFD0 opbefore=78 opafter=78 cycbefore=0 cycafter=0 value=CC"
N=NATIVE+"\nQA01RF034NATIVE age=103322545 target=103322545 pc=FFCF left=2 qhead=0 qtail=1 value=CC"

class InterpreterClockBoundary(unittest.TestCase):
    def test_exact_source_boundaries_no_new_event_credit(self):
        x=m.summarize(O,N)
        self.assertEqual(x["original_first_cc"]["spc_clock_debt_before"],2)
        self.assertEqual(x["native_first_cc"]["native_opcode_cycles_left_before_port_apply"],2)
        self.assertEqual(x["original_first_cc"]["actual_spc_ticks_during_source_execute"],1)
        self.assertFalse(x["source_correct_cpu_port_visibility_fix_proven"])
        self.assertFalse(x["cross_source_absolute_spc_phase_sync_proven"])
        self.assertEqual(x["complete_gameplay_event_credit"],0)

    def test_first_actual_source_observation_mandatory(self):
        with self.assertRaisesRegex(ValueError,"missing actual original/native"):
            m.summarize(ORIG,N)
        with self.assertRaisesRegex(ValueError,"missing actual original/native"):
            m.summarize(O,NATIVE)
        with self.assertRaisesRegex(ValueError,"does not bind RF033"):
            m.summarize(O.replace("after=103322546 debtbefore","after=103322547 debtbefore"),N)
        with self.assertRaisesRegex(ValueError,"does not bind first CC"):
            m.summarize(O,N.replace("target=103322545 pc","target=103322546 pc"))
        with self.assertRaisesRegex(ValueError,"impossible native"):
            m.summarize(O,N.replace("left=2","left=65"))
        with self.assertRaisesRegex(ValueError,"incomplete"):
            m.summarize(O,N.replace(" left=2",""))

if __name__=="__main__":
    unittest.main()

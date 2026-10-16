"""RF033 explicit original/native CPU master-clock trace must extend actual RF032."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"tests"/"unit"))
import qa01_rf033_cpu_master_clock_report as report  # noqa: E402
from test_qa01_rf032_native_port_target_report import O, N  # noqa: E402

ORIG = O + "\nQA01RF033ORIG before=103322545 after=103322546 h=312 v=119 ref=308 rem=10000 num=15664 den=328125 predicted=1 value=CC"
NATIVE = N + "\nQA01RF033NATIVE age=103322463 guest=777 master=211000123 frame=6057 framestart=210400000 extended=1 valid=1 value=CC pc=FFCF"

class MasterClockReport(unittest.TestCase):
    def test_qualified_first_writer_without_cross_phase_claim(self):
        r=report.summarize(ORIG,NATIVE)
        self.assertEqual(r["original_first_cc"]["cpu_beam_v"],119)
        self.assertEqual(r["original_first_cc"]["cpu_master_within_scanline"],312)
        self.assertEqual(r["original_first_cc"]["original_spc_ratio_denominator"],328125)
        self.assertEqual(r["native_first_cc"]["guest_apu_cycle_at_cpu_write"],777)
        self.assertEqual(r["native_first_cc"]["apu_port_clock_when_cpu_bus_write_queued"],103322463)
        self.assertEqual(r["native_first_cc"]["stored_port_target"],103322545)
        self.assertFalse(r["independent_original_native_master_clock_domains_phase_identical_proven"])
        self.assertEqual(r["usa_complete_event_acceptance_credit"],0)

    def test_missing_writer_and_mismatch_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"missing executed"):
            report.summarize(O,NATIVE)
        with self.assertRaisesRegex(ValueError,"missing executed"):
            report.summarize(ORIG,N)
        with self.assertRaisesRegex(ValueError,"actual first CC"):
            report.summarize(ORIG.replace("after=103322546","after=103322547"),NATIVE)
        with self.assertRaisesRegex(ValueError,"bind executed queue"):
            report.summarize(ORIG,NATIVE.replace("guest=777 master","guest=778 master"))
        with self.assertRaisesRegex(ValueError,"original SPC ratio"):
            report.summarize(ORIG.replace("den=328125","den=0"),NATIVE)
        with self.assertRaisesRegex(ValueError,"native frame clock mode"):
            report.summarize(ORIG,NATIVE.replace("extended=1","extended=2"))
        with self.assertRaisesRegex(ValueError,"truncated"):
            report.summarize(ORIG,NATIVE+"\nQA01RF033NATIVE_TRUNCATED")

if __name__=="__main__":
    unittest.main()

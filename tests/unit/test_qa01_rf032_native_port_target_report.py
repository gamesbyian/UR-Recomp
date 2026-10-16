"""RF032 executed queue and CPU-read fail-closed receipts, no event credit."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf032_native_port_target_report as r  # noqa: E402

O = "\n".join([
    "QA01IPLORIG side=cpu kind=write frame=0 v=119 h=312 age=103322546 pc=0000 op=00 value=CC ipl=0",
    "QA01IPLORIG side=spc kind=read frame=0 v=119 h=508 age=103322554 pc=FFD2 op=78 value=CC ipl=1",
    "QA01IPLORIG side=spc kind=echo frame=0 v=119 h=1136 age=103322580 pc=FFF7 op=C4 value=CC ipl=1",
    "QA01IPLORIG side=cpu kind=poll frame=0 v=119 h=1166 age=103322584 pc=0000 op=00 value=CC ipl=0",
])
N = "\n".join([
    "QA01IPLNATIVE kind=schedule age=103322463 pc=FFCF value=CC q=1 in=00 out=AA",
    "QA01RF032 kind=schedule age=103322463 guest=777 target=103322545 port=0 value=CC raw=AA in=00 out=AA pc=FFCF qhead=0 qtail=1 guestanchor=700 targetanchor=103322468",
    "QA01IPLNATIVE kind=apply age=103322545 pc=FFCF value=CC q=1 in=CC out=AA",
    "QA01RF032 kind=apply age=103322545 guest=0 target=103322545 port=0 value=CC raw=AA in=00 out=AA pc=FFCF qhead=0 qtail=1 guestanchor=700 targetanchor=103322468",
    "QA01IPLNATIVE kind=read age=103322546 pc=FFD2 value=CC q=0 in=CC out=AA",
    "QA01IPLNATIVE kind=echo age=103322571 pc=FFF7 value=CC q=0 in=CC out=CC",
    "QA01RF032 kind=cpu-poll age=103322570 guest=0 target=0 port=0 value=AA raw=AA in=CC out=AA pc=FFF7 qhead=1 qtail=1 guestanchor=700 targetanchor=103322468",
    "QA01RF032 kind=cpu-poll age=103322575 guest=0 target=0 port=0 value=CC raw=CC in=CC out=CC pc=FFF7 qhead=1 qtail=1 guestanchor=700 targetanchor=103322468",
])


class NativeTargetAndPoll(unittest.TestCase):
    def test_exact_qualifying_first_cc_and_clock_boundaries(self):
        x = r.summarize(O, N)
        self.assertEqual(x["native_first_cc_schedule"]["stored_target_cycle"], 103322545)
        self.assertEqual(x["native_first_cc_apply"]["applied_minus_stored_target_cycle"], 0)
        self.assertEqual(x["native_cpu_first_cc_echo_read"]["echo_to_cpu_observation_spc_cycles"], 4)
        self.assertEqual(x["native_cpu_first_cc_echo_read"]["raw_output_port"], "CC")
        self.assertEqual(x["release_complete_usa_event_credit"], 0)
        self.assertFalse(x["original_native_absolute_spc_ages_independently_calibrated"])

    def test_missing_native_cpu_poll_cc_fails(self):
        with self.assertRaisesRegex(ValueError, "missing executed native CPU"):
            r.summarize(O, N.replace("value=CC raw=CC", "value=AA raw=AA"))
        with self.assertRaisesRegex(ValueError, "missing native CPU earlier"):
            r.summarize(O, N.replace("value=AA raw=AA", "value=CC raw=CC"))

    def test_tamper_truncation_unsorted_or_missing_target_rejected(self):
        for updated, error in (
            (N + "\nQA01RF032_CPU_TRUNCATED", "truncated"),
            (N.replace("target=103322545 port=0 value=CC raw=AA in=00 out=AA pc=FFCF qhead=0 qtail=1 guestanchor=700 targetanchor=103322468",
                       "target=103322546 port=0 value=CC raw=AA in=00 out=AA pc=FFCF qhead=0 qtail=1 guestanchor=700 targetanchor=103322468",1), "stored first CC target"),
            (N.replace("QA01RF032 kind=apply age=103322545", "QA01RF032 kind=apply age=103322400"), "outside exact"),
            (N.replace("value=CC raw=CC in=CC", "value=GG raw=CC in=CC"), "invalid RF032"),
        ):
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError, error):
                    r.summarize(O, updated)

    def test_no_synthetic_original_qualification(self):
        with self.assertRaisesRegex(ValueError, "missing original"):
            r.summarize(O.replace("kind=poll", "kind=write"), N)


if __name__ == "__main__":
    unittest.main()

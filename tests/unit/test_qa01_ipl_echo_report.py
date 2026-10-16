"""Fail-closed executed IPL transport receipt, no inferred phase or event credit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_ipl_echo_report as m  # noqa: E402

O = "\n".join([
    "QA01IPLORIG side=cpu kind=write frame=6057 v=240 h=40 age=103322546 pc=0000 op=00 value=CC ipl=0",
    "QA01IPLORIG side=spc kind=read frame=6057 v=240 h=60 age=103322554 pc=FFD2 op=78 value=CC ipl=1",
    "QA01IPLORIG side=spc kind=echo frame=6057 v=240 h=65 age=103322559 pc=FFD8 op=C4 value=CC ipl=1",
    "QA01IPLORIG side=cpu kind=poll frame=6057 v=240 h=68 age=103322559 pc=0000 op=00 value=CC ipl=0",
])
N = "\n".join([
    "QA01IPLNATIVE kind=schedule age=103322541 pc=FFCF value=CC q=1 in=00 out=00",
    "QA01IPLNATIVE kind=apply age=103322541 pc=FFCF value=CC q=1 in=CC out=00",
    "QA01IPLNATIVE kind=read age=103322543 pc=FFD2 value=CC q=0 in=CC out=00",
    "QA01IPLNATIVE kind=echo age=103322548 pc=FFD8 value=CC q=0 in=CC out=CC",
])


class ExecutedIPLSchema(unittest.TestCase):
    def test_two_independent_executed_clock_domains(self):
        v = m.summarize(O, N)
        self.assertEqual(v["original_ipl_first_cc"]["write_to_read_spc_cycles"], 8)
        self.assertEqual(v["native_ipl_first_cc"]["apply_to_read_spc_cycles"], 2)
        self.assertEqual(v["original_ipl_first_cc"]["first_read_pc"], "FFD2")
        self.assertEqual(v["native_ipl_first_cc"]["first_read_pc"], "FFD2")
        self.assertFalse(v["original_native_independent_clock_phase_aligned"])
        self.assertEqual(v["release_complete_usa_event_credit"], 0)

    def test_refuse_lag_rephase_truncation_and_missing_echo(self):
        for old, changed, error in (
            ("age=103322554", "age=103322545", "chronology"),
            ("QA01IPLORIG side=spc kind=echo", "QA01IPLORIG side=spc kind=other", "unrecognized"),
            ("value=CC ipl=1", "value=CD ipl=1", "missing actual"),
            ("pc=FFD2 op=78", "pc=FFFF op=78", "compare instruction"),
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, error):
                    m.summarize(O.replace(old, changed, 1), N)
        with self.assertRaisesRegex(ValueError, "tracing exhausted"):
            m.summarize(O + "\nQA01IPLORIG_TRUNCATED", N)
        with self.assertRaisesRegex(ValueError, "tracing exhausted"):
            m.summarize(O, N + "\nQA01IPLNATIVE_TRUNCATED")

    def test_reject_fake_complete_event_by_missing_transport(self):
        for s in ("QA01IPLNATIVE kind=apply", "QA01IPLNATIVE kind=schedule",
                  "QA01IPLNATIVE kind=read", "QA01IPLNATIVE kind=echo"):
            with self.subTest(missing=s):
                with self.assertRaisesRegex(ValueError, "(missing actual|timestamped|compare PC)"):
                    m.summarize(O, "\n".join(line for line in N.splitlines() if s not in line))


if __name__ == "__main__":
    unittest.main()

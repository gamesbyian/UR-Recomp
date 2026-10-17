"""RF039: source-/native-executed target receiver sequence is fail-closed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf039_target_receiver_report as m


class ReceiverWitness(unittest.TestCase):
    def fixture(self):
        source = (
            "QA01RF037ORIGCPU2 age=103919450 v=116 h=442 port=2 val=24\n"
            "QA01RF037ORIGCPU2 age=103919475 v=116 h=972 port=3 val=02\n"
            "QA01RF037ORIGSPC age=103919450 pc=154F v=116 h=442 port=2 val=23\n"
            "QA01RF037ORIGSPC age=103919457 pc=154F v=116 h=600 port=2 val=24\n"
            "QA01RF037ORIGSPC age=103919462 pc=1553 v=116 h=704 port=3 val=E2\n"
            "QA01RF037ORIGSPC age=103919465 pc=1555 v=116 h=756 port=2 val=24\n"
            "QA01RF037ORIGSPC age=103919505 pc=1553 v=117 h=244 port=3 val=02\n")
        native = (
            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176886834 reg=2142 val=24 scope=x\n"
            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208 reg=2143 val=02 scope=x\n"
            "QA01RF037NATIVEBUS kind=schedule frame=6091 age=103919298 target=103919434 pc=1555 port=2 val=24 q=1\n"
            "QA01RF037NATIVEBUS kind=schedule frame=6091 age=103919444 target=103919452 pc=1555 port=3 val=02 q=1\n"
            "QA01RF037NATIVEBUS kind=apply frame=6091 age=103919434 target=103919434 pc=154D port=2 val=24 q=2\n"
            "QA01RF037NATIVEBUS kind=apply frame=6091 age=103919452 target=103919452 pc=14D7 port=3 val=02 q=2\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919427 target=103919427 pc=154F port=2 val=23 q=2\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919434 target=103919434 pc=154F port=2 val=24 q=0\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919439 target=103919439 pc=1553 port=3 val=E2 q=0\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919443 target=103919443 pc=1555 port=2 val=24 q=0\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919482 target=103919482 pc=1553 port=3 val=02 q=0\n")
        return source, native

    def test_complete_ordered_receiver_with_independent_clock_labels(self):
        o, n = self.fixture()
        d = m.analyze(o, n)
        self.assertTrue(d["receiver_coverage_complete"])
        self.assertTrue(d["native_schedule_prefix_matches_actual_writers"])
        self.assertTrue(d["target_recipient_pc_port_value_sequence_equal"])
        self.assertEqual(d["native_target_local_write_indices_zero_based"], [0, 1])
        self.assertEqual(len(d["native_target_apply"]), 2)
        self.assertEqual(len(d["source_target_spc_reads"]), 5)
        self.assertEqual(len(d["native_target_spc_reads"]), 5)
        self.assertEqual(d["source_minus_native_target_spc_age_differences"],
                         [23, 23, 23, 22, 23])
        self.assertFalse(d["phase_or_bus_order_equivalence_proven"])
        self.assertFalse(d["clock_fix_justified"])
        self.assertEqual(d["complete_usa_events_accepted"], 0)

    def test_missing_receiver_or_schedule_fails_closed(self):
        o, n = self.fixture()
        d = m.analyze(o.replace("QA01RF037ORIGSPC", "missing"), n)
        self.assertFalse(d["receiver_coverage_complete"])
        d = m.analyze(o, n.replace("kind=schedule", "kind=missing"))
        self.assertFalse(d["receiver_coverage_complete"])
        self.assertFalse(d["native_schedule_prefix_matches_actual_writers"])

    def test_wrong_receiver_value_or_pc_fails_closed(self):
        o, n = self.fixture()
        for incorrect in (
            o.replace("age=103919462 pc=1553", "age=103919462 pc=1500"),
            o.replace("age=103919457 pc=154F v=116 h=600 port=2 val=24",
                      "age=103919457 pc=154F v=116 h=600 port=2 val=23")
        ):
            self.assertFalse(m.analyze(incorrect, n)["receiver_coverage_complete"])
        broken_native = n.replace("age=103919482 target=103919482 pc=1553 port=3 val=02",
                                  "age=103919482 target=103919482 pc=1553 port=3 val=03")
        self.assertFalse(m.analyze(o, broken_native)["receiver_coverage_complete"])

    def test_wrong_writer_order_truncation_and_missing_target_rejected(self):
        o, n = self.fixture()
        with self.assertRaisesRegex(ValueError, "target missing"):
            m.analyze(o, n.replace("master=2176886834", "master=0"))
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.analyze(o, n + "QA01RF037NATIVEBUS_TRUNCATED frame=6091\n")
        with self.assertRaisesRegex(ValueError, "no longer consecutive"):
            n2 = n.replace(
                "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208",
                "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=0 reg=2142 val=00 scope=x\n"
                "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208")
            m.analyze(o, n2)


if __name__ == "__main__":
    unittest.main()

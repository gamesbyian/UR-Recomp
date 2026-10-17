"""RF039 fails closed when receiver/queue witness cannot be attributed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf039_target_receiver_report as m


class ReceiverWitness(unittest.TestCase):
    def fixture(self):
        orig = (
            "QA01RF037ORIGCPU2 age=103919450 v=116 h=442 port=2 val=24\n"
            "QA01RF037ORIGCPU2 age=103919475 v=116 h=972 port=3 val=02\n"
            "QA01RF037ORIGSPC age=103919460 pc=A123 v=116 h=490 port=2 val=24\n"
            "QA01RF037ORIGSPC age=103919480 pc=A123 v=116 h=990 port=3 val=02\n")
        nat = (
            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176886834 reg=2142 val=24 scope=x\n"
            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208 reg=2143 val=02 scope=x\n"
            "QA01RF037NATIVEBUS kind=schedule frame=6091 age=10000 target=10010 pc=A123 port=2 val=24 q=1\n"
            "QA01RF037NATIVEBUS kind=schedule frame=6091 age=10000 target=10020 pc=A123 port=3 val=02 q=2\n"
            "QA01RF037NATIVEBUS kind=apply frame=6091 age=10010 target=10010 pc=A123 port=2 val=24 q=2\n"
            "QA01RF037NATIVEBUS kind=apply frame=6091 age=10020 target=10020 pc=A123 port=3 val=02 q=1\n"
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=10015 target=10015 pc=A123 port=2 val=24 q=1\n")
        return orig, nat

    def test_full_source_bound_receiver_coverage_is_not_phase_proof(self):
        o, n = self.fixture()
        d = m.analyze(o, n)
        self.assertTrue(d["receiver_coverage_complete"])
        self.assertEqual(d["native_target_local_write_indices_zero_based"], [0, 1])
        self.assertEqual(len(d["native_target_apply"]), 2)
        self.assertEqual(len(d["native_target_vicinity_spc_reads"]), 1)
        self.assertEqual(d["original_spc_recipient_reads_count"], 2)
        self.assertFalse(d["phase_or_bus_order_equivalence_proven"])
        self.assertFalse(d["clock_fix_justified"])
        self.assertEqual(d["complete_usa_events_accepted"], 0)

    def test_missing_receiver_or_schedule_never_passes(self):
        o, n = self.fixture()
        d = m.analyze(o.replace("QA01RF037ORIGSPC", "missing"), n)
        self.assertFalse(d["receiver_coverage_complete"])
        d = m.analyze(o, n.replace("kind=schedule", "kind=missing"))
        self.assertFalse(d["receiver_coverage_complete"])
        self.assertFalse(d["native_schedule_prefix_matches_actual_writers"])

    def test_wrong_native_writer_order_and_truncation_are_rejected(self):
        o, n = self.fixture()
        with self.assertRaisesRegex(ValueError, "target missing"):
            m.analyze(o, n.replace("master=2176886834", "master=0"))
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.analyze(o, n + "QA01RF037NATIVEBUS_TRUNCATED frame=6091\n")
        with self.assertRaisesRegex(ValueError, "no longer consecutive"):
            n2 = n.replace("QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208",
                            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=0 reg=2142 val=00 scope=x\n"
                            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208")
            m.analyze(o, n2)


if __name__ == "__main__":
    unittest.main()

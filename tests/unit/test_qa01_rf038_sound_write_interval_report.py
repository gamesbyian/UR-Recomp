"""RF038 exact source/native writer-interval receipt and no-waiver negative tests."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
import qa01_rf038_sound_write_interval_report as m


class SoundWriterIntervalReport(unittest.TestCase):
    def inputs(self):
        orig = [
            dict(age="100", v="116", h="442", port="2", val="24"),
            dict(age="125", v="116", h="972", port="3", val="02")]
        native = [
            dict(frame="6091", master="2176886834", reg="2142", val="24"),
            dict(frame="6091", master="2176887208", reg="2143", val="02")]
        op = [
            dict(frame="6073", v="116", pre_h="400", post_h="460",
                 pc="82:8301", opcode="8D"),
            dict(frame="6073", v="116", pre_h="950", post_h="990",
                 pc="82:8304", opcode="8D")]
        pace = [
            dict(frame="6091", master="2176886900", charge="8", op="read8"),
            dict(frame="6091", master="2176887100", charge="16", op="read16")]
        return orig, native, op, pace

    def test_real_gap_and_separate_op_pacing_axes(self):
        data = m.inspect(*self.inputs(), ordinal=1)
        self.assertEqual(data["original_minus_native_master"], 156)
        self.assertEqual(data["native_paced_bus_master_charge_between_writes"], 24)
        self.assertEqual(data["native_interval_master_minus_logged_paced_charge"], 350)
        self.assertTrue(data["original_opcode_both_port_clocks_covered"])
        self.assertFalse(data["receiver_read_equivalence_proven"])
        self.assertEqual(data["complete_usa_events_admitted"], 0)

    def test_wrong_source_value_rejected(self):
        o, n, op, pace = self.inputs()
        o[1]["val"] = "03"
        with self.assertRaisesRegex(ValueError, "port value mismatch"):
            m.inspect(o, n, op, pace, ordinal=1)

    def test_truncated_source_or_native_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.inspect(*self.inputs(), ordinal=1,
                      truncated=("QA01RF038ORIGOP_TRUNCATED",))
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.inspect(*self.inputs(), ordinal=1,
                      truncated=("QA01RF038NATIVEPACE_TRUNCATED",))

    def test_missing_opcode_is_not_coverage_or_release(self):
        o, n, op, pace = self.inputs()
        d = m.inspect(o, n, [], pace, ordinal=1)
        self.assertFalse(d["original_opcode_both_port_clocks_covered"])
        self.assertEqual(d["complete_usa_events_admitted"], 0)
        self.assertFalse(d["clock_fix_justified"])

    def test_missing_endpoint_fails(self):
        o, n, op, pace = self.inputs()
        with self.assertRaisesRegex(ValueError, "missing source/native writer"):
            m.inspect(o[:-1], n, op, pace, ordinal=1)
        with self.assertRaisesRegex(ValueError, "missing source/native writer"):
            m.inspect(o, n[:-1], op, pace, ordinal=1)


if __name__ == "__main__":
    unittest.main()

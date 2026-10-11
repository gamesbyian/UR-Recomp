"""Native pinned WRAM consumer instrumentation and independent bounded report."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_stack_read_patch as patcher
import qa01_native_switcher_stack_gate as gate
import qa01_native_nmi_beam_patch as beam
import qa01_native_stack_read_report as report

SRC = (
    'extern Snes *g_snes;\n'
    + gate.STAMP + "\n" + beam.STAMP + "\n"
    + patcher.LOGGER_START + patcher.LOGGER_END
    + patcher.B8 + patcher.B16
)
VALID = (
    "QANATIVEREAD f=5781 bank=00 addr=01DD width=2 value=4004 "
    "A=0000 S=01DC M=0 scope=I_NMI_M1X1\n"
    "QANATIVEREAD f=5782 bank=7E addr=01DE width=1 value=0040 "
    "A=4004 S=01DD M=1 scope=SomeRestore\n"
)


class NativeStackReadTests(unittest.TestCase):
    def test_patches_pinned_native_bus_read_paths_without_changing_return(self):
        x = patcher.patch(SRC)
        self.assertIn(patcher.STAMP, x)
        self.assertIn('getenv("UR_QA_NATIVE_STACK_READ_PATH")', x)
        self.assertIn('width == 1 ? (addr == 0x01DDu || addr == 0x01DEu)', x)
        self.assertIn("ur_qa01_read_01dd(cpu, bank, addr, cpu->ram[off], 1);", x)
        self.assertIn("ur_qa01_read_01dd(cpu, bank, addr,", x)
        self.assertIn("if (ur_qa01_read_suppressed) return;", x)
        self.assertIn("++ur_qa01_read_suppressed;", x)
        self.assertIn("--ur_qa01_read_suppressed;", x)
        self.assertEqual(x.count("return cpu_latch_read8(cpu, cpu->ram[off]);"), 1)
        self.assertEqual(x.count("return cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8));"), 1)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patcher.patch(x)
        with self.assertRaisesRegex(ValueError, "prerequisites"):
            patcher.patch(SRC.replace(beam.STAMP, ""))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patcher.patch(SRC + patcher.B8)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patcher.patch(SRC + patcher.LOGGER_START)

    def test_real_source_scope_is_attempt_not_result_consumer(self):
        data = report.summarize(VALID)
        self.assertEqual(data["native_bus_read_attempt_count"], 2)
        self.assertEqual(data["native_bus_read_attempts_by_target"],
                         {"7E:01DD": 1, "7E:01DE": 2})
        self.assertFalse(data["zero_count_is_bounded_native_negative_not_no_reader_ever"])
        self.assertEqual(data["release_complete_event_credit"], 0)
        self.assertTrue(data["read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer"])
        self.assertEqual(data["native_stack_read_attempts"][0]["read_value"], "4004")

    def test_zero_rows_is_only_bounded_negative(self):
        data = report.summarize("")
        self.assertTrue(data["zero_count_is_bounded_native_negative_not_no_reader_ever"])
        self.assertEqual(data["native_bus_read_attempt_count"], 0)
        self.assertEqual(data["release_complete_event_credit"], 0)

    def test_invalid_bus_scope_or_forged_clock_fails_closed(self):
        for bad in (
            VALID.replace("f=5781", "f=5777", 1),
            VALID.replace("f=5782", "f=5780", 1),
            VALID.replace("bank=00", "bank=7F", 1),
            VALID.replace("addr=01DD", "addr=0200", 1),
            VALID.replace("width=2", "width=3", 1),
            VALID.replace("value=4004", "value=XXXX", 1),
            VALID.replace("value=0040", "value=0140", 1),
            VALID.replace("scope=I_NMI_M1X1", "scope=", 1),
            VALID * (report.LIMIT+1),
            "some garbage row\n",
        ):
            with self.subTest(bad=bad[-100:]), self.assertRaises(ValueError):
                report.summarize(bad)

    def test_workflow_only_enables_in_manual_paired_guest_and_keeps_calibration_isolated(self):
        wf=(ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        host=(ROOT / "tools/probe_original_event_complete.py").read_text()
        self.assertIn("qa01_native_stack_read_patch.py", wf)
        self.assertIn("qa01_native_stack_read_report.py", wf)
        self.assertIn("native-01dd-reads-report.json", wf)
        self.assertIn('UR_QA_NATIVE_STACK_READ_ENABLE: "1"', wf)
        self.assertIn('if os.environ.get("UR_QA_NATIVE_STACK_READ_ENABLE")', host)
        self.assertIn('script.name == "complete.script"', host)
        self.assertIn('str(output / "qa01-native-01dd-reads.log")', host)


if __name__ == "__main__":
    unittest.main()

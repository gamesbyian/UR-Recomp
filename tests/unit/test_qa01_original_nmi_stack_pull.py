"""QA-01 read-only original NMI stack pull probes and fail-closed classification."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import instrument_snesref_qa01_switcher_stack as stack
import qa01_original_nmi_pha_accumulator_patch as pha
import qa01_original_nmi_stack_pull_patch as patcher
import qa01_original_nmi_stack_pull_report as report

ORIGINAL = (
    "QASTACKBEGIN f=5778 v=240 pc=82B1F2 sp=01DE\n"
    "QASTACKNMI f=5778 v=225 pc=828046 sp0=01ED sp1=01E9 addr=01DD old=08 new=08\n"
    "QASTACKNMI f=5779 v=225 pc=80FAD6 sp0=01F5 sp1=01F1 addr=01DD old=08 new=08\n"
    "QASTACKNMI f=5780 v=225 pc=82803A sp0=01E9 sp1=01E5 addr=01DD old=08 new=08\n"
    "QASTACKNMI f=5781 v=225 pc=828036 sp0=01F2 sp1=01EE addr=01DD old=42 new=42\n"
    "QASTACKNMI f=5782 v=225 pc=82807A sp0=01F0 sp1=01EC addr=01DD old=42 new=42\n"
    "QASTACKWRITE f=5780 v=225 pc=00858E op=48 sp0=01DE sp1=01DC addr=01DD old=08 new=42\n"
    "QAPHAREG f=5780 v=225 pc=00858E op=48 sp0=01DE sp1=01DC a0=4042 a1=4042 pl0=00 pl1=00 m0=0 m1=0 dd0=08 dd1=42 de0=00 de1=40 f1=5780\n"
)
# This is a SYNTHETIC pull test fixture. The asserted real source trace
# establishes PHA only; there has been no executed return-path trace.
PULL = (
    "QANMIPULL f=5780 v=225 pc=0085A0 op=68 "
    "sp0=01DC sp1=01DE width=2 pl0=00 pl1=00 "
    "a0=0000 a1=4042 dd=42 de=40 "
    "touches_dd=1 touches_de=1 f1=5780\n"
)


class SwitcherNmiStackPullTests(unittest.TestCase):
    def test_patch_preserves_one_original_instruction_and_is_read_only(self):
        source = "head\n" + stack.NMI_MARKER + "\n" + stack.MARKER + "\ntail"
        observed = stack.patch(source, targets=(0x01DD,), watch_nmi=True)
        observed = pha.patch(observed)
        patched = patcher.patch(observed)
        self.assertEqual(patched.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(patched.count("S9xOpcode_NMI();"), 1)
        self.assertEqual(patched.count("Registers.PCw++;"), 1)
        self.assertIn(patcher.STAMP, patched)
        self.assertIn("QANMIPULL f=", patched)
        self.assertIn("ur_qa_stack_gate", patched)
        self.assertIn("ur_qa_pull_sp0 + ur_qa_pull_width", patched)
        self.assertIn("case 0x68:", patched)
        self.assertIn("case 0x2B:", patched)
        self.assertIn("case 0x28:", patched)
        self.assertIn("Memory.RAM[0x01DD]", patched)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patcher.patch(patched)
        with self.assertRaisesRegex(ValueError, "require prior"):
            patcher.patch(source)
        with self.assertRaisesRegex(ValueError, "marker missing"):
            patcher.patch(observed.replace(stack.MARKER, stack.MARKER * 2))

    def test_positive_synthetic_architectural_pull_retains_no_event_credit(self):
        result = report.summarize(ORIGINAL + PULL)
        self.assertEqual(result["schema"], report.SCHEMA)
        self.assertEqual(result["original_nmi_hardware_entries"], 5)
        self.assertEqual(result["observed_candidate_stack_pull_count"], 1)
        self.assertEqual(result["release_complete_event_credit"], 0)
        self.assertFalse(result["original_native_result_guest_relative_parity"])
        self.assertFalse(result["zero_count_is_bounded_negative_only"])
        pull = result["candidate_stack_pull_scopes"][0]
        self.assertEqual(pull["stack_pointer_before"], "01DC")
        self.assertEqual(pull["stack_pointer_after"], "01DE")
        self.assertEqual(pull["architectural_stack_pull_bytes"], 2)
        self.assertTrue(pull["architecturally_touches_01dd"])
        self.assertTrue(pull["architecturally_touches_01de"])
        self.assertEqual(pull["observed_01dd_byte_before"], "42")
        self.assertEqual(pull["observed_01de_byte_before"], "40")

    def test_bounded_zero_read_witness_does_not_claim_no_consumers(self):
        result = report.summarize(ORIGINAL)
        self.assertEqual(result["observed_candidate_stack_pull_count"], 0)
        self.assertTrue(result["zero_count_is_bounded_negative_only"])
        self.assertTrue(result["stack_reads_outside_named_pulls_not_excluded"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_valid_pull_widths_respect_original_p_status(self):
        self.assertEqual(report.expected_pull_width(0x68, 0), 2)
        self.assertEqual(report.expected_pull_width(0x68, 0x20), 1)
        self.assertEqual(report.expected_pull_width(0xFA, 0), 2)
        self.assertEqual(report.expected_pull_width(0x7A, 0x10), 1)
        self.assertEqual(report.expected_pull_width(0x2B, 0x30), 2)
        self.assertEqual(report.expected_pull_width(0xAB, 0), 1)
        self.assertEqual(report.expected_pull_width(0x28, 0), 1)
        with self.assertRaises(ValueError):
            report.expected_pull_width(0x48, 0)

    def test_malformed_or_forged_original_nmi_reads_fail_closed(self):
        for log in (
            PULL,  # Not a real original source replay.
            ORIGINAL.replace("QASTACKWRITE ", "QASTACKWROTE ") + PULL,
            ORIGINAL + PULL.replace("width=2", "width=1"),
            ORIGINAL + PULL.replace("sp1=01DE", "sp1=01DD"),
            ORIGINAL + PULL.replace("sp0=01DC", "sp0=01DF"),
            ORIGINAL + PULL.replace("touches_dd=1", "touches_dd=0"),
            ORIGINAL + PULL.replace("touches_de=1", "touches_de=0"),
            ORIGINAL + PULL.replace("pl0=00", "pl0=20"),
            ORIGINAL + PULL.replace("op=68", "op=48"),
            ORIGINAL + PULL.replace("f=5780", "f=5760"),
            ORIGINAL + PULL.replace("f1=5780", "f1=5784"),
            ORIGINAL + PULL.replace("v=225", "v=300"),
            ORIGINAL + PULL.replace("width=2", "width=bogus"),
            ORIGINAL + PULL * (report.MAX_PULLS + 1),
            ORIGINAL + PULL.replace("f=5780", "f=5781", 1) + PULL,
        ):
            with self.subTest(rejected_trace=log[-150:]):
                with self.assertRaises(ValueError):
                    report.summarize(log)


if __name__ == "__main__":
    unittest.main()

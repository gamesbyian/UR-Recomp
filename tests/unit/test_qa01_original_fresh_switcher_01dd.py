"""Narrow original Snes9x real Switcher 01DD opcode writer probes."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import instrument_snesref_qa01_switcher_stack as instrument
import qa01_original_fresh_switcher_01dd_report as qa

BEGIN="QASTACKBEGIN f=5778 v=240 pc=82B1F2 sp=01DE\n"
WRITE="QASTACKWRITE f=5781 v=240 pc=82B1F2 op=20 sp0=01DE sp1=01DC addr=01DD old=00 new=F4\n"

class FreshOriginal01DDTests(unittest.TestCase):
    def test_single_target_preserves_unchanged_default_and_unique_source_marker(self):
        synthetic="prefix\n"+instrument.MARKER+"\nsuffix"
        p=instrument.patch(synthetic,targets=(0x01DD,))
        self.assertEqual(p.count("0x01DD"),1)
        self.assertNotIn("0x01E6",p)
        self.assertEqual(p.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(p.count("Registers.PCw++;"),1)
        self.assertIn("UR_QA_STACK_FIRST",p)
        self.assertIn("UR_QA_STACK_LAST",p)
        q=instrument.patch(synthetic)
        self.assertIn("0x01E6",q)
        self.assertIn("0x01F3",q)
        for bad in ((),(0x01DD,0x01DD),(0x0200,),(-1,)):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,"unique approved stack address"):
                    instrument.patch(synthetic,targets=bad)

    def test_original_pc_sp_and_frame_event_do_not_claim_parity(self):
        s=qa.summarize_original(BEGIN+WRITE)
        self.assertEqual(s["schema"],qa.SCHEMA)
        self.assertEqual(s["total_original_changed_byte_opcode_scopes"],1)
        self.assertEqual(s["original_changed_byte_scopes_by_cpu_frame"],{5781:1})
        self.assertEqual(s["original_changed_byte_scopes_by_pc"],{"82:B1F2":1})
        self.assertEqual(s["original_changed_byte_scopes_by_opcode"],{"20":1})
        self.assertEqual(s["cpu_gate_pc"],"82:B1F2")
        self.assertTrue(s["first_bounded_original_opcode_scope_examples"][0]
                        ["push_opcode_and_stack_address_compatible"])
        self.assertEqual(s["complete_event_release_credit"],0)

    def test_zero_changed_byte_is_valid_bounded_negative_with_real_gate(self):
        s=qa.summarize_original(BEGIN)
        self.assertEqual(s["total_original_changed_byte_opcode_scopes"],0)
        self.assertTrue(s["zero_changes_is_bounded_negative_not_never_writes"])
        self.assertEqual(s["original_changed_byte_scopes_by_pc"],{})

    def test_strict_negative_wrong_frame_address_or_duplicate_gate(self):
        for trace in (
            "",
            BEGIN+BEGIN,
            BEGIN.replace("f=5778","f=5000"),
            BEGIN.replace("v=240","v=270"),
            BEGIN+WRITE.replace("addr=01DD","addr=01F1"),
            BEGIN+WRITE.replace("f=5781","f=5783"),
            BEGIN+WRITE.replace("old=00 new=F4","old=F4 new=F4"),
            BEGIN+WRITE.replace("f=5781","f=5777"),
        ):
            with self.subTest(trace=trace[:55]):
                with self.assertRaises(ValueError):
                    qa.summarize_original(trace)
        with self.assertRaisesRegex(ValueError,"safe limit"):
            from unittest.mock import patch
            with patch.object(qa,"MAX_WRITES",2):
                qa.summarize_original(BEGIN+WRITE*3)

if __name__=="__main__":
    unittest.main()

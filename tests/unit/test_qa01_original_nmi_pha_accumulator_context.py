"""QA-01 original I_NMI PHA real accumulator read-only scope and authenticity."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import instrument_snesref_qa01_switcher_stack as old
import qa01_original_nmi_pha_accumulator_patch as patcher
import qa01_original_nmi_pha_accumulator_report as report

BEGIN="QASTACKBEGIN f=5778 v=240 pc=82B1F2 sp=01DE\n"
NMI=(
"QASTACKNMI f=5778 v=225 pc=828046 sp0=01ED sp1=01E9 addr=01DD old=08 new=08\n"
"QASTACKNMI f=5779 v=225 pc=80FAD6 sp0=01F5 sp1=01F1 addr=01DD old=08 new=08\n"
"QASTACKNMI f=5780 v=225 pc=82803A sp0=01E9 sp1=01E5 addr=01DD old=08 new=08\n"
"QASTACKNMI f=5781 v=225 pc=828036 sp0=01F2 sp1=01EE addr=01DD old=42 new=42\n"
"QASTACKNMI f=5782 v=225 pc=82807A sp0=01F0 sp1=01EC addr=01DD old=42 new=42\n"
)
WRITE="QASTACKWRITE f=5780 v=225 pc=00858E op=48 sp0=01DE sp1=01DC addr=01DD old=08 new=42\n"
PHA="QAPHAREG f=5780 v=225 pc=00858E op=48 sp0=01DE sp1=01DC a0=4042 a1=4042 pl0=00 pl1=00 m0=0 m1=0 dd0=08 dd1=42 de0=00 de1=40 f1=5780\n"

class OriginalNmiPhaAccumulatorContextTests(unittest.TestCase):
    def test_disposable_core_patch_only_inserts_read_only_register_observation(self):
        base="head\n"+old.NMI_MARKER+"\n"+old.MARKER+"\ntail"
        observed=old.patch(base,targets=(0x01DD,),watch_nmi=True)
        patched=patcher.patch(observed)
        self.assertEqual(patched.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(patched.count("S9xOpcode_NMI();"),1)
        self.assertEqual(patched.count("Registers.PCw++;"),1)
        self.assertIn(patcher.STAMP,patched)
        self.assertIn("Registers.A.W",patched)
        self.assertIn("Registers.PL",patched)
        self.assertIn("Memory.RAM[0x01DD]",patched)
        self.assertIn("Memory.RAM[0x01DE]",patched)
        self.assertIn("(Op == 0x48)",patched)
        self.assertIn("0x858Eu",patched)
        self.assertIn("ur_qa_stack_gate",patched)
        with self.assertRaisesRegex(ValueError,"already installed"):
            patcher.patch(patched)
        with self.assertRaisesRegex(ValueError,"only valid after"):
            patcher.patch(base)
        with self.assertRaisesRegex(ValueError,"not unique"):
            patcher.patch(observed.replace(patcher.MARKER,patcher.MARKER*2))

    def test_true_original_pha_register_matches_original_stack_word(self):
        d=report.summarize(BEGIN+NMI+WRITE+PHA)
        self.assertEqual(d["schema"],report.SCHEMA)
        self.assertEqual(d["complete_event_release_credit"],0)
        self.assertEqual(len(d["original_nmi_hardware_entry_events"]),5)
        self.assertEqual(len(d["all_bounded_original_I_NMI_pha_register_scopes"]),1)
        x=d["confirmed_original_01dd_pha_register_scope"]
        self.assertEqual(x["original_cpu_frame_before"],5780)
        self.assertEqual(x["original_instruction_pc"],"00:858E")
        self.assertEqual(x["stack_pointer_before"],"01DE")
        self.assertEqual(x["stack_pointer_after"],"01DC")
        self.assertEqual(x["accumulator_before"],"4042")
        self.assertEqual(x["accumulator_after"],"4042")
        self.assertEqual(x["memory_width_flag_before"],0)
        self.assertEqual(x["memory_width_flag_after"],0)
        self.assertTrue(x["low_byte_matches_accumulator"])
        self.assertEqual(x["01dd_after"],"42")
        self.assertEqual(x["01de_after"],"40")
        self.assertTrue(d["original_cpu_vs_native_writer_frame_clocks_unaligned"])

    def test_fail_closed_missing_pha_changed_byte_reg_or_wrong_status(self):
        good=BEGIN+NMI+WRITE
        cases=[
            good,
            good+PHA.replace("a0=4042","a0=4004"),
            good+PHA.replace("a1=4042","a1=4004"),
            good+PHA.replace("m0=0","m0=1"),
            good+PHA.replace("m1=0","m1=1"),
            good+PHA.replace("pl1=00","pl1=20"),
            good+PHA.replace("op=48","op=20"),
            good+PHA.replace("pc=00858E","pc=00858F"),
            good+PHA.replace("f=5780","f=5760"),
            good+PHA.replace("sp1=01DC","sp1=01DD"),
            good+PHA.replace("dd1=42","dd1=04"),
            good+PHA.replace("de1=40","de1=41"),
            BEGIN+NMI+PHA,
        ]
        for t in cases:
            with self.subTest(mutation=t[-115:]):
                with self.assertRaises(ValueError):
                    report.summarize(t)

if __name__=="__main__":
    unittest.main()

"""QA-01 original Snes9x collision-PC observer and strict branch receipt tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import instrument_snesref_2p_air_writes as base
import instrument_snesref_2p_collision_gate as injector
import qa01_dual_air_collision_branch_report as report


def source_line(frame=2579, v=80, pc="81925A", nxt="81925C",
                contact="FF", seat="0000", state="0000"):
    return (
        f"QA01COLLBR pre_f={frame} post_f={frame} pre_v={v} post_v={v} "
        f"pc={pc} next={nxt} contact={contact}/{contact} "
        f"state={state}/{state} seat={seat}/{seat} "
        "y=0359/0359 vy=0000/0000\n"
    )


class BoundedOriginalCollisionGate(unittest.TestCase):
    def test_existing_original_cpu_opcode_executes_only_once(self):
        src = base.patch("prefix\n" + base.MARKER + "\nsuffix")
        patched = injector.patch(src)
        self.assertEqual(patched.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(patched.count("Registers.PCw++;"), 1)
        self.assertIn(injector.STAMP, patched)
        self.assertIn(base.STAMP, patched)
        self.assertIn("QA01COLLBR pre_f=", patched)
        for literal in ("0x819253", "0x819255", "0x819258", "0x81925A",
                        "0x81925F", "0x819262", "0x819263", "0x819266",
                        "0x819268", "Memory.RAM[0x02C0]",
                        "Memory.RAM[0x0F29]", "Memory.RAM[0x0FEF]",
                        "Memory.RAM[0x0FA1]", "Memory.RAM[0x00A7]"):
            self.assertIn(literal, patched)
        self.assertNotIn("Memory.RAM[0x02C0] =", patched)
        self.assertNotIn("Memory.RAM[0x0F29] =", patched)
        self.assertNotIn("ICPU.Frame =", patched)
        self.assertNotIn("Registers.PCw =", patched)
        with self.assertRaisesRegex(ValueError, "already installed"):
            injector.patch(patched)
        with self.assertRaisesRegex(ValueError, "must be installed first"):
            injector.patch("prefix\n" + base.MARKER + "\nsuffix")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            injector.patch(src.replace(
                "            Registers.PCw++;\n"
                "            (*Opcodes[Op].S9xOpcode)();\n"
                "            if (ur_qa_air_gate)\n", "bogus state\n"))

    def test_original_bpl_reports_actual_next_pc_with_seat_and_clock_unmerged(self):
        original = "".join((
            source_line(v=50, pc="819255", nxt="819258",
                        contact="FF", seat="0000"),
            source_line(v=52, pc="81925A", nxt="81925C",
                        contact="FF", seat="0000"),
            source_line(v=105, pc="81925A", nxt="81926E",
                        contact="00", seat="0002", state="0001"),
            source_line(v=108, pc="819266", nxt="819268",
                        contact="00", seat="0002", state="0001"),
            source_line(v=109, pc="819268", nxt="81926B",
                        contact="00", seat="0002", state="0001"),
        ))
        rows = report.classify(original)
        self.assertEqual(rows["schema"], report.SCHEMA)
        self.assertEqual(rows["observed_bpl_seats"], [0, 2])
        self.assertEqual(len(rows["original_cpu_scopes"]), 5)
        self.assertEqual(rows["original_cpu_scopes"][1]["branch_result"],
                         "fallthrough_on_negative")
        self.assertEqual(rows["original_cpu_scopes"][2]["branch_result"],
                         "taken_on_nonnegative")
        self.assertEqual(rows["original_cpu_scopes"][3]["branch_result"],
                         "fallthrough_to_store")
        self.assertTrue(rows["preserved_original_cpu_pre_post_frame_and_scanline"])
        self.assertFalse(rows["native_helper_PC_or_beam_alignment_proven"])
        self.assertFalse(rows["full_original_native_gameplay_causality_proven"])
        self.assertEqual(rows["strict_complete_usa_release_credit"], 0)

    def test_genuine_original_sign_gate_falsifies_opposite_branch(self):
        for before,pc,nxt,error in (
            (source_line(contact="FF", nxt="81926E"),"","", "sign"),
            (source_line(contact="00", nxt="81925C"),"","", "sign"),
            (source_line(nxt="819268"),"","", "next-PC"),
            (source_line(pc="81926A"),"","", "outside"),
            (source_line(frame=2588),"","", "frame"),
            (source_line(seat="0001"),"","", "scratch/seat"),
            (source_line().replace("state=0000/0000", "state=0000/0001"),"","", "scratch/seat"),
            (source_line().replace("contact=FF/FF", "contact=FF/00"),"","", "scratch/seat"),
            (source_line().replace("pre_f=2579", "pre_f=XX"),"","", "malformed"),
        ):
            with self.subTest(line=before):
                with self.assertRaisesRegex(ValueError, error):
                    report.classify(before)

    def test_refuses_unbounded_malformed_or_reordered_capture(self):
        a = source_line(v=100) + source_line(v=70)
        with self.assertRaisesRegex(ValueError, "chronology"):
            report.classify(a)
        with self.assertRaisesRegex(ValueError, "no bounded"):
            report.classify("no executing original collision branch\n")
        with self.assertRaisesRegex(ValueError, "budget"):
            report.classify(source_line() * (report.MAX_SCOPE + 1))
        with self.assertRaisesRegex(ValueError, "malformed"):
            report.classify(source_line() + "QA01COLLBR forged\n")


if __name__ == "__main__":
    unittest.main()

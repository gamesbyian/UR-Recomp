import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_io_access_clock_order_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 recompiler/v2/emit_function.py regions
# (unchanged at upstream ec8a3e7), joined by filler lines.
PINNED_HELPER_HEAD = '''def _block_speed(bank: int, pc: int):
    """Code-region cycle weighting, using live PBR for mirrored bodies."""
    from v2.emitter_helpers import runtime_code_speed
'''
PINNED_LOOP = '''        for ii, (di_insn, ir_ops) in enumerate(pairs):
            # NLR: inject _pending_skip setter + diagnostics RIGHT BEFORE
            # the terminator insn. This ensures any preceding setup ops
'''
PINNED_CHARGE = '''        if _cyc_const:
            src.append(f'    cpu->cycles += {_cyc_const};')
            _spd_expr, _spd_const = _block_speed(bank, key.pc)
            if _widths.PACED_BUS:
                _fetch = sum(int(p[0].length) for p in block_per_insn_ir.get(key, []))
                src.append('    cpu->master_cycles += ' + _paced_block_master(
                    _cyc_const, _fetch, _data_bytes, _spd_expr, _spd_const) + ';')
            elif _spd_const is not None:
                src.append(f'    cpu->master_cycles += {_cyc_const * _spd_const};')
            else:
                src.append(f'    cpu->master_cycles += {_cyc_const} * {_spd_expr};')
        for ln in block_lines[key]:
            # Inject a stack-auditor pop before any return so the shadow
'''
PINNED = "\n# ...\n".join((PINNED_HELPER_HEAD, PINNED_LOOP, PINNED_CHARGE))

# The pinned emitter's paced-accessor regex (emit_function.py:87).
PACED_RE = re.compile(r"\bcpu_(?:read|write)(8|16)_paced\(")
SPEED = "((g_memsel && (cpu->PB & 0x80)) ? 6 : 8)"
# Static 65816 cycles for the opcodes used below (ADC long,X with 16-bit A).
STATIC_CYCLES = {0xAD: 4, 0x10: 2, 0x18: 2, 0x7F: 6, 0xE8: 2}


def helper_namespace():
    """Execute the staged helper exactly as the patched emitter defines it."""
    ns = {"re": re, "_PACED_RE": PACED_RE,
          "block_static_cycles": lambda items: (
              sum(STATIC_CYCLES[op] for op, _m, _x in items), [])}
    exec(fix.HELPER, ns)
    return ns


def insn(opcode, length):
    return (SimpleNamespace(opcode=opcode, length=length, m_flag=1, x_flag=1), [])


def marked(segments):
    lines = []
    for i, seg in enumerate(segments):
        lines.append(f"/*@@UR_INSN {i}@@*/")
        lines.extend(seg)
    return lines


class StageTest(unittest.TestCase):
    def test_stages_all_three_edits_once_and_is_idempotent(self):
        once = fix.patch(PINNED)
        self.assertEqual(once.count(fix.MARK), 3)
        self.assertIn('lines.append(f"/*@@UR_INSN {ii}@@*/")', once)
        self.assertIn("_io_charges = _io_ordered_charges(", once)
        self.assertIn("def _io_ordered_charges(", once)
        self.assertEqual(fix.patch(once), once)

    def test_rejects_unknown_revision(self):
        drifted = PINNED.replace("_paced_block_master(\n", "_paced_master(\n")
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch(drifted)

    def test_rejects_altered_marker(self):
        once = fix.patch(PINNED)
        tampered = once.replace("in-order: register access", "reordered", 1)
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch(tampered)


class ChargeOrderTest(unittest.TestCase):
    def setUp(self):
        self.charges = helper_namespace()["_io_ordered_charges"]

    def test_rf017_vblank_poll_reads_before_the_branch_fetches(self):
        # 80:FAD6 LDA $4212 / BPL $FAD2: the pinned lump charged 5 fetches
        # (40 clocks at SlowROM) before the read; hardware reads after 3.
        pairs = [insn(0xAD, 3), insn(0x10, 2)]
        lines = marked([
            ["uint8 _v2 = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x4212));"],
            ["if (cpu->_flag_N == 0) { goto L_FAD2_M1X0; }"],
        ])
        got = self.charges(pairs, lines, SPEED, None)
        self.assertTrue(got[0].startswith(f"cpu->master_cycles += 3 * {SPEED} + 0;"))
        self.assertTrue(got[1].startswith(f"cpu->master_cycles += 2 * {SPEED} + 0;"))
        # Constant-speed bodies keep the same split at SlowROM's 8 clocks.
        const = self.charges(pairs, lines, None, 8)
        self.assertTrue(const[0].startswith("cpu->master_cycles += 24;"))
        self.assertTrue(const[1].startswith("cpu->master_cycles += 16;"))

    def test_split_preserves_the_block_total(self):
        # CLC / ADC $77000C,X / INX: SRAM data bytes stay with the accessor;
        # the static fetch + internal clocks sum to the pinned lump.
        pairs = [insn(0x18, 1), insn(0x7F, 4), insn(0xE8, 1), insn(0xAD, 3)]
        lines = marked([
            ["cpu->_flag_C = 0;"],
            ["uint16 _v4 = cpu_read16_paced(cpu, (uint8)(0x77), (uint16)(0x000c));"],
            ["cpu->X = (uint16)(cpu->X + 1);"],
            ["uint8 _v5 = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x2137));"],
        ])
        got = self.charges(pairs, lines, None, 8)
        total = sum(int(re.search(r"\+= (\d+);", s).group(1)) for s in got.values())
        cycles = sum(STATIC_CYCLES[p[0].opcode] for p in pairs)
        fetch = sum(p[0].length for p in pairs)
        data = 3  # two SRAM bytes and one $2137 byte, charged by their accessors
        self.assertEqual(total, fetch * 8 + (cycles - fetch - data) * 6)

    def test_blocks_without_register_access_keep_the_lump(self):
        pairs = [insn(0x18, 1), insn(0x7F, 4)]
        lines = marked([
            ["cpu->_flag_C = 0;"],
            ["uint16 _v4 = cpu_read16_paced(cpu, (uint8)(0x77), (uint16)(0x000c));"],
        ])
        self.assertIsNone(self.charges(pairs, lines, SPEED, None))

    def test_unreproducible_split_keeps_the_lump(self):
        # More paced bytes than the instruction's static cycles allow.
        pairs = [insn(0xAD, 3)]
        lines = marked([[
            "uint16 _a = cpu_read16_paced(cpu, cpu->DB, (uint16)(0x4212));",
            "uint16 _b = cpu_read16_paced(cpu, cpu->DB, (uint16)(0x4214));",
        ]])
        self.assertIsNone(self.charges(pairs, lines, SPEED, None))

    def test_unmarked_segments_keep_the_lump(self):
        pairs = [insn(0xAD, 3), insn(0x10, 2)]
        lines = marked([["uint8 _v = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x4212));"]])
        self.assertIsNone(self.charges(pairs, lines, SPEED, None))


PINNED_GEN = """RecompReturn Wait_M1X0(CpuState *cpu) {
  L_FAD6_M1X0:
    cpu_trace_block(cpu, 0x80FAD6);
    cpu->cycles += 6;
    cpu->master_cycles += 5 * ((g_memsel && (cpu->PB & 0x80)) ? 6 : 8) + 0;
    uint8 _v2 = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x4212));
    if (cpu->_flag_N == 0) { cpu->cycles += 1; cpu->master_cycles += 6; goto L_FAD2_M1X0; }
"""
CORRECTED_GEN = PINNED_GEN.replace(
    "    cpu->master_cycles += 5 * ((g_memsel && (cpu->PB & 0x80)) ? 6 : 8) + 0;\n"
    "    uint8 _v2 = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x4212));\n",
    "    cpu->master_cycles += 3 * ((g_memsel && (cpu->PB & 0x80)) ? 6 : 8) + 0;  "
    "/* in-order: register access sees prior bus cycles */\n"
    "    uint8 _v2 = cpu_read8_paced(cpu, cpu->DB, (uint16)(0x4212));\n"
    "    cpu->master_cycles += 2 * ((g_memsel && (cpu->PB & 0x80)) ? 6 : 8) + 0;  "
    "/* in-order: register access sees prior bus cycles */\n")


class VerifyGeneratedTest(unittest.TestCase):
    def test_accepts_a_reordered_block_with_the_same_total(self):
        self.assertNotEqual(PINNED_GEN, CORRECTED_GEN)
        self.assertEqual(fix.verify_generated(PINNED_GEN, CORRECTED_GEN), 2)
        self.assertEqual(fix.verify_generated(PINNED_GEN, PINNED_GEN), 0)

    def test_rejects_a_changed_block_total(self):
        bad = CORRECTED_GEN.replace("+= 2 * ", "+= 1 * ", 1)
        with self.assertRaisesRegex(ValueError, "total changed"):
            fix.verify_generated(PINNED_GEN, bad)

    def test_rejects_any_other_generated_change(self):
        bad = CORRECTED_GEN.replace("(uint16)(0x4212)", "(uint16)(0x4210)")
        with self.assertRaisesRegex(ValueError, "beyond static clock charges"):
            fix.verify_generated(PINNED_GEN, bad)


if __name__ == "__main__":
    unittest.main()

"""RF047 executed guest-PC source staging, with false-positive safeguards."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf047_executed_guest_pc_witness as pc


class ExecutedPC(unittest.TestCase):
    def fixture(self):
        beam = (
            "/* UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN */\n"
            "static int ur_rf047_allow_row(void) { return 1; }\n"
            "static void ur_rf047_nmi_snapshot(const char *stage, uint32_t vector) {\n"
        )
        emitter = (
            "def emit_function():\n"
            "    src.append(f'  extern const char *g_last_recomp_func;')\n"
            "    for ii, (di_insn, ir_ops) in enumerate(pairs):\n"
            "            if ii in skip_emit_idx:\n"
            "                continue\n"
            "            # Axis-2 step C dynamics: charge runtime-only modifiers (D.l != 0,\n"
            "            for op in ir_ops:\n"
            "                lines.append('real instruction effect')\n"
        )
        bridge = (
            "extern Snes *g_snes;\n"
            "        const uint8_t  op = bridge_bus_read(cpu, pc_before);\n"
        )
        return beam, emitter, bridge

    def test_pins_actual_source_insn_not_static_function_name(self):
        b, e, i = pc.patch(*self.fixture())
        self.assertEqual(b.count(pc.STAMP), 1)
        self.assertEqual(e.count("ur_rf047_mark_executed_pc"), 2)
        self.assertEqual(i.count("ur_rf047_mark_executed_pc"), 2)
        self.assertIn("di_insn.addr & 0xFFFFFF", e)
        self.assertIn("0x8282F0", e)
        self.assertIn("0x82D4F0", e)
        self.assertLess(e.index("if ii in skip_emit_idx"),
                        e.index("ur_rf047_mark_executed_pc"))
        self.assertLess(e.index("ur_rf047_mark_executed_pc(0x{di_insn.addr"),
                        e.index("for op in ir_ops:"))
        self.assertIn("const uint8_t  op = bridge_bus_read(cpu, pc_before);\n"
                      "        ur_rf047_mark_executed_pc(pc_before, 0u);", i)
        self.assertIn('stage=opcode', b)
        self.assertIn('QA01RF047NATIVEPC_TRUNCATED', b)
        self.assertIn('hi-lo > 16', b)
        self.assertNotIn("g_interp816_cur_pc", b + e + i)

    def test_missing_or_second_marker_fail_closed(self):
        b, e, i = self.fixture()
        with self.assertRaisesRegex(ValueError, "base native recorder"):
            pc.patch(b.replace("UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN", ""), e, i)
        with self.assertRaisesRegex(ValueError, "source drift"):
            pc.patch(b, e.replace("if ii in skip_emit_idx", "if ii in nonexist"), i.replace(
                pc.INTERP_SITE, "        const uint8_t op = 0;\n"))
        x = pc.patch(b, e, i)
        with self.assertRaisesRegex(ValueError, "partially staged"):
            pc.patch(*x)

    def test_guest_observer_does_not_fake_bus_read_or_clock_sync(self):
        b, e, i = pc.patch(*self.fixture())
        self.assertNotIn("cpu_read8(", pc.BEAM_HOOK)
        self.assertNotIn("cpu_write8(", pc.BEAM_HOOK)
        self.assertNotIn("master_cycles =", pc.BEAM_HOOK)
        self.assertNotIn("Register", pc.BEAM_HOOK)
        self.assertIn("late_seq", b)
        self.assertIn("ur_rf047_seq", b)


if __name__ == "__main__":
    unittest.main()

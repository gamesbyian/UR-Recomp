"""RF088 synthetic source guards; not a compiled or executed Zoo result."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf088_native_apu_echo_window as rf088


def fixture():
    return "\n".join((
        rf088.ENTRY,
        "    if (is_hw_reg(bank, addr)) {",
        rf088.READ8,
        "    }",
        "}",
        "uint16 cpu_read16(CpuState *cpu, uint8 bank, uint16 addr) {",
        rf088.READ16,
        "}",
        "void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 v) {",
        rf088.WRITE8,
        "}",
        "void cpu_write16(CpuState *cpu, uint8 bank, uint16 addr, uint16 v) {",
        rf088.WRITE16,
        "}",
    ))


class EchoWindowTests(unittest.TestCase):
    def test_four_post_io_hooks_preserve_actual_bus_call_population(self):
        original = fixture()
        patched = rf088.patch(original)
        self.assertEqual(patched.count(rf088.STAMP), 1)
        self.assertEqual(patched.count("ur_rf088_note(cpu,"), 4)
        for name in ("ReadRegOpenBus(", "ReadRegWord(", "WriteReg(",
                     "WriteRegWord(", "cpu_pace_cycles(",
                     "cpu_pace_cycles_word("):
            self.assertEqual(original.count(name), patched.count(name), name)
        self.assertLess(patched.index("ReadRegOpenBus(addr, cpu->open_bus);"),
                        patched.index("ur_rf088_note(cpu, bank, addr, 1u, ur_rf088_value, 'R');"))
        self.assertLess(patched.index("WriteRegWord(addr, v);"),
                        patched.index("ur_rf088_note(cpu, bank, addr, 2u, v, 'W');"))
        # The failed first combined case had zero RF088 rows. Do not
        # preselect an assumed pointer phase before measuring real reads.
        self.assertIn("snes_frame_counter >= 6055 && snes_frame_counter <= 6060", patched)
        self.assertIn("snes_frame_counter >= 6447 && snes_frame_counter <= 6451", patched)
        self.assertIn("!((snes_frame_counter >= 6055", patched)
        self.assertNotIn("cpu->ram[0x63] != 0xB0", patched)
        self.assertNotIn("cpu->ram[0x64] != 0xC6", patched)
        self.assertIn("ptr=%02X%02X", patched)
        self.assertIn("addr < 0x2140 || addr > 0x2143", patched)
        self.assertNotIn("addr != 0x2142 && addr != 0x2143", patched)
        self.assertIn("(unsigned)cpu->ram[0x64], (unsigned)cpu->ram[0x63]", patched)
        self.assertIn("QA01RF088NATIVE_TRUNCATED", patched)
        self.assertIn("UR_QA01_RF088_NATIVE_APU_ECHO", patched)

    def test_reapplication_and_source_drift_fail_closed(self):
        source = fixture()
        with self.assertRaisesRegex(ValueError, "already or partially"):
            rf088.patch(rf088.patch(source))
        for anchor in (rf088.ENTRY, rf088.READ8, rf088.READ16,
                       rf088.WRITE8, rf088.WRITE16):
            with self.subTest(anchor=anchor[:30]), self.assertRaisesRegex(
                    ValueError, "missing or ambiguous"):
                rf088.patch(source.replace(anchor, "SOURCE_DRIFT", 1))

    def test_actual_pinned_submodule_if_checked_out(self):
        path = Path(__file__).resolve().parents[2] / "baldosa" / rf088.FILE
        if path.is_file():
            self.assertIn(rf088.STAMP, rf088.patch(path.read_text()))


if __name__ == "__main__":
    unittest.main()

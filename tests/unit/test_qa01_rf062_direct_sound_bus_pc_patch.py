"""RF062 direct decoded-PC sound ROM reader: ROM-free execution-site tests."""
from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf062_direct_sound_bus_pc_patch as rf


class DirectSoundRead(unittest.TestCase):
    def fixture(self):
        gen = (
            "_CURRENT_SOURCE_PC24 = 0\n"
            "def _emit_read(op: Read) -> List[str]:\n"
            "    bank, addr = _segref_addr_expr(op.seg)\n"
            '    return [f"{widths.ctype(op.width)} {_v(op.out)} = "\n'
            '            f"{widths.read_fn(op.width)}(cpu, {bank}, {addr});"]\n')
        cpu = (
            "uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n"
            "    cpu->master_cycles += cpu_region_speed(((uint32_t)bank << 16) | addr);\n"
            "    return cpu_read8(cpu, bank, addr);\n"
            "}\n")
        header = "uint8  cpu_read8_paced (CpuState *cpu, uint8 bank, uint16 addr);\n"
        return gen, cpu, header

    def test_actual_codegen_emission_follows_decoded_pc_and_width(self):
        gen, cpu, header = rf.patch(*self.fixture())
        namespace = {
            "Read": object,
            "List": List,
            "_segref_addr_expr": lambda seg: ("0x11", "0xC774"),
            "_v": lambda out: "v",
            "widths": SimpleNamespace(
                ctype=lambda width: "uint8" if width == 1 else "uint16",
                read_fn=lambda width: "cpu_read8_paced" if width == 1 else "cpu_read16_paced"),
        }
        exec(gen, namespace)
        read = SimpleNamespace(width=1, out=1, seg=None)
        namespace["_CURRENT_SOURCE_PC24"] = 0x8282F0
        live = namespace["_emit_read"](read)
        self.assertEqual(live, ["uint8 v = ur_rf062_cpu_read8_pc(cpu, 0x11, 0xC774, 0x8282F0u);"])
        namespace["_CURRENT_SOURCE_PC24"] = 0x8282F2
        self.assertIn("cpu_read8_paced(cpu, 0x11, 0xC774)",
                      namespace["_emit_read"](read)[0])
        namespace["_CURRENT_SOURCE_PC24"] = 0x8282F0
        self.assertIn("cpu_read16_paced", namespace["_emit_read"](
            SimpleNamespace(width=2, out=1, seg=None))[0])
        self.assertEqual(cpu.count("uint8 value = cpu_read8_paced(cpu, bank, addr);"), 1)
        self.assertEqual(gen.count("ur_rf062_cpu_read8_pc(cpu,"), 1)
        self.assertIn("uint8 ur_rf062_cpu_read8_pc(", header)
        self.assertNotIn("g_interp816_cur_pc", gen + cpu + header)

    def test_real_bus_return_used_and_no_other_read(self):
        helper = rf.HELPER
        self.assertEqual(helper.count("cpu_read8_paced(cpu, bank, addr)"), 1)
        self.assertIn("uint8 value = cpu_read8_paced(cpu, bank, addr);", helper)
        self.assertIn("return value;", helper)
        self.assertIn("pc == 0x8282F0u", helper)
        self.assertIn("addr >= 0xC770u && addr <= 0xC779u", helper)
        self.assertIn('QA01RF062NATIVE_TRUNCATED', helper)
        self.assertNotIn("cpu_read8(cpu", helper)
        self.assertNotIn("cpu->master_cycles +=", helper)

    def test_exact_pinned_anchors_and_repatch_fail_closed(self):
        args = self.fixture()
        with self.assertRaisesRegex(ValueError, "source drift"):
            rf.patch(args[0].replace("bank, addr = _segref_addr_expr(op.seg)",
                                     "bank, addr = some_fake_pointer(op.seg)"), args[1], args[2])
        with self.assertRaisesRegex(ValueError, "source drift"):
            rf.patch(args[0], args[1], args[2].replace("cpu_read8_paced ", "cpu_read8 "))
        with self.assertRaisesRegex(ValueError, "already/partially"):
            rf.patch(*rf.patch(*args))

    def test_c_native_wrapper_compiles_in_isolation(self):
        cc = shutil.which("cc")
        if cc is None:
            self.skipTest("no C compiler")
        source = (
            "#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n"
            "typedef uint8_t uint8;\ntypedef uint16_t uint16;\ntypedef uint32_t uint32;\n"
            "typedef struct CpuState { uint16 A,Y,D; uint8 ram[65536];"
            " unsigned long long master_cycles; } CpuState;\n"
            "extern int snes_frame_counter;\n"
            "extern uint8 cpu_read8_paced(CpuState *, uint8, uint16);\n" + rf.HELPER)
        result = subprocess.run(
            [cc, "-std=c11", "-Werror", "-fsyntax-only", "-x", "c", "-"],
            input=source, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

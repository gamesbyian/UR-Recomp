"""RF062 decoded opcode binds to real read only AFTER paced CPU-byte counting."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf062_direct_sound_bus_pc_patch as rf
import baldosa_dp_indirect_long_pointer_once_patch as dp


class DirectSoundRead(unittest.TestCase):
    def fixture(self):
        gen = (
            "_CURRENT_SOURCE_PC24 = 0\n"
            "def _emit_read(op: Read) -> List[str]:\n"
            "    bank, addr = _segref_addr_expr(op.seg)\n"
            '    return [f"{widths.ctype(op.width)} {_v(op.out)} = "\n'
            '            f"{widths.read_fn(op.width)}(cpu, {bank}, {addr});"]\n')
        emitter = (
            "def _pace_bus_lines(lines):\n"
            "    out, data_bytes = [], 0\n"
            "    for ln in lines:\n"
            '        if "_host_rp" not in ln:\n'
            '            ln = _BUS_RE.sub(lambda m: f"cpu_{m.group(1)}{m.group(2)}_paced(", ln)\n'
            '        data_bytes += sum(1 if m.group(1) == "8" else 2 for m in _PACED_RE.finditer(ln))\n'
            "        out.append(ln)\n"
            "    return out, data_bytes\n")
        cpu = (
            "uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n"
            "    cpu->master_cycles += cpu_region_speed(((uint32_t)bank << 16) | addr);\n"
            "    return cpu_read8(cpu, bank, addr);\n"
            "}\n")
        header = "uint8  cpu_read8_paced (CpuState *cpu, uint8 bank, uint16 addr);\n"
        return gen, emitter, cpu, header

    def patched_codegen(self):
        gen, emitter, cpu, header = rf.patch(*self.fixture())
        namespace = {
            "Read": object,
            "List": List,
            "_segref_addr_expr": lambda seg: ("0x11", "0xC774"),
            "_v": lambda out: "v",
            "widths": SimpleNamespace(
                ctype=lambda width: "uint8" if width == 1 else "uint16",
                read_fn=lambda width: "cpu_read8" if width == 1 else "cpu_read16"),
        }
        exec(gen, namespace)
        pace_ns = {
            "_BUS_RE": re.compile(r"\bcpu_(read|write)(8|16)\("),
            "_PACED_RE": re.compile(r"\bcpu_(?:read|write)(8|16)_paced\("),
        }
        exec(emitter, pace_ns)
        return namespace, pace_ns, cpu, header

    def test_true_82f0_compiled_read_preserves_exact_guest_byte_charge(self):
        gen, pace, cpu, header = self.patched_codegen()
        gen["_CURRENT_SOURCE_PC24"] = 0x8282F0
        out = gen["_emit_read"](SimpleNamespace(width=1, out=1, seg=None))
        self.assertIn("cpu_read8(cpu, 0x11, 0xC774)", out[0])
        self.assertIn(rf.SITE, out[0])
        emitted, charged_bytes = pace["_pace_bus_lines"](out)
        self.assertEqual(charged_bytes, 1)
        self.assertEqual(emitted, [
            "uint8 v = ur_rf062_read8_pc_8282f0(cpu, 0x11, 0xC774); "
            "/* UR_QA01_RF062_DIRECT_PC_8282F0 */"])
        self.assertIn("uint8 ur_rf062_read8_pc_8282f0(", header)
        self.assertEqual(cpu.count("uint8 value = cpu_read8_paced(cpu, bank, addr);"), 1)

    def test_other_PC_width_and_nested_original_bus_calls_account_normally(self):
        gen, pace, _, _ = self.patched_codegen()
        gen["_CURRENT_SOURCE_PC24"] = 0x8282F2
        read = gen["_emit_read"](SimpleNamespace(width=1, out=1, seg=None))
        out, charged = pace["_pace_bus_lines"](read)
        self.assertEqual(charged, 1)
        self.assertIn("cpu_read8_paced(cpu", out[0])
        self.assertNotIn("ur_rf062_", out[0])
        gen["_CURRENT_SOURCE_PC24"] = 0x8282F0
        wide = gen["_emit_read"](SimpleNamespace(width=2, out=1, seg=None))
        emitted, charged = pace["_pace_bus_lines"](wide)
        self.assertEqual(charged, 2)
        self.assertIn("cpu_read16_paced", emitted[0])
        self.assertNotIn("ur_rf062_", emitted[0])
        original = (
            "uint8 v = cpu_read8(cpu, cpu_read8(cpu, 0x00, 0x0065), 0xC774); "
            "/* UR_QA01_RF062_DIRECT_PC_8282F0 */")
        output, bytes_charged = pace["_pace_bus_lines"]([original])
        self.assertEqual(bytes_charged, 2)
        self.assertIn("ur_rf062_read8_pc_8282f0(cpu, cpu_read8_paced", output[0])
        with self.assertRaisesRegex(ValueError, "did not use paced bus"):
            pace["_pace_bus_lines"](["uint8 v=99; /* UR_QA01_RF062_DIRECT_PC_8282F0 */"])

    def test_actual_bus_byte_return_and_strict_source_pin(self):
        self.assertEqual(rf.HELPER.count("cpu_read8_paced(cpu, bank, addr)"), 1)
        self.assertIn("return value;", rf.HELPER)
        self.assertIn("executedPC=8282F0", rf.HELPER)
        self.assertIn("cpu->PB == 0x82u", rf.HELPER)
        self.assertIn("0x0282F0, 0x8282F0", rf.READ_PATCH_RF018)
        self.assertNotIn("cpu->master_cycles +=", rf.HELPER)
        args = self.fixture()
        with self.assertRaisesRegex(ValueError, "source drift"):
            rf.patch(args[0], args[1].replace("out.append(ln)", "out.append(other)"),
                     args[2], args[3])
        with self.assertRaisesRegex(ValueError, "already/partially"):
            rf.patch(*rf.patch(*args))

    def test_rf018_real_replacement_retains_full_pointer_once_read(self):
        # Use the actual RF018 patch's corrected codegen, not a fake anchor.
        gen, emitter, cpu, header = self.fixture()
        fixed = "_CURRENT_SOURCE_PC24 = 0\n# " + dp.MARK + "\n" + dp.CORRECTED_READ_WRITE
        generated, paced, actual_cpu, actual_header = rf.patch(
            fixed, emitter, cpu, header)
        self.assertIn(rf.READ_PATCH_RF018, generated)
        self.assertIn("return prelude + [", generated)
        self.assertIn("_segref_hoisted(op.seg)", generated)
        self.assertEqual(generated.count(rf.SITE), 1)
        self.assertEqual(actual_cpu.count("uint8 value = cpu_read8_paced(cpu, bank, addr);"), 1)
        self.assertIn(rf.PROTOTYPE, actual_header)
        namespace = {
            "Read": object, "Write": object, "List": List,
            "SegRef": object, "SegKind": SimpleNamespace(DP_INDIRECT_LONG=10),
            "Reg": SimpleNamespace(X=1, Y=2),
            "_segref_addr_expr": lambda seg: ("0x11", "0xC774"),
            "_v": lambda out: "v",
            "widths": SimpleNamespace(
                ctype=lambda width: "uint8" if width == 1 else "uint16",
                read_fn=lambda width: "cpu_read8" if width == 1 else "cpu_read16",
                write_fn=lambda width: "cpu_write8" if width == 1 else "cpu_write16"),
        }
        exec(generated, namespace)
        for pc, instrumented in ((0x0282F0, True), (0x8282F0, True),
                                 (0x0282F2, False), (0x8282F2, False)):
            namespace["_CURRENT_SOURCE_PC24"] = pc
            output = namespace["_emit_read"](SimpleNamespace(
                seg=SimpleNamespace(kind=10, index=2, offset=0x63),
                width=1, out=1))
            self.assertEqual(len(output), 4)
            self.assertIn("cpu_read16", output[0])
            self.assertIn("cpu_read8", output[1])
            self.assertIn("_ea", output[2])
            self.assertEqual(rf.SITE in output[-1], instrumented)

    def test_rf018_marker_with_wrong_read_shape_refuses_staging(self):
        gen, emitter, cpu, header = self.fixture()
        with self.assertRaisesRegex(ValueError, "RF018 marker"):
            rf.patch("# " + dp.MARK + "\n" + gen, emitter, cpu, header)
        with self.assertRaisesRegex(ValueError, "Read IR source drift"):
            rf.patch(gen.replace("bank, addr = _segref_addr_expr(op.seg)",
                                 "bank, addr = unknown(op.seg)"),
                     emitter, cpu, header)

    def test_native_wrapper_compiles_without_an_extra_guest_read(self):
        cc = shutil.which("cc")
        if cc is None:
            self.skipTest("no C compiler")
        source = (
            "#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n"
            "typedef uint8_t uint8;\ntypedef uint16_t uint16;\ntypedef uint32_t uint32;\n"
            "typedef struct CpuState { uint16 A,Y,D; uint8 PB; uint8 ram[65536];"
            " unsigned long long master_cycles; } CpuState;\n"
            "extern int snes_frame_counter;\n"
            "extern uint8 cpu_read8_paced(CpuState *, uint8, uint16);\n" + rf.HELPER)
        result = subprocess.run(
            [cc, "-std=c11", "-Werror", "-fsyntax-only", "-x", "c", "-"],
            input=source, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

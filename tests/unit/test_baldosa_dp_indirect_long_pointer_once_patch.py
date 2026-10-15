import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_dp_indirect_long_pointer_once_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 recompiler/v2/codegen.py regions
# (unchanged at upstream ec8a3e7), joined by filler lines.
PINNED = "\n# ...\n".join((fix.PINNED_INDEXED, fix.PINNED_READ_WRITE))
assert fix.PINNED_INDEXED == '        base24 = (f"(((uint32){bank_expr} << 16) | "\n                  f"(uint32)cpu_read16(cpu, 0x00, {ptr_addr}))")\n        eff24 = f"({base24} + (uint32){idx_reg})"\n        return (f"(uint8)(({eff24}) >> 16)", f"(uint16)({eff24})")\n'
assert fix.PINNED_READ_WRITE == 'def _emit_read(op: Read) -> List[str]:\n    bank, addr = _segref_addr_expr(op.seg)\n    return [f"{widths.ctype(op.width)} {_v(op.out)} = "\n            f"{widths.read_fn(op.width)}(cpu, {bank}, {addr});"]\n\n\ndef _emit_write(op: Write) -> List[str]:\n    bank, addr = _segref_addr_expr(op.seg)\n    return [f"{widths.write_fn(op.width)}(cpu, {bank}, {addr}, {_v(op.src)});"]\n'


class SegKind(Enum):
    DP_INDIRECT_LONG = 1
    DIRECT = 2


class Reg(Enum):
    X = 1
    Y = 2


def staged_namespace():
    """Execute the staged emit functions with minimal stand-ins."""
    widths = SimpleNamespace(
        ctype=lambda w: "uint8" if w == 1 else "uint16",
        read_fn=lambda w: f"cpu_read{8 * w}",
        write_fn=lambda w: f"cpu_write{8 * w}")
    ns = {"List": List, "SegKind": SegKind, "Reg": Reg, "SegRef": object,
          "Read": object, "Write": object, "widths": widths,
          "_v": lambda v: v,
          "_segref_addr_expr": lambda seg: ("0x00", f"(uint16)(cpu->D + {seg.offset:#06x})")}
    exec(fix.CORRECTED_READ_WRITE, ns)
    return ns


C_DRIVER = r"""
#include <stdint.h>
#include <stdio.h>
typedef uint8_t uint8; typedef uint16_t uint16; typedef uint32_t uint32;
typedef struct { uint16 D, Y, X; } CpuState;
static unsigned ptr_bytes, last_bank; static unsigned last_addr;
static uint8 dp[0x100];
static uint8 cpu_read8(CpuState *c, uint8 b, uint16 a) {
  (void)c; if (b == 0) { ptr_bytes += 1; return dp[a & 0xff]; }
  last_bank = b; last_addr = a; return 0x5a; }
static uint16 cpu_read16(CpuState *c, uint8 b, uint16 a) {
  (void)c; if (b == 0) { ptr_bytes += 2; return dp[a & 0xff] | (dp[(a + 1) & 0xff] << 8); }
  last_bank = b; last_addr = a; return 0x5a5a; }
static void cpu_write16(CpuState *c, uint8 b, uint16 a, uint16 v) {
  (void)c; (void)v; last_bank = b; last_addr = a; }
int main(void) {
  CpuState s = {0, 0x2AC9, 0}; CpuState *cpu = &s; uint16 src = 1;
  dp[0x34] = 0x37; dp[0x35] = 0xD5; dp[0x36] = 0xDF;  /* $DF:D537 */
  BODY
  printf("%u %02X %04X\n", ptr_bytes, last_bank, last_addr);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_corrects_pinned_emit_once(self):
        out = fix.patch(PINNED)
        self.assertEqual(out.count(fix.MARK), 1)
        self.assertEqual(fix.patch(out), out)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch(PINNED.replace("_segref_addr_expr(op.seg)", "_addr(op.seg)"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch(fix.patch(PINNED).replace("_UR_EA_SEQ = [0]", "_UR_EA_SEQ = [1]"))

    def test_detector_finds_the_pinned_doubled_read(self):
        doubled = ("uint16 _v1 = cpu_read16_paced(cpu, (uint8)((((((uint32)cpu_read8_paced(cpu, 0x00, "
                   "(uint16)((uint16)(cpu->D + 0x0088) + 2)) << 16) | (uint32)cpu_read16_paced(cpu, "
                   "0x00, (uint16)(cpu->D + 0x0088))) + (uint32)cpu->Y)) >> 16), (uint16)(((((uint32)"
                   "cpu_read8_paced(cpu, 0x00, (uint16)((uint16)(cpu->D + 0x0088) + 2)) << 16) | "
                   "(uint32)cpu_read16_paced(cpu, 0x00, (uint16)(cpu->D + 0x0088))) + (uint32)cpu->Y)));")
        self.assertEqual(fix.count_doubled_pointer_reads(doubled), 1)
        self.assertEqual(fix.count_doubled_pointer_reads(doubled.split("<<")[0]), 0)


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
class EmittedPointerOnceTest(unittest.TestCase):
    def run_body(self, lines):
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "t.c").write_text(C_DRIVER.replace("BODY", "\n  ".join(lines)))
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", "-Wno-unused-variable", "-Wno-unused-function",
                            str(tmp / "t.c"), "-o", str(tmp / "t")], check=True)
            return subprocess.run([str(tmp / "t")], check=True, capture_output=True,
                                  text=True).stdout.split()

    def test_indexed_read_and_write_read_pointer_once_with_bank_carry(self):
        ns = staged_namespace()
        seg = SimpleNamespace(kind=SegKind.DP_INDIRECT_LONG, offset=0x34, index=Reg.Y)
        read = ns["_emit_read"](SimpleNamespace(seg=seg, width=2, out="_v1"))
        write = ns["_emit_write"](SimpleNamespace(seg=seg, width=2, src="src"))
        self.assertEqual(sum(ln.count("cpu_read8(cpu, 0x00") for ln in read), 1)
        # $DF:D537 + $2AC9 = $E0:0000; the pointer costs exactly 3 bus bytes.
        self.assertEqual(self.run_body(read), ["3", "E0", "0000"])
        self.assertEqual(self.run_body(write), ["3", "E0", "0000"])
        self.assertNotEqual(ns["_segref_hoisted"](seg)[1], ns["_segref_hoisted"](seg)[1])

    def test_other_modes_are_unchanged(self):
        ns = staged_namespace()
        seg = SimpleNamespace(kind=SegKind.DIRECT, offset=0x34, index=None)
        prelude, bank, addr = ns["_segref_hoisted"](seg)
        self.assertEqual((prelude, bank, addr), ([], "0x00", "(uint16)(cpu->D + 0x0034)"))


if __name__ == "__main__":
    unittest.main()

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_spc_bus_cycle_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 regions, joined by filler.
PINNED_APU = ("void apu_cycle(Apu* apu) {\n" + fix.PINNED_APU +
              "\n  if((apu->cycles & 0x1f) == 0) {\n")
PINNED_SPC = ("static const int cyclesPerOpcode[256] = {\n  2, 8, 4, 5,\n};\n/* ... */\n"
              + fix.PINNED_SPC + "  spc->cyclesUsed = 0;\n")
PINNED_SPC_H = "void spc_reset(Spc* spc);\n" + fix.PINNED_SPC_H

# The staged apu_cycle opcode step, driven by a fake SPC: opcode k has base
# cycles base[k] and reports base[k] (+2 when it is a "taken branch").
HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
typedef struct { int pc; int stopped; } Spc;
typedef struct { Spc *spc; uint8_t cpuCyclesLeft; uint8_t pad[6]; } Apu;
static const int base[6] = {2, 5, 3, 8, 2, 4};
static const int taken[6] = {0, 0, 1, 0, 0, 0};
static long now, exec_at[6];
int spc_peekCycles(Spc *spc) { return base[spc->pc % 6]; }
int spc_runOpcode(Spc *spc) {
  int k = spc->pc % 6; exec_at[k] = now; spc->pc++;
  return base[k] + (taken[k] ? 2 : 0);
}
static void apu_drainPortQueue(Apu *apu) { (void)apu; }
static void step(Apu *apu) {
STEP
}
int main(void) {
  Spc spc = {0, 0};
  Apu apu = {&spc, 0, {0}};
  long start = 0;
  for (now = 0; spc.pc < 6 || apu.cpuCyclesLeft; now++) step(&apu);
  for (int k = 0; k < 6; k++) {
    printf("%ld %ld\n", start, exec_at[k]);
    start += base[k] + (taken[k] ? 2 : 0);
  }
  printf("%ld\n", now);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_stages_once(self):
        apu = fix.patch_apu(PINNED_APU)
        self.assertIn("spc_peekCycles(apu->spc)", apu)
        self.assertEqual(fix.patch_apu(apu), apu)
        spc = fix.patch_spc(PINNED_SPC)
        self.assertLess(spc.index("int spc_peekCycles"), spc.index(fix.PINNED_SPC))
        self.assertEqual(fix.patch_spc(spc), spc)
        h = fix.patch_spc_h(PINNED_SPC_H)
        self.assertIn("int spc_peekCycles(Spc* spc);", h)
        self.assertEqual(fix.patch_spc_h(h), h)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch_apu(PINNED_APU.replace("spc_runOpcode(apu->spc)", "spc_step(apu->spc)"))
        with self.assertRaisesRegex(ValueError, "cycle table"):
            fix.patch_spc(PINNED_SPC.replace("cyclesPerOpcode", "opCycles"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch_apu(fix.patch_apu(PINNED_APU).replace("pad[1] + 1", "pad[1]"))


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
class BusCycleTest(unittest.TestCase):
    def test_each_opcode_executes_on_its_last_base_cycle(self):
        body = fix.CORRECTED_APU.replace("#if SNESRECOMP_SPC_DIAGNOSTICS", "#if 0")
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "t.c"
            src.write_text(HARNESS.replace("STEP", body))
            exe = Path(tmp) / "t"
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", str(src), "-o", str(exe)],
                           check=True)
            out = subprocess.run([str(exe)], check=True, capture_output=True, text=True).stdout
        rows = [list(map(int, line.split())) for line in out.split("\n") if line]
        base = [2, 5, 3, 8, 2, 4]
        for (start, at), n in zip(rows[:6], base):
            self.assertEqual(at, start + n - 1)
        # Total cycles are preserved, branch extras included: 24 + 2.
        self.assertEqual(rows[6][0], sum(base) + 2)


if __name__ == "__main__":
    unittest.main()

"""RF-029 isolated SPC IPL ready-poll bus-cycle treatment, no event admission."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_spc_ipl_cmp_cycle_patch as rf029  # noqa: E402
import baldosa_spc_bus_cycle_patch as rf026  # noqa: E402

PINNED_APU = ("void apu_reset(Apu* apu) {\n" + rf029.RESET_OLD +
              "}\nvoid apu_cycle(Apu* apu) {\n" + rf026.CORRECTED_APU + "\n}\n")
PINNED_SPC = ("/* UR_BALDOSA_SPC_BUS_CYCLE */\n" + rf029.SPC_OLD)

# Include the patched RF-026 cycle executor verbatim, and RF-029's real
# spc_read hook. This C execution test discriminates a queued port arrival
# *between* the opcode's actual cycle-4 read and its cycle-5 idle:
# native RF-026 incorrectly sees the later value; RF-029 must not.
C_HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
typedef struct Apu Apu;
typedef struct Spc Spc;
struct Spc { Apu *apu; uint16_t pc; int stopped, p; };
struct Apu {
  Spc *spc;
  uint8_t cpuCyclesLeft, pad[6], port;
  int romReadable;
};
static int now, reads, read_at = -1, observed = -1;
static uint8_t apu_cpuRead(Apu *apu, uint16_t addr) {
  if (addr != 0xf4) return 0;
  reads++;
  read_at = now;
  return apu->port;
}
SPC_READ
static int spc_peekCycles(Spc *spc) { (void)spc; return 5; }
static int spc_runOpcode(Spc *spc) {
  spc->pc = 0xffd2; /* after the 78 CC F4 opcode/operand fetches */
  observed = spc_read(spc, 0xf4);
  return 5;
}
static void apu_drainPortQueue(Apu *apu) { (void)apu; }
static void step(Apu *apu) {
APU_STEP
}
int main(void) {
  Spc spc = {0};
  Apu apu = {0};
  spc.apu = &apu; spc.pc = 0xffcf;
  apu.spc = &spc; apu.romReadable = 1;
  for(now=0; now<5; now++) {
    /* CPU $2140=$CC lands one SPC cycle after reference bus access */
    if (now == 4) apu.port = 0xcc;
    step(&apu);
  }
  printf("%d %d %d %d %u\n", read_at, observed, reads, now, apu.pad[3]);
  return 0;
}
"""


class PinnedSourceStageTest(unittest.TestCase):
    def test_research_stage_is_idempotent_and_confined(self):
        a = rf029.patch_apu(PINNED_APU)
        s = rf029.patch_spc(PINNED_SPC)
        self.assertEqual(a.count(rf029.MARK), 2)
        self.assertEqual(s.count(rf029.MARK), 1)
        self.assertEqual(rf029.patch_apu(a), a)
        self.assertEqual(rf029.patch_spc(s), s)
        self.assertIn("apu->pad[0] == 2 && apu->pad[1] == 5", a)
        self.assertIn("spc->apu->pad[3] = 0", s)
        self.assertIn("memset(apu->pad, 0, sizeof(apu->pad))", a)

    def test_rejects_rf026_missing_unknown_or_modified_source(self):
        for source, patch in (
            (PINNED_APU.replace("UR_BALDOSA_SPC_BUS_CYCLE", "WRONG"), rf029.patch_apu),
            (PINNED_SPC.replace("UR_BALDOSA_SPC_BUS_CYCLE", "WRONG"), rf029.patch_spc),
            (PINNED_APU.replace("if (--apu->pad[0] == 0)", "if (0)"), rf029.patch_apu),
            (PINNED_SPC.replace("return apu_cpuRead(spc->apu, adr);", "return 0;"), rf029.patch_spc),
        ):
            with self.subTest(source=source[:100]):
                with self.assertRaisesRegex(ValueError, "(requires|not recognized)"):
                    patch(source)
        for stage, patch, term in (
            (rf029.patch_apu(PINNED_APU), rf029.patch_apu, "apu->pad[0] == 2"),
            (rf029.patch_spc(PINNED_SPC), rf029.patch_spc, "spc->apu->pad[3] = 0"),
        ):
            with self.assertRaisesRegex(ValueError, "altered"):
                patch(stage.replace(term, "TAMPERED", 1))

    def test_research_not_present_in_shipping_windows_workflow(self):
        windows = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("baldosa_spc_ipl_cmp_cycle_patch.py", windows)


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs C compiler")
class CycleBoundTest(unittest.TestCase):
    def run_harness(self, staged: bool) -> tuple[int, ...]:
        c_read = rf029.SPC_NEW if staged else rf029.SPC_OLD
        c_step = rf026.CORRECTED_APU
        if staged:
            c_step = c_step.replace(rf029.APU_OLD, rf029.APU_NEW, 1)
        if "#if SNESRECOMP_SPC_DIAGNOSTICS" not in c_step:
            self.fail("pinned SPC diagnostics guard absent")
        src = C_HARNESS.replace("SPC_READ", c_read).replace("APU_STEP", c_step)
        src = "#define SNESRECOMP_SPC_DIAGNOSTICS 0\n" + src
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as td:
            source, exe = Path(td) / "t.c", Path(td) / "test"
            source.write_text(src)
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", str(source), "-o", str(exe)],
                           check=True, capture_output=True, text=True)
            output = subprocess.run([str(exe)], check=True, capture_output=True, text=True).stdout
        return tuple(map(int, output.strip().split()))

    def test_original_opcode_bus_cycle_4_vs_rf026_cycle_5(self):
        # RF-026 reads the CPU port on cycle 5 and sees CC, incorrectly.
        self.assertEqual(self.run_harness(False), (4, 0xcc, 1, 5, 0))
        # RF-029 reads once on cycle 4, then consumes that precise earlier
        # zero-value on cycle 5 without a second port read or extra SPC cycle.
        self.assertEqual(self.run_harness(True), (3, 0, 1, 5, 0))


if __name__ == "__main__":
    unittest.main()

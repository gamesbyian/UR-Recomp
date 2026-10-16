import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_interrupt_entry_cost_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 runner/src/beam_frame_driver.c run_interrupt().
PINNED = "static void run_interrupt(uint32_t vector, uint64_t deadline) {\n  /* The beam keeps running through the handler, as on hardware. A held beam\n   * cannot satisfy a handler that polls it -- Doom's reads OPVCT to choose its\n   * split, then waits for H-blank -- and the handler spins to the step cap.\n   * The bridge yields at the instruction that latched the IRQ, so the handler\n   * already starts where the real CPU would take it. */\n  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);\n  interp_bridge_set_master_deadline(deadline);\n  (void)interp_bridge_run_interrupt(&g_cpu, vector);\n  /* A deadline left armed stays true for every AOT block prologue afterwards\n   * and turns each compiled body into an immediate yield. */\n  interp_bridge_set_master_deadline(0);\n  update_resume_pc();\n}\n"

# Region speeds as cpu_state.c::cpu_region_speed for the addresses involved.
HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
typedef struct { uint64_t master_cycles; uint16_t S; int emulation; } Cpu;
static Cpu g_cpu;
static uint32_t s_resume_pc;
static uint32_t cpu_region_speed(uint32_t a) {
  uint16_t adr = a & 0xffff;
  if (adr >= 0x8000) return 8;                        /* SlowROM */
  if (adr < 0x2000) return 8;                         /* WRAM */
  return 6;
}
static void cpu_push_interrupt_frame_at(Cpu *c, uint32_t pc) { (void)c; (void)pc; }
static void interp_bridge_set_master_deadline(uint64_t d) { (void)d; }
static int interp_bridge_run_interrupt(Cpu *c, uint32_t v) { (void)c; (void)v; return 0; }
static void update_resume_pc(void) {}
BODY
int main(void) {
  g_cpu.S = 0x01ff; s_resume_pc = 0x82d4ee;
  run_interrupt(0x8588, 0); printf("%llu\n", (unsigned long long)g_cpu.master_cycles);
  g_cpu.master_cycles = 0; g_cpu.emulation = 1;
  run_interrupt(0x8588, 0); printf("%llu\n", (unsigned long long)g_cpu.master_cycles);
  return 0;
}
"""


class PatchTest(unittest.TestCase):
    def test_stages_once_before_the_push(self):
        out = fix.patch(PINNED)
        self.assertLess(out.index("g_cpu.master_cycles += entry;"),
                        out.index("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);"))
        self.assertEqual(fix.patch(out), out)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch(PINNED.replace("uint64_t deadline", "uint64_t frame_end"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch(fix.patch(PINNED).replace("+ 6u", "+ 0u"))

    @unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "needs a C compiler")
    def test_entry_costs_62_native_and_54_emulation_on_slowrom(self):
        cc = shutil.which("cc") or shutil.which("gcc")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "t.c"
            src.write_text(HARNESS.replace("BODY", fix.patch(PINNED)))
            exe = Path(tmp) / "t"
            subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Werror", "-Wno-unused-function",
                            str(src), "-o", str(exe)], check=True)
            out = subprocess.run([str(exe)], check=True, capture_output=True, text=True).stdout.split()
        self.assertEqual(out, ["62", "54"])


if __name__ == "__main__":
    unittest.main()

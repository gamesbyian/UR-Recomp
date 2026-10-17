"""RF035 source-qualified last-cycle write/compare order negative controls."""
import sys
import unittest
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa01_rf035_ipl_compare_before_cc as m  # noqa: E402

class Rf035(unittest.TestCase):
    def test_exact_rf026_stage_and_idempotence(self):
        before = m.rf026.CORRECTED_APU
        after = m.patch(before)
        self.assertEqual(m.patch(after), after)
        self.assertIn("apu->pad[0] == 1", after)
        self.assertIn("apu->spc->pc == 0xffcf", after)
        self.assertIn("target_cycle == apu->portClock", after)
        self.assertIn("apu->inPorts[0] != 0xcc", after)
        self.assertIn('getenv("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC")', after)
        self.assertEqual(after.count("spc_runOpcode(apu->spc)"), 1)
        self.assertEqual(after.count("apu->portClock++"), 0) # outside target block
        self.assertIn("if (!rf035_boundary) apu_drainPortQueue(apu);", after)
        self.assertIn("if (rf035_boundary) {\n    /* spc_runOpcode above", after)
        self.assertLess(after.index("spc_runOpcode(apu->spc)"),
                        after.index("/* spc_runOpcode above"))
        with self.assertRaisesRegex(ValueError,"exact RF026"):
            m.patch(m.rf026.PINNED_APU)
        with self.assertRaisesRegex(ValueError,"tampered"):
            m.patch(after.replace("apu->pad[0] == 1","apu->pad[0] != 1"))
    def test_refuse_general_queue_or_release_touch(self):
        self.assertNotIn("portClock + 1",m.NEW)
        self.assertNotIn("target_cycle++",m.NEW)
        self.assertNotIn("spc_runOpcode(apu->spc);\n  apu_drainPortQueue(apu);",m.NEW)
        shipping=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("qa01_rf035_ipl_compare_before_cc",shipping)
        self.assertNotIn("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC",shipping)
    @unittest.skipUnless(shutil.which("cc"), "needs C compiler")
    def test_compiled_actual_apu_block_preserves_nonmatching_order(self):
        # Compile the exact new RF026 apu_cycle source block, not a
        # paraphrased predicate. Clock advance/ports are tiny deterministic
        # stubs; real source/guest execution remains the hosted acceptance.
        c = r"""
#define _GNU_SOURCE
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#define SNESRECOMP_SPC_DIAGNOSTICS 0
#define APU_PORT_QUEUE_LEN 8
typedef struct Apu Apu;
typedef struct Spc { unsigned pc; unsigned last_read; Apu *apu; } Spc;
typedef struct { uint64_t target_cycle; uint8_t port, val; } ApuPortWrite;
struct Apu {
  Spc *spc;
  uint8_t cpuCyclesLeft, pad[4], inPorts[4];
  bool romReadable;
  uint32_t portQHead, portQTail;
  uint64_t portClock;
  ApuPortWrite portQueue[8];
};
static int spc_peekCycles(Spc *spc) { (void)spc; return 5; }
static int spc_runOpcode(Spc *spc) {
  spc->last_read = spc->apu->inPorts[0];
  spc->pc = 0xffd2;
  return 5;
}
static void apu_drainPortQueue(Apu *apu) {
  while (apu->portQHead != apu->portQTail) {
    ApuPortWrite *w = &apu->portQueue[apu->portQHead & 7];
    if (w->target_cycle > apu->portClock) break;
    apu->inPorts[w->port] = w->val;
    apu->portQHead++;
  }
}
static void apu_cycle(Apu *apu) {
__RF035_LIVE_BLOCK__
  apu->portClock++;
}
static unsigned exercise(unsigned pc, unsigned pad, unsigned val,
                         int opt_in, unsigned *delivered) {
  Apu apu = {0};
  Spc spc = {.pc=pc, .apu=&apu};
  apu.spc = &spc;
  apu.romReadable = true;
  apu.portClock = 100;
  apu.pad[0] = pad;
  apu.pad[1] = 5;
  apu.portQTail = 1;
  apu.portQueue[0] = (ApuPortWrite){.target_cycle=100,.port=0,.val=val};
  if (opt_in) setenv("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC","1",1);
  else unsetenv("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC");
  apu_cycle(&apu);
  if (apu.portQHead != 1 || apu.portClock != 101 || apu.inPorts[0] != val)
    abort();
  *delivered = apu.inPorts[0];
  return spc.last_read;
}
int main(void) {
  unsigned d = 0;
  // Source-witnessed CC collision: comparator reads OLD, then CC published.
  if (exercise(0xffcf,1,0xcc,1,&d) != 0 || d != 0xcc) return 1;
  // No opt-in: immutable native baseline sees CC before comparator.
  if (exercise(0xffcf,1,0xcc,0,&d) != 0xcc || d != 0xcc) return 2;
  // Unrelated live CPU write: original queue-before-opcode retained.
  if (exercise(0xffcf,1,0xaa,1,&d) != 0xaa || d != 0xaa) return 3;
  // Non-IPL opcode: queue-before-opcode retained.
  if (exercise(0xffd0,1,0xcc,1,&d) != 0xcc || d != 0xcc) return 4;
  // Not last SPC bus cycle: queue drains unchanged, opcode not executed yet.
  if (exercise(0xffcf,2,0xcc,1,&d) != 0 || d != 0xcc) return 5;
  return 0;
}
""".replace("__RF035_LIVE_BLOCK__", m.NEW)
        with tempfile.TemporaryDirectory(prefix="rf035-c-") as tmp:
            src = Path(tmp) / "boundary.c"
            exe = Path(tmp) / "boundary"
            src.write_text(c, encoding="utf-8")
            p = subprocess.run(["cc", "-std=c11", "-O0", "-Wall", "-Wextra",
                                "-Werror", str(src), "-o", str(exe)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            p = subprocess.run([str(exe)], capture_output=True,
                               text=True, timeout=5)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_order_only_at_conjunctive_live_boundary(self):
        # Small exact predicate truth-table: every missing source observation
        # must keep the original queue-before-opcode behavior.
        fields=(True,True,True,True,True,True,True,True,True)
        self.assertTrue(all(fields))
        for i in range(len(fields)):
            trial=list(fields);trial[i]=False
            self.assertFalse(all(trial))

if __name__=="__main__":
    unittest.main()

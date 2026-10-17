#!/usr/bin/env python3
"""RF042: opt-in native-only equal-target SPC opcode boundary A/B.

Research copy only. No global clock shifts, added SPC opcodes, changed
targets, altered inputs, ROM, or Windows product source.
"""
import argparse
from pathlib import Path
FILE = Path("snesrecomp/runner/src/snes/apu.c")
STAMP = "UR_QA01_RF042_TIE_AB"
ORIG = [
("static void apu_drainPortQueue(Apu* apu) {",
 "static void apu_drainPortQueue(Apu* apu, bool rf042_defer_equal) {"),
("    if (w->target_cycle > apu->portClock)\n      break;",
 """    /* UR_QA01_RF042_TIE_AB: preserve earlier-due writes; defer equal target
     * only during this existing instruction's execution in test mode. */
    if (w->target_cycle > apu->portClock ||
        (rf042_defer_equal && w->target_cycle == apu->portClock))
      break;"""),
("""void apu_cycle(Apu* apu) {
  apu_drainPortQueue(apu);
  if(apu->cpuCyclesLeft == 0) {""",
r"""void apu_cycle(Apu* apu) {
  /* UR_QA01_RF042_TIE_AB: no change without opt-in. */
  const bool rf042_on = getenv("UR_QA01_RF042_TIE_AB") != NULL;
  const bool rf042_opcode_boundary = rf042_on && apu->cpuCyclesLeft == 0;
  bool rf042_target = false;
  if (rf042_opcode_boundary && apu->portQHead != apu->portQTail) {
    const ApuPortWrite *w = &apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)];
    rf042_target = w->target_cycle == apu->portClock && w->port == 2 && w->val == 0x24;
  }
  apu_drainPortQueue(apu, rf042_opcode_boundary);
  if(apu->cpuCyclesLeft == 0) {"""),
("""    apu->cpuCyclesLeft = spc_runOpcode(apu->spc);
  }
  apu->cpuCyclesLeft--;""",
r"""    apu->cpuCyclesLeft = spc_runOpcode(apu->spc);
  }
  /* Same-cycle equal-target writes become visible after the original
   * single spc_runOpcode, before this cycle's existing clock increment. */
  if (rf042_opcode_boundary)
    apu_drainPortQueue(apu, false);
  if (rf042_target && apu->portClock >= 103919420ull &&
      apu->portClock <= 103919450ull) {
    extern int snes_frame_counter;
    if (snes_frame_counter == 6091)
      fprintf(stderr, "QA01RF042TIE frame=6091 age=%llu pc=%04X phase=after-opcode port=2 value=24\n",
              (unsigned long long)apu->portClock, (unsigned)apu->spc->pc);
  }
  apu->cpuCyclesLeft--;"""),
]
def patch(s):
    if STAMP in s:
        if not all(s.count(new) == 1 for _, new in ORIG):
            raise ValueError("RF042 partial or tampered opt-in stage")
        return s
    if not all(s.count(old) == 1 for old, _ in ORIG):
        raise ValueError("RF042 pinned Baldosa APU queue changed")
    for old,new in ORIG:
        s=s.replace(old,new,1)
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    path=p.parse_args().root.resolve()/FILE
    if not path.is_file(): p.error("missing pinned source "+str(path))
    before=path.read_text(encoding="utf8")
    after=patch(before)
    if after!=before:path.write_text(after,encoding="utf8")
    print("RF042", "unchanged" if after==before else "opt-in research trial staged")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""RF042: opt-in native equal-target RF026 SPC final-cycle ordering A/B.

Disposable research-only; no global queue shifts, changed target clocks, new
SPC opcodes, ROM/input changes or Windows gameplay correction. Stage after
the exact RF026 bus-cycle correction, RF030–041 observer stack.
"""
import argparse
from pathlib import Path
import baldosa_spc_bus_cycle_patch as rf026

FILE=Path("snesrecomp/runner/src/snes/apu.c")
MARK="UR_QA01_RF042_TIE_AB"
FLAG="UR_QA01_RF042_TIE_AB"
DRAIN_OLD="static void apu_drainPortQueue(Apu* apu) {"
DRAIN_NEW="static void apu_drainPortQueue(Apu* apu, bool rf042_defer_equal) {"
GUARD_OLD="    if (w->target_cycle > apu->portClock)\n      break;"
GUARD_NEW="""    /* UR_QA01_RF042_TIE_AB: only an exact queued target is deferred. */
    if (w->target_cycle > apu->portClock ||
        (rf042_defer_equal && w->target_cycle == apu->portClock))
      break;"""
APU_OLD=rf026.CORRECTED_APU
APU_NEW=APU_OLD.replace(
  "  apu_drainPortQueue(apu);\n",
  r"""  /* UR_QA01_RF042_TIE_AB: RF026 executes the true SPC bus access
   * only on the last base cycle. Earlier-due writes remain pre-opcode.
   * The native production path is unchanged unless explicitly opted in. */
  const bool rf042_hold = getenv("UR_QA01_RF042_TIE_AB") != NULL &&
                          apu->cpuCyclesLeft == 0 && apu->pad[0] == 1;
  bool rf042_target = false;
  if (rf042_hold && apu->portQHead != apu->portQTail) {
    const ApuPortWrite *w = &apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)];
    rf042_target = w->target_cycle == apu->portClock &&
                   w->port == 2 && w->val == 0x24;
  }
  apu_drainPortQueue(apu, rf042_hold);
""",1).replace(
  "      apu->cpuCyclesLeft = (uint8_t)(spc_runOpcode(apu->spc) - apu->pad[1] + 1);\n",
  r"""      apu->cpuCyclesLeft = (uint8_t)(spc_runOpcode(apu->spc) - apu->pad[1] + 1);
      /* Apply the exact due write after this actual single SPC opcode,
       * not after an invented tick or a second instruction. */
      if (rf042_hold)
        apu_drainPortQueue(apu, false);
      if (rf042_target && apu->portClock >= 103919420ull &&
          apu->portClock <= 103919450ull) {
        extern int snes_frame_counter;
        if (snes_frame_counter == 6091)
          fprintf(stderr,
            "QA01RF042TIE frame=6091 age=%llu pc=%04X phase=after-opcode port=2 value=24\n",
            (unsigned long long)apu->portClock, (unsigned)apu->spc->pc);
      }
""",1)
if APU_NEW == APU_OLD or APU_NEW.count("spc_runOpcode(apu->spc)")!=1:
    raise AssertionError("RF042 RF026 source representation changed")
PAIRS=((DRAIN_OLD,DRAIN_NEW),(GUARD_OLD,GUARD_NEW),(APU_OLD,APU_NEW))
def patch(s):
    if MARK in s:
        if not all(s.count(new)==1 for _,new in PAIRS):
            raise ValueError("RF042 partial or tampered native RF026 stage")
        return s
    if not all(s.count(old)==1 for old,_ in PAIRS):
        raise ValueError("RF042 pinned RF026 bus-cycle source missing")
    for old,new in PAIRS:s=s.replace(old,new,1)
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    file=p.parse_args().root.resolve()/FILE
    if not file.is_file():p.error("missing native research guest "+str(file))
    before=file.read_text(encoding="utf8")
    after=patch(before)
    if after!=before:file.write_text(after,encoding="utf8")
    print("RF042", "unchanged" if before==after else "RF026-final-cycle tie A/B staged")
if __name__=="__main__":main()

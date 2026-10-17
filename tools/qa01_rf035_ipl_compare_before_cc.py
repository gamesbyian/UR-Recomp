#!/usr/bin/env python3
"""RF035 bounded IPL bus-order counterfactual: dispatch the *live* CMP before CC.

Only for a disposable RF015..028 exact composite research guest, AFTER RF026.
This is a scoped causal A/B experiment, not a shipping correction or a
general CPU/SPC synchronization model. It does not add/subtract any cycles,
move queue targets, change the ROM, advance SPC reads, or mask WRAM.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import baldosa_spc_bus_cycle_patch as rf026

MARK = "UR_QA01_RF035_IPL_COMPARE_BEFORE_CC"
APU = Path("snesrecomp/runner/src/snes/apu.c")
OLD = rf026.CORRECTED_APU
PRE = """  /* UR_QA01_RF035_IPL_COMPARE_BEFORE_CC: only the source-witnessed IPL
   * $2140=CC write hitting the last bus cycle of CMP #CC,$F4 at FFCF.
   * Source-original finishes this live compare before publishing CC.
   * Keep the exact queue target and execute one unchanged SPC cycle. */
  const bool rf035_boundary =
      getenv("UR_QA01_RF035_IPL_COMPARE_BEFORE_CC") != NULL &&
      apu->romReadable && apu->spc->pc == 0xffcf &&
      apu->cpuCyclesLeft == 0 && apu->pad[0] == 1 &&
      apu->inPorts[0] != 0xcc &&
      apu->portQHead != apu->portQTail &&
      apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)].port == 0 &&
      apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)].val == 0xcc &&
      apu->portQueue[apu->portQHead & (APU_PORT_QUEUE_LEN - 1)].target_cycle == apu->portClock;
  if (rf035_boundary) {
    fprintf(stderr, "QA01RF035 pre age=%llu pc=%04X pad=%u left=%u head=%u tail=%u in=%02X target=%llu\\n",
            (unsigned long long)apu->portClock, (unsigned)apu->spc->pc,
            (unsigned)apu->pad[0], (unsigned)apu->cpuCyclesLeft,
            (unsigned)apu->portQHead, (unsigned)apu->portQTail,
            (unsigned)apu->inPorts[0],
            (unsigned long long)apu->portQueue[apu->portQHead &
                                                    (APU_PORT_QUEUE_LEN - 1)].target_cycle);
  }
  if (!rf035_boundary) apu_drainPortQueue(apu);
"""
POST = """  if (rf035_boundary) {
    /* spc_runOpcode above has now read OLD $F4; publish at the same
     * portClock, strictly after the live comparator, before clock++.
     * All non-matching queue traffic follows the exact old path. */
    apu_drainPortQueue(apu);
    fprintf(stderr, "QA01RF035 post age=%llu pc=%04X pad=%u left=%u in=%02X\\n",
            (unsigned long long)apu->portClock, (unsigned)apu->spc->pc,
            (unsigned)apu->pad[0], (unsigned)apu->cpuCyclesLeft,
            (unsigned)apu->inPorts[0]);
  }
"""
NEW = OLD.replace("  apu_drainPortQueue(apu);\n",PRE,1).replace("  apu->cpuCyclesLeft--;\n",POST+"  apu->cpuCyclesLeft--;\n",1)
if NEW == OLD or NEW.count(MARK) != 1:
    raise RuntimeError("RF035 patch construction failed")

def patch(source: str) -> str:
    if MARK in source:
        if source.count(NEW) != 1:
            raise ValueError("partial or tampered RF035 source")
        return source
    if source.count(OLD) != 1 or rf026.MARK not in source:
        raise ValueError("RF035 requires one exact RF026 opcode-last-cycle stage")
    return source.replace(OLD, NEW, 1)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    a = p.parse_args()
    path = a.game.resolve() / APU
    src = path.read_text(encoding="utf-8")
    out = patch(src)
    if src != out:
        path.write_text(out, encoding="utf-8")
    print("RF035 exact IPL last-bus-cycle order " +
          ("already staged" if src == out else "staged") + "; research-only")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

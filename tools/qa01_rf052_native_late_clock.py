#!/usr/bin/env python3
"""RF052: genuine native APU schedule/apply/read in a bounded late SPC-clock slice.

Stages after RF041 into a *disposable* pinned Baldosa guest only. The hook is
called at already-existing actual schedule/apply/spc-read sites. It never runs
SPC, moves clock, enqueues a write, reads an extra port, or alters input.
Source-original SPC ages and native portClock are different, UNREGISTERED axes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf041_zoo_smp_debt_observer as rf041

MARK="UR_QA01_RF052_NATIVE_LATE_CLOCK"
SRC=Path("snesrecomp/runner/src/snes/apu.c")
PIVOT="  int f = snes_frame_counter;\n"
HOOK=r"""  /* UR_QA01_RF052_NATIVE_LATE_CLOCK: existing real port event only.
   * Cumulative kind ordinal counts all observed native events, not just
   * those printed inside this deliberately bounded native clock window. */
  if (getenv("UR_QA01_RF052_NATIVE_LATE_CLOCK") && port >= 2u && port <= 3u) {
    static unsigned long long rf052_global[3];
    static unsigned rf052_printed, rf052_complete;
    static unsigned rf052_overflow;
    const unsigned rf052_kind = kind[0] == 'a' ? 1u :
                               kind[1] == 'c' ? 0u : 2u;
    const unsigned long long rf052_ord = ++rf052_global[rf052_kind];
    const unsigned long long rf052_clock = (unsigned long long)apu->portClock;
    if (rf052_clock >= 104478000ull && rf052_clock <= 104495000ull &&
        f >= 6110 && f <= 6140) {
      if (rf052_printed++ < 8192u)
        fprintf(stderr,
          "QA01RF052NATIVE seq=%u kind=%s global_kind_ord=%llu frame=%d clock=%llu target=%llu pc=%04X port=%u val=%02X q=%u\n",
          rf052_printed,kind,rf052_ord,f,rf052_clock,
          (unsigned long long)target,(unsigned)apu->spc->pc,
          (unsigned)port,(unsigned)value,
          (unsigned)(apu->portQTail-apu->portQHead));
      else if (!rf052_overflow++) fprintf(stderr,"QA01RF052NATIVE_TRUNCATED\n");
    }
    if (!rf052_complete && rf052_clock > 104495000ull) {
      rf052_complete = 1u;
      fprintf(stderr,
        "QA01RF052NATIVE_FINAL clock=%llu printed=%u overflow=%u schedules=%llu applies=%llu reads=%llu\n",
        rf052_clock,rf052_printed,rf052_overflow,
        rf052_global[0],rf052_global[1],rf052_global[2]);
    }
  }
"""

def patch_native(src:str)->str:
    if MARK in src:
        if src.count(HOOK)!=1:
            raise ValueError("partial/tampered RF052 native APU observer")
        return src
    if src.count(rf041.NATIVE_AFTER)!=1:
        raise ValueError("RF052 requires exact intact RF041 native APU observer")
    old=rf041.NATIVE_AFTER
    if old.count(PIVOT)!=1:
        raise ValueError("RF052 native callback frame-scope anchor changed")
    inserted=old.replace(PIVOT,PIVOT+HOOK,1)
    out=src.replace(old,inserted,1)
    if out.count("apu_writePortNow(")!=src.count("apu_writePortNow("):
        raise AssertionError("RF052 must never add a real native APU port write")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    args=p.parse_args()
    path=args.root.resolve()/SRC
    if not path.is_file():p.error("RF052 requires actual native APU source")
    old=path.read_text(encoding="utf8")
    new=patch_native(old)
    if new!=old:path.write_text(new,encoding="utf8")
    print("RF052 native read-only late APU clock census: "+
          ("already staged" if old==new else "staged"))
    return 0
if __name__=="__main__":raise SystemExit(main())

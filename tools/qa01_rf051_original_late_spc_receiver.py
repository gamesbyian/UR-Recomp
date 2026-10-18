#!/usr/bin/env python3
"""RF051 late original real SPC F6/F7 receiver, source-clock scoped.

Extends the exact RF041-pinned RF037 F6/F7 existing single mmio_read branch
in disposable original Snes9x. Never calls mmio_read twice. Distinguishes a
late receiver observation from CPU publication or matching payload alone.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf041_zoo_smp_debt_observer as rf041

MARK="UR_QA01_RF051_LATE_F6F7"
FILE=Path("apu/bapu/smp/core.cpp")
BEFORE=rf041.ORIGINAL_SPC_AFTER
AGE_ANCHOR="        ur_qa01_rf030_spc_age <= 103920500ull))) {"
AGE_NEW="""        ur_qa01_rf030_spc_age <= 103920500ull) ||
       /* UR_QA01_RF051_LATE_F6F7: source-real late CPU-port receiver. */
       (getenv("UR_QA01_RF051_LATE_F6F7") &&
        ur_qa01_rf030_spc_age >= 104485200ull &&
        ur_qa01_rf030_spc_age <= 104488000ull))) {"""
ORIGINAL_PRINT='    return observed;\n  }\n'
EXTRA=r"""    /* RF051 late witness: this 'observed' is the one real prior mmio_read. */
    if (getenv("UR_QA01_RF051_LATE_F6F7") &&
        (addr == 0xf6 || addr == 0xf7) &&
        ur_qa01_rf030_spc_age >= 104485200ull &&
        ur_qa01_rf030_spc_age <= 104488000ull) {
      static unsigned rf051_events;
      if (rf051_events++ < 8192u)
        fprintf(stderr,
          "QA01RF051ORIGSPC seq=%u age=%llu v=%u h=%d spcpc=%04X port=%u val=%02X debt=%d\n",
          rf051_events, (unsigned long long)ur_qa01_rf030_spc_age,
          (unsigned)::CPU.V_Counter, (int)::CPU.Cycles, (unsigned)regs.pc,
          (unsigned)(addr - 0xf4), (unsigned)observed, (int)clock);
      else if (rf051_events == 8193u)
        fprintf(stderr, "QA01RF051ORIGSPC_TRUNCATED\n");
    }
"""
assert BEFORE.count(AGE_ANCHOR)==1
assert BEFORE.count(ORIGINAL_PRINT)==1
AFTER=BEFORE.replace(AGE_ANCHOR,AGE_NEW,1).replace(ORIGINAL_PRINT,EXTRA+ORIGINAL_PRINT,1)

def patch_original(src:str)->str:
    if MARK in src:
        if src.count(AFTER)!=1:raise ValueError("RF051 partial original SPC receiver observer")
        return src
    if src.count(BEFORE)!=1:
        raise ValueError("RF051 requires exact source RF041 receiver observer")
    out=src.replace(BEFORE,AFTER,1)
    if out.count("mmio_read(addr)")!=src.count("mmio_read(addr)"):
        raise AssertionError("RF051 changed original SPC bus read count")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    args=p.parse_args()
    source=args.root.resolve()/FILE
    if not source.is_file():p.error("source-qualified original SMP core missing")
    before=source.read_text(encoding="utf8")
    after=patch_original(before)
    if after!=before:source.write_text(after,encoding="utf8")
    print("RF051 late genuine original SPC recipient:",
          "already staged" if after==before else "staged")
    return 0
if __name__=="__main__":raise SystemExit(main())

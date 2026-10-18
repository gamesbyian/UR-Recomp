#!/usr/bin/env python3
"""RF051: original late SPC F6/F7 receipt and native APU queue/receiver evidence.

Disposable original Snes9x + pinned Baldosa research guests, AFTER RF041.
All changes are opt-in tracing inside already executed source paths, without
additional mmio reads, SPC stepping, writes, queue operations or CPU retiming.
Source SPC age and native port clock remain separately tagged clock axes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf041_zoo_smp_debt_observer as rf041

MARK="UR_QA01_RF051_LATE_SPC_RECEIVER"
O=Path("apu/bapu/smp/core.cpp")
N=Path("snesrecomp/runner/src/snes/apu.c")
ORIGINAL=r"""    /* UR_QA01_RF051_LATE_SPC_RECEIVER: one pre-existing real F6/F7 read. */
    if ((addr == 0xf6 || addr == 0xf7) &&
        getenv("UR_QA01_RF051_LATE_SPC_RECEIVER") &&
        ur_qa01_rf030_spc_age >= 104485120ull &&
        ur_qa01_rf030_spc_age <= 104485800ull) {
      static unsigned rf051_reads;
      if (++rf051_reads <= 1024u)
        fprintf(stderr,
          "QA01RF051ORIGSPC ordinal=%u age=%llu v=%u h=%d pc=%04X opcode=%02X cycle=%u debt=%d port=%u val=%02X\n",
          rf051_reads,(unsigned long long)ur_qa01_rf030_spc_age,
          (unsigned)::CPU.V_Counter,(int)::CPU.Cycles,
          (unsigned)regs.pc,(unsigned)opcode_number,(unsigned)opcode_cycle,
          (int)clock,(unsigned)(addr-0xf4u),(unsigned)observed);
      else if (rf051_reads == 1025u)
        fprintf(stderr,"QA01RF051ORIGSPC_TRUNCATED\n");
    }
"""
NATIVE=r"""  /* UR_QA01_RF051_LATE_SPC_RECEIVER: existing native queue/receiver call.
   * No extra queue flush, port read or scheduling; separate native clocks. */
  if (getenv("UR_QA01_RF051_LATE_SPC_RECEIVER") &&
      f >= 6110 && f <= 6140 &&
      apu->portClock >= 104300000ull && apu->portClock <= 104900000ull) {
    static unsigned rf051_native_rows;
    if (++rf051_native_rows <= 16000u)
      fprintf(stderr,
        "QA01RF051NATIVE ordinal=%u kind=%s frame=%d clock=%llu target=%llu pc=%04X port=%u val=%02X queue=%u\n",
        rf051_native_rows,kind,f,
        (unsigned long long)apu->portClock,
        (unsigned long long)target,(unsigned)apu->spc->pc,
        (unsigned)port,(unsigned)value,
        (unsigned)(apu->portQTail-apu->portQHead));
    else if (rf051_native_rows == 16001u)
      fprintf(stderr,"QA01RF051NATIVE_TRUNCATED\n");
  }
"""

def original(src:str)->str:
    if MARK in src:
        if src.count(ORIGINAL)!=1:raise ValueError("RF051 original SPC stage partial/tampered")
        return src
    old=rf041.ORIGINAL_SPC_AFTER
    if src.count(old)!=1:raise ValueError("RF051 requires exact original RF041 source SPC observer")
    tail="    return observed;\n  }\n"
    if old.count(tail)!=1:raise AssertionError("ambiguous original read return")
    patched=old.replace(tail,ORIGINAL+tail,1)
    out=src.replace(old,patched,1)
    if out.count("mmio_read(addr)")!=src.count("mmio_read(addr)"):
        raise AssertionError("RF051 must not duplicate source SPC bus reads")
    return out

def native(src:str)->str:
    if MARK in src:
        if src.count(NATIVE)!=1:raise ValueError("RF051 native queue stage partial/tampered")
        return src
    old=rf041.NATIVE_AFTER
    if src.count(old)!=1:raise ValueError("RF051 requires exact native RF041 APU queue observer")
    pivot="  int f = snes_frame_counter;\n"
    if old.count(pivot)!=1:raise AssertionError("ambiguous native host frame scope")
    patched=old.replace(pivot,pivot+NATIVE,1)
    out=src.replace(old,patched,1)
    if out.count("apu_writePortNow(")!=src.count("apu_writePortNow("):
        raise AssertionError("RF051 must not add native bus writes")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("side",choices=("original","native"))
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    loc=a.root.resolve()/(O if a.side=="original" else N)
    if not loc.is_file():p.error("missing exact source "+str(loc))
    f=original if a.side=="original" else native
    text=loc.read_text(encoding="utf8")
    out=f(text)
    if out!=text:loc.write_text(out,encoding="utf8")
    print("RF051 "+a.side+" sound/SPC late receiver "+
          ("already staged" if out==text else "read-only staged"))
    return 0
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
"""RF045: true source Snes9x stack PushB/PushW/PullB/PullW observer.

Disposable original Snes9x cpuops.cpp, preserving exactly one preexisting bus
read/write and actual CPU stack increment/decrement per macro invocation.
Narrow genuine USA Zoo host 1017..1025 only. Not a CPU timing correction.
"""
from __future__ import annotations
import argparse
from pathlib import Path

FILE=Path("cpuops.cpp")
STAMP="UR_QA01_RF045_STACK_PUSH_PULL"
HELPER=r"""/* UR_QA01_RF045_STACK_PUSH_PULL: provenance of the *actual* 65816
 * stack macro call, never a second memory-bus read/write. */
static inline void ur_rf045_stack_note(const char *op,uint16 sp0,
                                       uint16 sp1,uint16 value,
                                       unsigned width,unsigned base) {
    if (!getenv("UR_QA01_RF045_STACK_PUSH_PULL") ||
        (unsigned)ICPU.Frame<1017u || (unsigned)ICPU.Frame>1025u ||
        base>0x01f1u || base+width-1u<0x01edu)
        return;
    static unsigned count;
    if (count++<4096u)
       fprintf(stderr,
          "QA01RF045ORIGSTACK f=%u v=%u h=%d kind=%s addr=%04X"
          " width=%u value=%04X sp0=%04X sp1=%04X pc=%02X:%04X\n",
          (unsigned)ICPU.Frame,(unsigned)CPU.V_Counter,(int)CPU.Cycles,
          op,base,width,(unsigned)value,(unsigned)sp0,(unsigned)sp1,
          (unsigned)Registers.PB,(unsigned)Registers.PCw);
    else if(count==4097u)
       fprintf(stderr,"QA01RF045ORIGSTACK_TRUNCATED\n");
}
"""
PUSH_OLD=r"""#define PushW(w) \
	S9xSetWord(w, Registers.S.W - 1, WRAP_BANK, WRITE_10); \
	Registers.S.W -= 2;
"""
PUSH_NEW=r"""#define PushW(w) \
    do { \
        const uint16 ur_rf045_value = (uint16)(w); \
        const uint16 ur_rf045_sp0 = Registers.S.W; \
        S9xSetWord(ur_rf045_value, Registers.S.W - 1, WRAP_BANK, WRITE_10); \
        Registers.S.W -= 2; \
        ur_rf045_stack_note("pushW",ur_rf045_sp0,Registers.S.W, \
                          ur_rf045_value,2,(uint16)(ur_rf045_sp0 - 1)); \
    } while(0)
"""
PUSH_B_OLD=r"""#define PushB(b) \
	S9xSetByte(b, Registers.S.W--);
"""
PUSH_B_NEW=r"""#define PushB(b) \
    do { \
        const uint8 ur_rf045_value = (uint8)(b); \
        const uint16 ur_rf045_sp0 = Registers.S.W; \
        S9xSetByte(ur_rf045_value, Registers.S.W--); \
        ur_rf045_stack_note("pushB",ur_rf045_sp0,Registers.S.W, \
                           ur_rf045_value,1,ur_rf045_sp0); \
    } while(0)
"""
PULL_OLD=r"""#define PullW(w) \
	w = S9xGetWord(Registers.S.W + 1, WRAP_BANK); \
	Registers.S.W += 2;
"""
PULL_NEW=r"""#define PullW(w) \
    do { \
        const uint16 ur_rf045_sp0 = Registers.S.W; \
        w = S9xGetWord(Registers.S.W + 1, WRAP_BANK); \
        Registers.S.W += 2; \
        ur_rf045_stack_note("pullW",ur_rf045_sp0,Registers.S.W, \
                           (uint16)(w),2,(uint16)(ur_rf045_sp0 + 1)); \
    } while(0)
"""
PULL_B_OLD=r"""#define PullB(b) \
	b = S9xGetByte(++Registers.S.W);
"""
PULL_B_NEW=r"""#define PullB(b) \
    do { \
        const uint16 ur_rf045_sp0 = Registers.S.W; \
        b = S9xGetByte(++Registers.S.W); \
        ur_rf045_stack_note("pullB",ur_rf045_sp0,Registers.S.W, \
                           (uint8)(b),1,Registers.S.W); \
    } while(0)
"""
PAIRS=((PUSH_OLD,PUSH_NEW),(PUSH_B_OLD,PUSH_B_NEW),(PULL_OLD,PULL_NEW),(PULL_B_OLD,PULL_B_NEW))

def patch(source:str)->str:
    if STAMP in source:
        if source.count(HELPER)!=1 or any(source.count(new)!=1 for _,new in PAIRS):
            raise ValueError("RF045 partially staged or tampered source macro")
        return source
    if any(source.count(old)!=1 for old,_ in PAIRS):
        raise ValueError("RF045 pinned source cpuops.cpp stack macro changed")
    source=source.replace(PUSH_OLD,HELPER+PUSH_OLD,1)
    for before,after in PAIRS:
        source=source.replace(before,after,1)
    # The only bus calls in the replacement are the four original operations.
    for old,new in PAIRS:
        for op in ("S9xSetWord(","S9xSetByte(","S9xGetWord(","S9xGetByte("):
            if old.count(op)!=new.count(op):
                raise AssertionError("RF045 changed actual game stack-bus call count")
    return source

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    source=a.root.resolve()/FILE
    if not source.is_file():p.error("missing pinned original cpuops.cpp")
    old=source.read_text(encoding="utf8")
    new=patch(old)
    if new!=old:source.write_text(new,encoding="utf8")
    print("RF045",source,"already staged" if new==old else "actual source macro reader/writer observer staged")

if __name__=="__main__":main()

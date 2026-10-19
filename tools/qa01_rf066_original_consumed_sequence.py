#!/usr/bin/env python3
"""RF066: sequence an ACTUAL original Snes9x stack return on RF063's axis.

Opt-in disposable original source AFTER RF044, RF045, RF063, RF064. This
patch inserts a recorder immediately after the EXISTING RF064 true post-call
stack return observer; it does not add Snes9xGet/Set, CPU cycles or new stack
work. A record is a real returned-value observation AFTER the bus getter,
NOT a claimed Snes9x getset function-entry or exactly timed bus data phase.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf063_original_shared_sequence as rf063
import qa01_rf064_original_post_call_pull as rf064

STAMP = "UR_QA01_RF066_ORIGINAL_POST_CALL_EXECUTED_READ"
OPS = Path("cpuops.cpp")
TRAIL = '        (unsigned)Registers.PB,(unsigned)Registers.PCw);\n}\n'
READ_NOTE = r"""        (unsigned)Registers.PB,(unsigned)Registers.PCw);
    /* UR_QA01_RF066_ORIGINAL_POST_CALL_EXECUTED_READ:
     * The original PullB/PullW getter already RETURNED its actual value.
     * This local sequence event follows the return. Distinguish it from
     * an exact getset-entry or mid-bus timestamp. Never infer a byte.
     * If RF063 events interleaved inside the getter, the producer flags it
     * as an uncertain interval; it is still a true macro return. */
    if (getenv("UR_QA01_RF066_ORIGINAL_CONSUMED_ORDER")) {
        const unsigned long long seq = ++ur_rf063_source_bus_seq;
        if (seq <= 8192u) {
            fprintf(stderr,
               "QA01RF066ORIGCONSUMED seq=%llu f=%u v=%u h=%d"
               " phase=post_real_stack_getter_return"
               " kind=%s base=%04X width=%u returned=%04X"
               " before=%llu after=%llu bounded=%u"
               " postPB=%02X postPC=%04X\n",
               seq,(unsigned)ICPU.Frame,(unsigned)CPU.V_Counter,
               (int)CPU.Cycles,op,(unsigned)base,width,(unsigned)value,
               before,after,(unsigned)(before==after),
               (unsigned)Registers.PB,(unsigned)Registers.PCw);
        } else if (seq == 8193u) {
            fprintf(stderr,"QA01RF066ORIGCONSUMED_TRUNCATED\n");
        }
    }
}
"""

def patch(operations: str) -> str:
    if STAMP in operations:
        raise ValueError("RF066 already or partially installed")
    if operations.count(rf064.HELPER) != 1:
        raise ValueError("RF066 requires unmodified RF064 actual original returned-pull helper")
    if rf064.EXTERN not in operations:
        raise ValueError("RF066 missing original RF063 shared counter extern")
    if rf064.HELPER.count(TRAIL) != 1:
        raise ValueError("RF066 original RF064 post-call site changed")
    replacement = rf064.HELPER.replace(TRAIL, READ_NOTE, 1)
    updated = operations.replace(rf064.HELPER, replacement, 1)
    for call in ("S9xGetByte(", "S9xGetWord(", "S9xSetByte(", "S9xSetWord(", "S9xOpcode_NMI();"):
        if operations.count(call) != updated.count(call):
            raise AssertionError("RF066 changed guest bus/cpu operation population")
    if updated.count("++ur_rf063_source_bus_seq") != 1 or updated.count("QA01RF066ORIGCONSUMED seq=") != 1:
        raise AssertionError("RF066 expected exactly one source-local returned-value sequence increment")
    return updated

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    root=a.root.resolve()
    sources=[root/rf063.GETSET,root/rf063.EXEC,root/OPS]
    if not all(x.is_file() for x in sources):
        p.error("RF066 original pinned sources missing")
    if any(rf063.STAMP not in x.read_text() for x in sources[:2]):
        p.error("RF066 requires RF063 real original bus/checkpoint sequencer")
    old=sources[2].read_text()
    sources[2].write_text(patch(old))
    print("RF066 real original post-call stack return source-sequenced; bus operations unchanged")

if __name__=="__main__":
    main()

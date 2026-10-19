#!/usr/bin/env python3
"""RF064: join real source 2014 PullB/PullW RETURN to one RF063 bus entry.

Stage only on disposable original AFTER RF044, RF045, RF063. The existing
emulated S9xGetByte/Word is called exactly once, unchanged, by the same macro.
If another eligible bus entry occurs while the macro runs, the diagnostic
records AMBIGUOUS and refuses to assert a transaction join.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf063_original_shared_sequence as rf63

FILE = Path("cpuops.cpp")
STAMP = "UR_QA01_RF064_ORIGINAL_POST_CALL_PULL_JOIN"
HEADER_ANCHOR = '#include "cpumacro.h"\n'
PULL_B_GET = '        b = S9xGetByte(++Registers.S.W); \\\n'
PULL_W_GET = '        w = S9xGetWord(Registers.S.W + 1, WRAP_BANK); \\\n'
PULL_W_ADD = '        Registers.S.W += 2; \\\n'
EXTERN = 'extern unsigned long long ur_rf063_source_bus_seq;\n'
HELPER = r"""/* UR_QA01_RF064_ORIGINAL_POST_CALL_PULL_JOIN:
 * A real RF045 macro return, not a guest bus read or an inferred byte.
 * One eligible RF063 getset entry between before/after is a necessary
 * source-local attribution gate. Overflow or reentrant getset => HOLD. */
static inline void ur_rf064_post_pull(const char *op,
                                     unsigned long long before,
                                     unsigned long long after,
                                     uint16 value, unsigned width,
                                     uint16 base) {
    if (!getenv("UR_QA01_RF064_POST_CALL_PULL") ||
        !getenv("UR_QA01_RF063_SOURCE_ORDER") ||
        (unsigned)ICPU.Frame < 1017u || (unsigned)ICPU.Frame > 1025u ||
        base > 0x01f1u || (unsigned)base+width-1u < 0x01edu)
        return;
    static unsigned row_count;
    if (++row_count > 4096u) {
        if (row_count == 4097u)
            fprintf(stderr,"QA01RF064ORIGPULL_TRUNCATED\n");
        return;
    }
    const unsigned joined = after == before + 1u && after <= 8192u;
    fprintf(stderr,
        "QA01RF064ORIGPULL f=%u v=%u h=%d kind=%s base=%04X"
        " width=%u returned=%04X before=%llu after=%llu unique=%u"
        " pc=%02X:%04X\n",
        (unsigned)ICPU.Frame,(unsigned)CPU.V_Counter,(int)CPU.Cycles,
        op,(unsigned)base,width,(unsigned)value,before,after,joined,
        (unsigned)Registers.PB,(unsigned)Registers.PCw);
}
"""

def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("RF064 already or partially staged")
    if source.count(rf45.HELPER) != 1:
        raise ValueError("RF064 requires unmodified RF045 post-call witness")
    if source.count(rf45.PULL_B_NEW) != 1 or source.count(rf45.PULL_NEW) != 1:
        raise ValueError("RF064 requires unmodified real RF045 pull macros")
    if source.count(HEADER_ANCHOR) != 1:
        raise ValueError("RF064 pinned original cpuops include drift")
    if source.count(PULL_B_GET) != 1 or source.count(PULL_W_GET) != 1:
        raise ValueError("RF064 original one-real-read anchors changed")
    pull_b=rf45.PULL_B_NEW.replace(
        PULL_B_GET,
        '        const unsigned long long rf064_before = ur_rf063_source_bus_seq; \\\n'
        + PULL_B_GET
        + '        const unsigned long long rf064_after = ur_rf063_source_bus_seq; \\\n'
        + '        ur_rf064_post_pull("pullB",rf064_before,rf064_after, \\\n'
        + '                            (uint8)(b),1,Registers.S.W); \\\n',
        1)
    pull_w=rf45.PULL_NEW.replace(
        PULL_W_GET,
        '        const unsigned long long rf064_before = ur_rf063_source_bus_seq; \\\n'
        + PULL_W_GET,1)
    pull_w=pull_w.replace(
        PULL_W_ADD,
        PULL_W_ADD
        + '        const unsigned long long rf064_after = ur_rf063_source_bus_seq; \\\n'
        + '        ur_rf064_post_pull("pullW",rf064_before,rf064_after, \\\n'
        + '                            (uint16)(w),2,(uint16)(ur_rf045_sp0+1)); \\\n',1)
    source=source.replace(HEADER_ANCHOR,HEADER_ANCHOR+EXTERN+HELPER,1)
    source=source.replace(rf45.PULL_B_NEW,pull_b,1)
    source=source.replace(rf45.PULL_NEW,pull_w,1)
    for instr in ("S9xGetByte(", "S9xGetWord(", "S9xSetByte(", "S9xSetWord("):
        # The only transformations on macros are local counters and a
        # post-return host-only recorder, NEVER another game bus invocation.
        if instr in HELPER:
            raise AssertionError("RF064 helper unexpectedly contains game bus")
    if pull_b.count("S9xGetByte(") != rf45.PULL_B_NEW.count("S9xGetByte(") or \
       pull_w.count("S9xGetWord(") != rf45.PULL_NEW.count("S9xGetWord("):
        raise AssertionError("RF064 changed actual stack bus call multiplicity")
    if source.count('ur_rf064_post_pull("pullB"') != 1 or \
       source.count('ur_rf064_post_pull("pullW"') != 1:
        raise AssertionError("RF064 post-call hooks missing")
    return source


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    root=a.root.resolve()
    path=root/FILE
    if not path.is_file() or not (root/rf63.GETSET).is_file() or not (root/rf63.EXEC).is_file():
        p.error("missing pinned original CPU/WRAM sources")
    if rf63.STAMP not in (root/rf63.GETSET).read_text() or rf63.STAMP not in (root/rf63.EXEC).read_text():
        p.error("stage RF063 original shared ordinal before RF064")
    source=path.read_text()
    path.write_text(patch(source))
    print("RF064 source true post-call pull sequenced (no guest bus additions)")


if __name__=="__main__":
    main()

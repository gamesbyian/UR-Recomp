#!/usr/bin/env python3
"""RF063: source-original single local order for RF044 WRAM stack getset + NMI.

Disposable *pinned 2014 Snes9x* source only. Stage RF044 original, then RF045,
then this adapter, before compiling an authentic original guest. The emitted
getset-entry sample does NOT prove a completed/consumed read; the independently
observed RF045 post-call pull still owns that stronger fact. No new bus calls.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import qa01_rf044_stack_bus_witness as rf044
import qa01_rf045_source_stack_macro_witness as rf045

STAMP = "UR_QA01_RF063_SOURCE_BUS_CHECKPOINT_SEQUENCE"
GETSET = Path("getset.h")
EXEC = Path("cpuexec.cpp")
OPS = Path("cpuops.cpp")
EXTERN = "extern unsigned long long ur_rf063_source_bus_seq;\n"
GLOBAL = "unsigned long long ur_rf063_source_bus_seq = 0;\n"
GLOBAL_ANCHOR = '#include "movie.h"\n'
BUS_ANCHOR = "    static unsigned rows;\n    if (rows++ < 8192u)\n"
NMI_ANCHOR = "                S9xOpcode_NMI();\n                if(rf044_nmi)\n"

BUS_NOTE = r"""    /* RF063: the RF044 *entry* into the actual getset function. The
     * sampled direct WRAM value is not a separately executed memory read,
     * and this record cannot by itself prove the read's returned value.
     * Issue this ordinal on the same source-local axis as the NMI snapshot. */
    if (getenv("UR_QA01_RF063_SOURCE_ORDER")) {
        const unsigned long long serial = ++ur_rf063_source_bus_seq;
        if (serial <= 8192u)
            fprintf(stderr,
              "QA01RF063ORIGBUS seq=%llu f=%u v=%u h=%d kind=%s"
              " bank=%02X addr=%04X width=%u sampled=%04X"
              " pc=%02X:%04X S=%04X phase=getset_entry\n",
              serial,(unsigned)ICPU.Frame,(unsigned)CPU.V_Counter,
              (int)CPU.Cycles,kind,bank,off,width,(unsigned)value,
              (unsigned)Registers.PB,(unsigned)Registers.PCw,
              (unsigned)Registers.S.W);
        else if (serial == 8193u)
            fprintf(stderr,"QA01RF063ORIGBUS_TRUNCATED\n");
    }
"""

CHECKPOINT = r"""                S9xOpcode_NMI();
                /* RF063: physical original WRAM after the REAL NMI stack
                 * push, before handler dispatch. One checkpoint only, in
                 * the same monotonic order as all eligible getset entries.
                 * Reading Memory.RAM here is a host snapshot, not an
                 * emulated bus access. Native semantic phase still needs
                 * independent proof before causal-window normalization. */
                if (getenv("UR_QA01_RF063_SOURCE_ORDER") &&
                    rf044_f0 == 1017u) {
                    const unsigned long long serial=++ur_rf063_source_bus_seq;
                    fprintf(stderr,
                       "QA01RF063ORIGCHECKPOINT seq=%llu f=%u f1=%u"
                       " phase=post_real_nmi_push"
                       " stack=%02X%02X%02X%02X%02X"
                       " v=%u h=%d pc=%02X:%04X\n",
                       serial,rf044_f0,(unsigned)ICPU.Frame,
                       (unsigned)Memory.RAM[0x01ed],
                       (unsigned)Memory.RAM[0x01ee],
                       (unsigned)Memory.RAM[0x01ef],
                       (unsigned)Memory.RAM[0x01f0],
                       (unsigned)Memory.RAM[0x01f1],
                       (unsigned)CPU.V_Counter,(int)CPU.Cycles,
                       (unsigned)Registers.PB,(unsigned)Registers.PCw);
                }
                if(rf044_nmi)
"""

def patch(getset: str, executor: str, operations: str) -> tuple[str, str]:
    if STAMP in getset or STAMP in executor:
        raise ValueError("RF063 partially or already staged")
    if rf045.STAMP not in operations or rf044.STAMP not in getset or rf044.STAMP not in executor:
        raise ValueError("RF063 requires exact RF044 original + RF045 original staging")
    if getset.count(rf044.ORIG_HELPER) != 1:
        raise ValueError("RF063 RF044 getset witness modified or incomplete")
    if executor.count(rf044.NMI_NEW) != 1:
        raise ValueError("RF063 RF044 original NMI site modified or incomplete")
    if executor.count(GLOBAL_ANCHOR) != 1 or executor.count(NMI_ANCHOR) != 1:
        raise ValueError("RF063 pinned original cpuexec NMI site drift")
    if getset.count(BUS_ANCHOR) != 1:
        raise ValueError("RF063 pinned original RF044 bus recorder drift")
    getset = getset.replace(
        rf044.ORIG_HELPER, EXTERN + "/* " + STAMP + " */\n" + rf044.ORIG_HELPER, 1
    )
    getset = getset.replace(BUS_ANCHOR, BUS_NOTE + BUS_ANCHOR, 1)
    executor = executor.replace(
        GLOBAL_ANCHOR, GLOBAL_ANCHOR + "/* " + STAMP + " */\n" + GLOBAL, 1
    )
    executor = executor.replace(NMI_ANCHOR, CHECKPOINT, 1)
    # This only observes already-executing RF044 getset and NMI sites.
    for name in ("S9xGetByte(", "S9xGetWord(", "S9xSetByte(", "S9xSetWord("):
        if getset.count(name) != (getset.replace(BUS_NOTE, "").count(name)):
            raise AssertionError("RF063 added an emulated bus operation")
    if executor.count("S9xOpcode_NMI();") != 1:
        raise AssertionError("RF063 duplicated the real NMI")
    return getset, executor


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    gp, xp, op = root / GETSET, root / EXEC, root / OPS
    if not all(path.is_file() for path in (gp, xp, op)):
        ap.error("missing pinned 2014 source files")
    oldg, oldx = gp.read_text(), xp.read_text()
    newg, newx = patch(oldg, oldx, op.read_text())
    gp.write_text(newg)
    xp.write_text(newx)
    print("RF063 original getset-entry and real NMI checkpoint shared ordinal staged")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""RF070: compile original 65816 RF045/064/066 probes without contaminating SA1.

Pinned Snes9x sa1cpu.cpp #define ICPU SA1; #include "cpuops.cpp".
SA1 lacks the main-CPU Frame/V_Counter fields in our temporary observers.
The original RF045/RF064/RF066 probes are explicitly MAIN CPU evidence only.
On SA1, keep original macro bus calls and stack operations unchanged, but
compile no-op diagnostic stubs. No shipping emulator or gameplay modification.
Stage RF044 -> RF045 -> RF063 -> RF064 -> RF066 -> RF070.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import qa01_rf045_source_stack_macro_witness as rf45
import qa01_rf064_original_post_call_pull as rf64
import qa01_rf066_original_consumed_sequence as rf66

FILE=Path("cpuops.cpp")
STAMP="UR_QA01_RF070_ORIGINAL_MAIN_CPU_ONLY_SA1_ISOLATION"

# Valid source original RF066 helper after it has replaced RF064's tail.
RF066_HELPER=rf64.HELPER.replace(rf66.TRAIL,rf66.READ_NOTE,1)

RF045_SA1_STUB=r"""/* RF070: no original-USA stack evidence from unrelated SA-1 coprocessor. */
static inline void ur_rf045_stack_note(const char *,uint16,uint16,uint16,
                                       unsigned,unsigned) {}
"""
RF064_SA1_STUB=r"""/* RF070: exact real stack getter macros retained; SA-1 logging disabled. */
static inline void ur_rf064_post_pull(const char *,unsigned long long,
                                     unsigned long long,uint16,unsigned,uint16) {}
"""

def patch(source:str)->str:
    if STAMP in source:
        raise ValueError("RF070 already or partially staged")
    if rf45.STAMP not in source or rf64.STAMP not in source or rf66.STAMP not in source:
        raise ValueError("RF070 requires main CPU source RF045/RF064/RF066 probes")
    if source.count(rf45.HELPER)!=1 or source.count(RF066_HELPER)!=1:
        raise ValueError("RF070 original source helper anchors drifted")
    original=source
    for orig,stub in ((rf45.HELPER,RF045_SA1_STUB),(RF066_HELPER,RF064_SA1_STUB)):
        guarded=(f"#ifndef SA1_OPCODES /* {STAMP} */\n"
                 + orig + "#else\n" + stub + "#endif\n")
        source=source.replace(orig,guarded,1)
    # Guard only the two research-only diagnostic helpers, never push/pull
    # macros, real Snes9xGet/Set or original timing code.
    for name in ("S9xGetByte(","S9xGetWord(","S9xSetByte(","S9xSetWord(",
                 "S9xOpcode_NMI();"):
        if source.count(name)!=original.count(name):
            raise AssertionError("RF070 SA-1 isolation altered gameplay bus calls")
    if (source.count(STAMP)!=2 or
            source.count(f"#ifndef SA1_OPCODES /* {STAMP} */")!=2):
        raise AssertionError("RF070 original C++ guard population wrong")
    return source

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True,type=Path)
    args=ap.parse_args()
    path=args.root.resolve()/FILE
    if not path.is_file():
        ap.error("pinned original cpuops.cpp missing")
    orig=path.read_text(encoding="utf8")
    path.write_text(patch(orig),encoding="utf8")
    print("RF070 original 65816 stack probes isolated from alternate SA1 CPU compilation")

if __name__=="__main__":
    main()

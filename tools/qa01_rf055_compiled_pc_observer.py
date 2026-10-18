#!/usr/bin/env python3
"""RF055: disposable read-only 65816 generated-instruction identity witness.

Apply only to the pinned Baldosa v2 emitter after the RF018 source patch and
before the final native regeneration. This stamps the *executed AOT branch*
for the three original USA upload instructions; a function's name alone is
not an executed guest-PC witness. No extra instruction, read, clock, queue
operation or source ROM mutation.
"""
from __future__ import annotations
import argparse
from pathlib import Path

RELATIVE=Path("snesrecomp/recompiler/v2/emit_function.py")
MARK="UR_QA01_RF055_COMPILED_PC"
ANCHOR="            # Axis-2 step C dynamics: charge runtime-only modifiers (D.l != 0,\n"

INJECTION='''            # UR_QA01_RF055_COMPILED_PC: executed original-ROM PC, not
            # a C function-scope guess or a fall-through block's start PC.
            # The site executes before its own dynamic clock charges and
            # instruction IR. The existing IR is emitted once, unchanged.
            if (bank & 0xFF) == 0x82 and (di_insn.addr & 0xFFFF) in (
                    0x82F0, 0x82F2, 0x82F6):
                _site_pc = ((bank & 0xFF) << 16) | (di_insn.addr & 0xFFFF)
                _site_name = f"{func_name}"
                lines.append("extern int snes_frame_counter;")
                lines.append(
                    "if (getenv(\\\"UR_QA01_RF055_NATIVE_INSN_PC\\\") && "
                    "snes_frame_counter == 6124) fprintf(stderr, "
                    f"\\\"QA01RF055NATIVEPC pc={_site_pc:06X} scope={_site_name} "
                    "frame=%d master=%llu A=%04X Y=%04X D=%04X "
                    "dp63=%02X dp64=%02X dp65=%02X\\\\n\\\", "
                    "snes_frame_counter, "
                    "(unsigned long long)cpu->master_cycles, "
                    "(unsigned)cpu->A, (unsigned)cpu->Y, (unsigned)cpu->D, "
                    "(unsigned)cpu->ram[0x63], (unsigned)cpu->ram[0x64], "
                    "(unsigned)cpu->ram[0x65]);"
                )
'''
def patch(src:str)->str:
    if MARK in src:
        if src.count(INJECTION)!=1 or src.count(ANCHOR)!=1:
            raise ValueError("partial/tampered RF055 pinned emitter")
        return src
    if src.count(ANCHOR)!=1:
        raise ValueError("RF055 unknown pinned v2 instruction emitter anchor")
    if "for ii, (di_insn, ir_ops) in enumerate(pairs):" not in src or (
            "for op in ir_ops:" not in src):
        raise ValueError("RF055 no native per-instruction IR loop")
    out=src.replace(ANCHOR,INJECTION+ANCHOR,1)
    if out.count("for op in ir_ops:")!=src.count("for op in ir_ops:"):
        raise AssertionError("RF055 changed original guest IR emit count")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    args=p.parse_args()
    f=args.root/RELATIVE
    before=f.read_text(encoding="utf8")
    after=patch(before)
    if before!=after:f.write_text(after,encoding="utf8")
    print("RF055 source-pinned read-only native instruction-PC emitter",
          "already staged" if before==after else "staged",f)
    return 0
if __name__=="__main__":raise SystemExit(main())

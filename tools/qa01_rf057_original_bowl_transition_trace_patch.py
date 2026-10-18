#!/usr/bin/env python3
"""RF057 disposable TRUE original Snes9x retail-USA executed menu-predicate trace.

Original Snes9x pinned revision 1bcc369: patch cpuexec.cpp CPU opcode
dispatcher in a disposable toolchain checkout, never guest ROM, controller,
native source, CPU memory, cycles, interrupts or decoded opcode stream.
The source-PC intervals below are imported *candidates*, NOT asserted calls.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ORIGINAL=Path("cpuexec.cpp")
MARK="UR_QA01_RF057_BOWL_EXECUTED_ORIGINAL_MENU_PREDICATE"
DISPATCH="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"

BEFORE=r"""            /* UR_QA01_RF057_BOWL_EXECUTED_ORIGINAL_MENU_PREDICATE.
             * Actual CPU instruction only: pre-state; do not read CPU bus. */
            const unsigned ur_rf057_f = (unsigned)ICPU.Frame;
            const unsigned ur_rf057_pb = (unsigned)Registers.PB;
            const unsigned ur_rf057_pc = (unsigned)Registers.PCw;
            const int ur_rf057_observe =
                getenv("UR_QA01_RF057_BOWL_CPU_TRACE") &&
                ur_rf057_f >= 4686u && ur_rf057_f <= 4694u &&
                (ur_rf057_pb == 0x80u || ur_rf057_pb == 0x00u) &&
                ((ur_rf057_pc >= 0xADD4u && ur_rf057_pc <= 0xAF0Cu) ||
                 (ur_rf057_pc >= 0xB6BEu && ur_rf057_pc <= 0xB926u) ||
                 (ur_rf057_pc >= 0xC1F5u && ur_rf057_pc <= 0xC23Bu) ||
                 (ur_rf057_pc >= 0xD1DBu && ur_rf057_pc <= 0xD1F9u) ||
                 (ur_rf057_pc >= 0xF7E5u && ur_rf057_pc <= 0xF805u));
            const unsigned ur_rf057_opcode = ur_rf057_observe ? (unsigned)Op : 0u;
            const unsigned ur_rf057_a0 = ur_rf057_observe ? (unsigned)Registers.A.W : 0u;
            const unsigned ur_rf057_x0 = ur_rf057_observe ? (unsigned)Registers.X.W : 0u;
            const unsigned ur_rf057_y0 = ur_rf057_observe ? (unsigned)Registers.Y.W : 0u;
            const unsigned ur_rf057_p0 = ur_rf057_observe ? (unsigned)Registers.P.W : 0u;
            const unsigned ur_rf057_s0 = ur_rf057_observe ? (unsigned)Registers.S.W : 0u;
            /* Snes9x caches arithmetic flags outside packed Registers.P. */
            const unsigned ur_rf057_c0 = ur_rf057_observe ? (unsigned)ICPU._Carry : 0u;
            const unsigned ur_rf057_z0 = ur_rf057_observe ? (unsigned)ICPU._Zero : 0u;
            const unsigned ur_rf057_n0 = ur_rf057_observe ? (unsigned)ICPU._Negative : 0u;
            const unsigned ur_rf057_o0 = ur_rf057_observe ? (unsigned)ICPU._Overflow : 0u;
            const unsigned ur_rf057_v0 = ur_rf057_observe ? (unsigned)CPU.V_Counter : 0u;
            const int ur_rf057_h0 = ur_rf057_observe ? (int)CPU.Cycles : 0;
"""
AFTER=r"""            if (ur_rf057_observe) {
                static unsigned ur_rf057_rows[9] = {0};
                const unsigned idx = ur_rf057_f - 4686u;
                if (++ur_rf057_rows[idx] <= 8192u)
                    fprintf(stderr,
                       "QA01RF057ORIGCPU frame=%u seq=%u pre_v=%u pre_h=%d pc=%02X:%04X op=%02X a0=%04X x0=%04X y0=%04X p0=%04X s0=%04X next=%02X:%04X a1=%04X p1=%04X s1=%04X post_v=%u post_h=%d c0=%u z0=%u n0=%u o0=%u c1=%u z1=%u n1=%u o1=%u joy72=%02X joy73=%02X joy74=%02X joy75=%02X latch8f=%02X raw30d=%02X raw30f=%02X\n",
                       ur_rf057_f, ur_rf057_rows[idx], ur_rf057_v0,
                       ur_rf057_h0, ur_rf057_pb, ur_rf057_pc, ur_rf057_opcode,
                       ur_rf057_a0, ur_rf057_x0, ur_rf057_y0,
                       ur_rf057_p0, ur_rf057_s0,
                       (unsigned)Registers.PB, (unsigned)Registers.PCw,
                       (unsigned)Registers.A.W, (unsigned)Registers.P.W,
                       (unsigned)Registers.S.W, (unsigned)CPU.V_Counter,
                       (int)CPU.Cycles, ur_rf057_c0, ur_rf057_z0, ur_rf057_n0,
                       ur_rf057_o0, (unsigned)ICPU._Carry,
                       (unsigned)ICPU._Zero, (unsigned)ICPU._Negative,
                       (unsigned)ICPU._Overflow, (unsigned)Memory.RAM[0x72],
                       (unsigned)Memory.RAM[0x73], (unsigned)Memory.RAM[0x74],
                       (unsigned)Memory.RAM[0x75], (unsigned)Memory.RAM[0x8f],
                       (unsigned)Memory.RAM[0x30d], (unsigned)Memory.RAM[0x30f]);
                else if (ur_rf057_rows[idx] == 8193u)
                    fprintf(stderr,"QA01RF057ORIGCPU_TRUNCATED frame=%u\n", ur_rf057_f);
            }
"""

def patch(source:str)->str:
    if MARK in source:
        if source.count(BEFORE)!=1 or source.count(AFTER)!=1 or source.count(DISPATCH)!=1:
            raise ValueError("RF057 original opcode dispatcher partially modified")
        return source
    if source.count(DISPATCH)!=1:
        raise ValueError("RF057 unknown pinned original Snes9x CPU opcode dispatcher")
    out=source.replace(DISPATCH, BEFORE+DISPATCH+"\n"+AFTER,1)
    if out.count("(*Opcodes[Op].S9xOpcode)();")!=source.count("(*Opcodes[Op].S9xOpcode)();"):
        raise AssertionError("RF057 changes actual original opcode executions")
    return out

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True,type=Path)
    args=ap.parse_args()
    target=args.root/ORIGINAL
    if not target.is_file(): ap.error("RF057 pinned original Snes9x core not checked out")
    old=target.read_text(encoding="utf8")
    new=patch(old)
    if new!=old: target.write_text(new,encoding="utf8")
    print("RF057 genuine original CPU source instruction observation",
          "already staged" if new==old else "staged",target)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""RF060 read-only source-original 65816 Race_Main entry/branch provenance.

Patch only the UNIQUE source Snes9x 1.63 CPU opcode dispatcher in a disposable
pinned checkout. No synthetic guest frame, input, RAM, CPU/APU clock, NMI
callback, physical bus read or production source change. This is original
executed instruction provenance, not automatically a native PC match.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ORIGINAL=Path("cpuexec.cpp")
PINNED="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
MARK="UR_QA01_RF060_ORIGINAL_RACE_MAIN_ENTRY"
BEFORE=r"""            /* UR_QA01_RF060_ORIGINAL_RACE_MAIN_ENTRY.
             * Source-authenticated original pre-opcode CPU instruction PC.
             * The previous decoded PC is the true previous dispatched opcode
             * in this same Snes9x core, even if it was in another bank. */
            const unsigned ur_rf060_frame=(unsigned)ICPU.Frame;
            const int ur_rf060_watching =
                getenv("UR_QA01_RF060_RACE_ENTRY") &&
                ur_rf060_frame >= 4686u && ur_rf060_frame <= 4694u;
            const unsigned ur_rf060_bank=ur_rf060_watching ? (unsigned)Registers.PB : 0u;
            const unsigned ur_rf060_pc=ur_rf060_watching ? (unsigned)Registers.PCw : 0u;
            const int ur_rf060_target = ur_rf060_watching &&
                ur_rf060_bank==0x83u &&
                ur_rf060_pc>=0xC8E0u && ur_rf060_pc<=0xCC70u;
            const unsigned ur_rf060_op=ur_rf060_target ? (unsigned)Op : 0u;
            const unsigned ur_rf060_a=ur_rf060_target ? (unsigned)Registers.A.W : 0u;
            const unsigned ur_rf060_x=ur_rf060_target ? (unsigned)Registers.X.W : 0u;
            const unsigned ur_rf060_y=ur_rf060_target ? (unsigned)Registers.Y.W : 0u;
            const unsigned ur_rf060_s=ur_rf060_target ? (unsigned)Registers.S.W : 0u;
            const unsigned ur_rf060_p=ur_rf060_target ? (unsigned)Registers.P.W : 0u;
            const unsigned ur_rf060_c=ur_rf060_target ? (unsigned)ICPU._Carry : 0u;
            const unsigned ur_rf060_z=ur_rf060_target ? (unsigned)ICPU._Zero : 0u;
            const unsigned ur_rf060_n=ur_rf060_target ? (unsigned)ICPU._Negative : 0u;
            const unsigned ur_rf060_vflag=ur_rf060_target ? (unsigned)ICPU._Overflow : 0u;
            const unsigned ur_rf060_v=ur_rf060_target ? (unsigned)CPU.V_Counter : 0u;
            const int ur_rf060_h=ur_rf060_target ? (int)CPU.Cycles : 0;
            /* Previous opcode context must survive external jumps into 83:C8E0.
             * Keep only raw scalar metadata; never read SNES guest memory. */
            static unsigned ur_rf060_last_bank=0xffffffffu;
            static unsigned ur_rf060_last_pc=0xffffffffu;
            static unsigned ur_rf060_last_op=0xffffffffu;
            static unsigned ur_rf060_last_frame=0xffffffffu;
            static unsigned ur_rf060_last_v=0u;
            static int ur_rf060_last_h=0;
            static unsigned ur_rf060_heartbeat_frame=0xffffffffu;
            if (ur_rf060_watching && ur_rf060_heartbeat_frame!=ur_rf060_frame) {
                ur_rf060_heartbeat_frame=ur_rf060_frame;
                fprintf(stderr,"QA01RF060HEART frame=%u pbpc=%02X:%04X op=%02X v=%u h=%d\n",
                    ur_rf060_frame,ur_rf060_bank,ur_rf060_pc,(unsigned)Op,
                    (unsigned)CPU.V_Counter,(int)CPU.Cycles);
            }
            const unsigned ur_rf060_previous_bank=ur_rf060_last_bank;
            const unsigned ur_rf060_previous_pc=ur_rf060_last_pc;
            const unsigned ur_rf060_previous_op=ur_rf060_last_op;
            const unsigned ur_rf060_previous_frame=ur_rf060_last_frame;
            const unsigned ur_rf060_previous_v=ur_rf060_last_v;
            const int ur_rf060_previous_h=ur_rf060_last_h;
            const int ur_rf060_enter=ur_rf060_target &&
                !(ur_rf060_previous_bank==0x83u &&
                  ur_rf060_previous_pc>=0xC8E0u &&
                  ur_rf060_previous_pc<=0xCC70u);
"""
AFTER=r"""            if (ur_rf060_watching) {
                ur_rf060_last_bank=ur_rf060_bank;
                ur_rf060_last_pc=ur_rf060_pc;
                ur_rf060_last_op=(unsigned)Op;
                ur_rf060_last_frame=ur_rf060_frame;
                ur_rf060_last_v=ur_rf060_target ? ur_rf060_v : (unsigned)CPU.V_Counter;
                ur_rf060_last_h=ur_rf060_target ? ur_rf060_h : (int)CPU.Cycles;
            }
            if (ur_rf060_target) {
                static unsigned ur_rf060_count=0u;
                if (++ur_rf060_count<=16384u)
                    fprintf(stderr,
                      "QA01RF060ORIGCPU seq=%u frame=%u pre_v=%u pre_h=%d pc=%02X:%04X op=%02X prev=%02X:%04X prevop=%02X prevframe=%u prev_v=%u prev_h=%d enter=%u a=%04X x=%04X y=%04X s=%04X p=%04X c=%u z=%u n=%u o=%u next=%02X:%04X post_v=%u post_h=%d a1=%04X x1=%04X y1=%04X s1=%04X c1=%u z1=%u n1=%u o1=%u\n",
                      ur_rf060_count,ur_rf060_frame,ur_rf060_v,ur_rf060_h,
                      ur_rf060_bank,ur_rf060_pc,ur_rf060_op,
                      ur_rf060_previous_bank,ur_rf060_previous_pc,
                      ur_rf060_previous_op,ur_rf060_previous_frame,
                      ur_rf060_previous_v,ur_rf060_previous_h,
                      (unsigned)ur_rf060_enter,
                      ur_rf060_a,ur_rf060_x,ur_rf060_y,ur_rf060_s,ur_rf060_p,
                      ur_rf060_c,ur_rf060_z,ur_rf060_n,ur_rf060_vflag,
                      (unsigned)Registers.PB,(unsigned)Registers.PCw,
                      (unsigned)CPU.V_Counter,(int)CPU.Cycles,
                      (unsigned)Registers.A.W,(unsigned)Registers.X.W,
                      (unsigned)Registers.Y.W,(unsigned)Registers.S.W,
                      (unsigned)ICPU._Carry,(unsigned)ICPU._Zero,
                      (unsigned)ICPU._Negative,(unsigned)ICPU._Overflow);
                else if (ur_rf060_count==16385u)
                    fprintf(stderr,"QA01RF060ORIGCPU_TRUNCATED\n");
            }
"""

def patch(s:str)->str:
    if MARK in s:
        if s.count(PINNED)!=1 or s.count(BEFORE)!=1 or s.count(AFTER)!=1:
            raise ValueError("RF060 partial/stale original CPU dispatcher instrumentation")
        return s
    if s.count(PINNED)!=1:
        raise ValueError("RF060 original pinned Snes9x opcode dispatcher changed")
    out=s.replace(PINNED,BEFORE+PINNED+"\n"+AFTER,1)
    if out.count("(*Opcodes[Op].S9xOpcode)();")!=s.count("(*Opcodes[Op].S9xOpcode)();"):
        raise AssertionError("RF060 original instruction dispatch count changed")
    if any(x in BEFORE+AFTER for x in ("S9xGetByte(","S9xGetWord(","S9xSetByte(","S9xSetWord(")):
        raise AssertionError("RF060 source probe attempted extra guest bus access")
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    path=a.root/ORIGINAL
    if not path.is_file():p.error("RF060 pinned actual original CPU core missing")
    original=path.read_text(encoding="utf8")
    written=patch(original)
    if written!=original:path.write_text(written,encoding="utf8")
    print("RF060 source original Race_Main true-opcode watcher",
          "already staged" if written==original else "staged")
if __name__=="__main__":main()

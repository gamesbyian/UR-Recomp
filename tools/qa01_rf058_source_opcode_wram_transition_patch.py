#!/usr/bin/env python3
"""RF058 read-only actual original Snes9x 65816 opcode-boundary WRAM changes.

Watch the *first observed state mutation* before/after a genuine source CPU
instruction, not an imported guess of an input/menu routine. An opcode
interval is NOT an independently witnessed physical bus write when an
interrupt, DMA or an emulator callback can intervene.

Only disposable pinned Snes9x original CPU source, no guest clock,
controller, ROM, queue or memory writes, and no extra CPU memory-bus calls.
"""
from __future__ import annotations
import argparse
from pathlib import Path

PATH=Path("cpuexec.cpp")
MARK="UR_QA01_RF058_ACTUAL_ORIGINAL_OPCODE_WRAM_DELTA"
PINNED="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
SLOTS=((0x0000,0x20,0x02),(0x0057,0xE2,0x00),
       (0x006F,0x0F,0x00),(0x0083,0x86,0x94))
BEFORE=r"""            /* UR_QA01_RF058_ACTUAL_ORIGINAL_OPCODE_WRAM_DELTA
             * Raw WRAM observations around exactly ONE existing real 65816
             * opcode dispatch. Never read the SNES guest bus a second time.
             * This is an observation of a mutation within the instruction
             * interval, not itself a physical memory write callback. */
            const unsigned ur_rf058_frame = (unsigned)ICPU.Frame;
            const int ur_rf058_on =
                getenv("UR_QA01_RF058_ORIG_BOWL_WRAM") &&
                ur_rf058_frame >= 4686u && ur_rf058_frame <= 4694u;
            const unsigned ur_rf058_addr[4]={0x0000u,0x0057u,0x006fu,0x0083u};
            unsigned ur_rf058_before[4]={0,0,0,0};
            const unsigned ur_rf058_bank = ur_rf058_on ? (unsigned)Registers.PB : 0u;
            const unsigned ur_rf058_pc = ur_rf058_on ? (unsigned)Registers.PCw : 0u;
            const unsigned ur_rf058_op = ur_rf058_on ? (unsigned)Op : 0u;
            const unsigned ur_rf058_a = ur_rf058_on ? (unsigned)Registers.A.W : 0u;
            const unsigned ur_rf058_x = ur_rf058_on ? (unsigned)Registers.X.W : 0u;
            const unsigned ur_rf058_y = ur_rf058_on ? (unsigned)Registers.Y.W : 0u;
            const unsigned ur_rf058_v = ur_rf058_on ? (unsigned)CPU.V_Counter : 0u;
            const int ur_rf058_h = ur_rf058_on ? (int)CPU.Cycles : 0;
            if (ur_rf058_on) {
                static unsigned ur_rf058_beat = 0xffffffffu;
                if (ur_rf058_beat != ur_rf058_frame) {
                    ur_rf058_beat = ur_rf058_frame;
                    fprintf(stderr,"QA01RF058CPUHEART frame=%u v=%u h=%d pc=%02X:%04X\n",
                        ur_rf058_frame,ur_rf058_v,ur_rf058_h,
                        ur_rf058_bank,ur_rf058_pc);
                }
                for (int ur_rf058_i=0;ur_rf058_i<4;++ur_rf058_i)
                    ur_rf058_before[ur_rf058_i] =
                        (unsigned)Memory.RAM[ur_rf058_addr[ur_rf058_i]];
            }
"""
AFTER=r"""            if (ur_rf058_on) {
                static unsigned ur_rf058_rows = 0u;
                for (int ur_rf058_i=0;ur_rf058_i<4;++ur_rf058_i) {
                    const unsigned ur_rf058_old=ur_rf058_before[ur_rf058_i];
                    const unsigned ur_rf058_new=
                        (unsigned)Memory.RAM[ur_rf058_addr[ur_rf058_i]];
                    if (ur_rf058_old==ur_rf058_new) continue;
                    if (++ur_rf058_rows <= 8192u)
                        fprintf(stderr,
                           "QA01RF058OPWRAM seq=%u frame=%u pre_v=%u pre_h=%d pc=%02X:%04X op=%02X a=%04X x=%04X y=%04X post_v=%u post_h=%d nextpc=%02X:%04X addr=7E:%04X old=%02X new=%02X\n",
                           ur_rf058_rows,ur_rf058_frame,
                           ur_rf058_v,ur_rf058_h,
                           ur_rf058_bank,ur_rf058_pc,ur_rf058_op,
                           ur_rf058_a,ur_rf058_x,ur_rf058_y,
                           (unsigned)CPU.V_Counter,(int)CPU.Cycles,
                           (unsigned)Registers.PB,(unsigned)Registers.PCw,
                           ur_rf058_addr[ur_rf058_i],ur_rf058_old,
                           ur_rf058_new);
                    else if (ur_rf058_rows==8193u)
                        fprintf(stderr,"QA01RF058OPWRAM_TRUNCATED\n");
                }
            }
"""

def patch(source:str)->str:
    if MARK in source:
        if source.count(BEFORE)!=1 or source.count(AFTER)!=1 or source.count(PINNED)!=1:
            raise ValueError("RF058 partially installed or altered original CPU patch")
        return source
    if source.count(PINNED)!=1:
        raise ValueError("RF058 requires exact pinned original 65816 dispatcher")
    assembled=BEFORE+PINNED+"\n"+AFTER
    out=source.replace(PINNED,assembled,1)
    if (out.count("(*Opcodes[Op].S9xOpcode)();") !=
            source.count("(*Opcodes[Op].S9xOpcode)();")):
        raise AssertionError("RF058 may not change original 65816 dispatch count")
    if any(fn in assembled for fn in ("S9xGetByte(","S9xGetWord(",
                                     "S9xSetByte(","S9xSetWord(")):
        raise AssertionError("RF058 must not perform SNES memory-bus calls")
    return out

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    target=a.root/PATH
    if not target.is_file():p.error("RF058 pinned original Snes9x core missing")
    old=target.read_text(encoding="utf8")
    new=patch(old)
    if new!=old:target.write_text(new,encoding="utf8")
    print("RF058 actual original opcode-boundary raw WRAM observer",
          "already staged" if new==old else "staged")

if __name__=="__main__":main()

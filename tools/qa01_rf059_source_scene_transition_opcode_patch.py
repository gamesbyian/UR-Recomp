#!/usr/bin/env python3
"""RF059 read-only actual original Snes9x 65816 opcode-boundary next-race WRAM changes.

Watch the *actual next-race persistent state mutation* before/after a genuine source CPU
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
MARK="UR_QA01_RF059_ACTUAL_ORIGINAL_OPCODE_WRAM_DELTA"
PINNED="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
SLOTS=(0x121f,0x126b,0x1277,0x1359,0x135b,0x135d,0x135f,0x2000,0x2002,0x2004,0x2007,0x2008,0x2009,0x2017,0x2018,0x2019,0x2069)
BEFORE=r"""            /* UR_QA01_RF059_ACTUAL_ORIGINAL_OPCODE_WRAM_DELTA
             * Raw WRAM observations around exactly ONE existing real 65816
             * opcode dispatch. Never read the SNES guest bus a second time.
             * This is an observation of a mutation within the instruction
             * interval, not itself a physical memory write callback. */
            const unsigned ur_rf059_frame = (unsigned)ICPU.Frame;
            const int ur_rf059_on =
                getenv("UR_QA01_RF059_ORIG_BOWL_WRAM") &&
                ur_rf059_frame >= 4686u && ur_rf059_frame <= 4694u;
            const unsigned ur_rf059_addr[17]={0x121fu,0x126bu,0x1277u,0x1359u,0x135bu,0x135du,0x135fu,0x2000u,0x2002u,0x2004u,0x2007u,0x2008u,0x2009u,0x2017u,0x2018u,0x2019u,0x2069u};
            unsigned ur_rf059_before[17]={0};
            const unsigned ur_rf059_bank = ur_rf059_on ? (unsigned)Registers.PB : 0u;
            const unsigned ur_rf059_pc = ur_rf059_on ? (unsigned)Registers.PCw : 0u;
            const unsigned ur_rf059_op = ur_rf059_on ? (unsigned)Op : 0u;
            const unsigned ur_rf059_a = ur_rf059_on ? (unsigned)Registers.A.W : 0u;
            const unsigned ur_rf059_x = ur_rf059_on ? (unsigned)Registers.X.W : 0u;
            const unsigned ur_rf059_y = ur_rf059_on ? (unsigned)Registers.Y.W : 0u;
            const unsigned ur_rf059_v = ur_rf059_on ? (unsigned)CPU.V_Counter : 0u;
            const int ur_rf059_h = ur_rf059_on ? (int)CPU.Cycles : 0;
            if (ur_rf059_on) {
                static unsigned ur_rf059_beat = 0xffffffffu;
                if (ur_rf059_beat != ur_rf059_frame) {
                    ur_rf059_beat = ur_rf059_frame;
                    fprintf(stderr,"QA01RF059CPUHEART frame=%u v=%u h=%d pc=%02X:%04X\n",
                        ur_rf059_frame,ur_rf059_v,ur_rf059_h,
                        ur_rf059_bank,ur_rf059_pc);
                }
                for (int ur_rf059_i=0;ur_rf059_i<17;++ur_rf059_i)
                    ur_rf059_before[ur_rf059_i] =
                        (unsigned)Memory.RAM[ur_rf059_addr[ur_rf059_i]];
            }
"""
AFTER=r"""            if (ur_rf059_on) {
                static unsigned ur_rf059_rows = 0u;
                for (int ur_rf059_i=0;ur_rf059_i<17;++ur_rf059_i) {
                    const unsigned ur_rf059_old=ur_rf059_before[ur_rf059_i];
                    const unsigned ur_rf059_new=
                        (unsigned)Memory.RAM[ur_rf059_addr[ur_rf059_i]];
                    if (ur_rf059_old==ur_rf059_new) continue;
                    if (++ur_rf059_rows <= 8192u)
                        fprintf(stderr,
                           "QA01RF059OPWRAM seq=%u frame=%u pre_v=%u pre_h=%d pc=%02X:%04X op=%02X a=%04X x=%04X y=%04X post_v=%u post_h=%d nextpc=%02X:%04X addr=7E:%04X old=%02X new=%02X\n",
                           ur_rf059_rows,ur_rf059_frame,
                           ur_rf059_v,ur_rf059_h,
                           ur_rf059_bank,ur_rf059_pc,ur_rf059_op,
                           ur_rf059_a,ur_rf059_x,ur_rf059_y,
                           (unsigned)CPU.V_Counter,(int)CPU.Cycles,
                           (unsigned)Registers.PB,(unsigned)Registers.PCw,
                           ur_rf059_addr[ur_rf059_i],ur_rf059_old,
                           ur_rf059_new);
                    else if (ur_rf059_rows==8193u)
                        fprintf(stderr,"QA01RF059OPWRAM_TRUNCATED\n");
                }
            }
"""

def patch(source:str)->str:
    if MARK in source:
        if source.count(BEFORE)!=1 or source.count(AFTER)!=1 or source.count(PINNED)!=1:
            raise ValueError("RF059 partially installed or altered original CPU patch")
        return source
    if source.count(PINNED)!=1:
        raise ValueError("RF059 requires exact pinned original 65816 dispatcher")
    assembled=BEFORE+PINNED+"\n"+AFTER
    out=source.replace(PINNED,assembled,1)
    if (out.count("(*Opcodes[Op].S9xOpcode)();") !=
            source.count("(*Opcodes[Op].S9xOpcode)();")):
        raise AssertionError("RF059 may not change original 65816 dispatch count")
    if any(fn in assembled for fn in ("S9xGetByte(","S9xGetWord(",
                                     "S9xSetByte(","S9xSetWord(")):
        raise AssertionError("RF059 must not perform SNES memory-bus calls")
    return out

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    target=a.root/PATH
    if not target.is_file():p.error("RF059 pinned original Snes9x core missing")
    old=target.read_text(encoding="utf8")
    new=patch(old)
    if new!=old:target.write_text(new,encoding="utf8")
    print("RF059 actual original opcode-boundary raw WRAM observer",
          "already staged" if new==old else "staged")

if __name__=="__main__":main()

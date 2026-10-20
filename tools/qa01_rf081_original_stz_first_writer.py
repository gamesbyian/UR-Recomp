#!/usr/bin/env python3
"""RF081: real Snes9x 2014 STZ direct-page setter and completed opcode.

After RF079 original already-fetched opcode/postdispatch instrumentation,
record the EXISTING S9xSetByte invocation while 82:D4F2 (STZ) executes
and the actual physical WRAM byte after the opcode returns. No added guest
bus operation or cycle. Two host labels, 1017 (divergent) and 1018 (control).
"""
from __future__ import annotations
import argparse
from pathlib import Path

import qa01_rf079_original_post_bit_branch as rf079

EXEC = Path("cpuexec.cpp")
GETSET = Path("getset.h")
STAMP = "UR_QA01_RF081_ORIGINAL_STZ_TRUE_WRITE"
HEADER = '#include "movie.h"\n'
BYTE = "inline void S9xSetByte (uint8 Byte, uint32 Address)\n{\n"
PRE = "(*Opcodes[Op].S9xOpcode)();\n"
POST = "\t\t\tur_rf079_original_post_op(ur_rf079_prepc,Op);\n"
HELPER = r'''/* UR_QA01_RF081_ORIGINAL_STZ_TRUE_WRITE
 * The original byte-writer hook is in actual S9xSetByte, before its
 * genuine mapping/commit. The post-dispatch source callback checks the
 * direct WRAM mirror after the true opcode, without an extra guest read.
 * Independent semantic-phase alignment is NOT implied by host labels. */
static unsigned ur_rf081_original_armed;
static unsigned ur_rf081_original_seen;
static uint32 ur_rf081_original_target;
static uint8 ur_rf081_original_byte;
static unsigned long long ur_rf081_original_seq;
static unsigned ur_rf081_original_rows;
static int ur_rf081_original_enabled(void) {
    return getenv("UR_QA01_RF081_ORIGINAL_STZ") &&
      ((unsigned)ICPU.Frame == 1017u || (unsigned)ICPU.Frame == 1018u);
}
static void ur_rf081_original_emit(const char *stage, unsigned addr,
                                   unsigned value, unsigned committed) {
    if (ur_rf081_original_rows++ >= 32768u) {
        if (ur_rf081_original_rows == 32769u)
            fprintf(stderr, "QA01RF081ORIG_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
      "QA01RF081ORIG seq=%llu stage=%s f=%u pc=82D4F2"
      " D=%04X addr=%06X value=%02X committed=%u"
      " v=%u h=%d phase=source_local\n",
      ++ur_rf081_original_seq,stage,(unsigned)ICPU.Frame,
      (unsigned)Registers.D.W,addr,value,committed,
      (unsigned)CPU.V_Counter,(int)CPU.Cycles);
}
static inline void ur_rf081_original_arm(unsigned pc, uint8 opcode) {
    ur_rf081_original_armed =
       ur_rf081_original_enabled() && pc == 0x82D4F2u && opcode == 0x64u;
    ur_rf081_original_seen = 0;
    ur_rf081_original_target = 0;
    ur_rf081_original_byte = 0;
}
void ur_rf081_original_actual_setbyte(uint8 value, uint32 address) {
    if (!ur_rf081_original_armed) return;
    ++ur_rf081_original_seen;
    ur_rf081_original_target=address & 0xffffffu;
    ur_rf081_original_byte=value;
    ur_rf081_original_emit("setbyte_enter",ur_rf081_original_target,value,0);
}
static inline void ur_rf081_original_after_dispatch(unsigned pc, uint8 opcode) {
    if (!ur_rf081_original_armed) return;
    const unsigned addr=(unsigned)((Registers.D.W+0x59u) & 0xffffu);
    /* Host-side direct RAM mirror only, NOT S9xGetByte. A genuine
     * S9xSetByte record must independently qualify this snapshot. */
    ur_rf081_original_emit("after_stz_opcode",addr,
                          (unsigned)Memory.RAM[addr],
                          ur_rf081_original_seen);
    ur_rf081_original_armed=0;
}
'''
GETSET_DECL = 'extern void ur_rf081_original_actual_setbyte(uint8, uint32);\n'

def patch(executor: str, getset: str) -> tuple[str, str]:
    if STAMP in executor or STAMP in getset:
        raise ValueError("RF081 original STZ already or partly staged")
    if rf079.STAMP not in executor or executor.count(POST) != 1:
        raise ValueError("RF081 requires genuine RF079 original post-dispatch source")
    if "UR_QA01_RF063_SOURCE_BUS_CHECKPOINT_SEQUENCE" not in getset:
        raise ValueError("RF081 requires already-qualified original getset")
    if executor.count(HEADER) != 1 or getset.count(BYTE) != 1 or \
       executor.count(PRE) != 1:
        raise ValueError("RF081 original opcode/byte writer structural drift")
    orig_ops = ("S9xSetByte(", "S9xSetWord(", "S9xGetByte(", "S9xGetWord(",
                "(*Opcodes[Op].S9xOpcode)();", "Registers.PCw++;")
    before = tuple(executor.count(x)+getset.count(x) for x in orig_ops)
    executor = executor.replace(HEADER, HEADER+HELPER, 1)
    executor = executor.replace("\t\t\t"+PRE,
        "\t\t\tur_rf081_original_arm(ur_rf079_prepc,Op);\n\t\t\t"+PRE, 1)
    executor = executor.replace(POST,
        POST+"\t\t\tur_rf081_original_after_dispatch(ur_rf079_prepc,Op);\n",1)
    getset = getset.replace(BYTE,
        GETSET_DECL+BYTE+"\tur_rf081_original_actual_setbyte(Byte,Address);\n",1)
    after=tuple(executor.count(x)+getset.count(x) for x in orig_ops)
    if after != before:
        raise AssertionError("RF081 changes an emulated bus/opcode operation")
    if executor.count(STAMP) != 1 or \
       getset.count("ur_rf081_original_actual_setbyte(Byte,Address)") != 1:
        raise AssertionError("RF081 source placement invalid")
    return executor, getset

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True,type=Path)
    args=ap.parse_args()
    root=args.root.resolve()
    ep,gp=root/EXEC,root/GETSET
    if not ep.is_file() or not gp.is_file():
        ap.error("pinned original executor/getset source absent")
    a,b=patch(ep.read_text(),gp.read_text())
    ep.write_text(a)
    gp.write_text(b)
    print("RF081 actual original STZ setter + post-op RAM committed state staged")

if __name__=="__main__":
    main()

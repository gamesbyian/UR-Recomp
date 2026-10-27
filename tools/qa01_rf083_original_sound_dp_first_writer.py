#!/usr/bin/env python3
"""RF083 original Zoo sound DP first opcode/write observer; disposable source only.

Stage on a pinned Snes9x 2014 reference source checkout. Log genuine already-
fetched CPU PC/opcode, direct-RAM mutations, and existing S9xSetByte entries.
Setter entry != proven bus commit; an opcode interval != a physical write.
"""
import argparse
from pathlib import Path

EXEC=Path("cpuexec.cpp")
GETSET=Path("getset.h")
STAMP="UR_QA01_RF083_ZOO_SOUND_DP_FIRST_WRITER"
HEADER='#include "movie.h"\n'
OP="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
BYTE="inline void S9xSetByte (uint8 Byte, uint32 Address)\n{\n"
WORD="inline void S9xSetWord (uint16 Word, uint32 Address, enum s9xwrap_t w = WRAP_NONE, enum s9xwriteorder_t o = WRITE_01)\n{\n"
C=r'''/* UR_QA01_RF083_ZOO_SOUND_DP_FIRST_WRITER */
static int rf083_active;
static unsigned rf083_pc,rf083_op,rf083_frame,rf083_v;
static int rf083_h;
static unsigned rf083_before[4],rf083_seen,rf083_addr,rf083_value;
static unsigned rf083_last_frame=0xffffffffu,rf083_rows;
static unsigned long long rf083_seq;
static unsigned rf083_word_rows;
static const unsigned rf083_slots[4]={0x63u,0x64u,0x65u,0x69u};
static void rf083_print(const char *type,unsigned slot,unsigned old,unsigned now){
    if(++rf083_rows>8192u){
        if(rf083_rows==8193u) fprintf(stderr,"QA01RF083ORIG_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
      "QA01RF083ORIG seq=%llu type=%s frame=%u pc=%06X op=%02X"
      " pre_v=%u pre_h=%d post_v=%u post_h=%d"
      " slot=%04X old=%02X new=%02X setterCount=%u"
      " setterAddr=%06X setterVal=%02X clock=original_cpu\n",
      ++rf083_seq,type,rf083_frame,rf083_pc,rf083_op,rf083_v,rf083_h,
      (unsigned)CPU.V_Counter,(int)CPU.Cycles,rf083_slots[slot],old,now,
      rf083_seen,rf083_addr,rf083_value);
}
static void rf083_pre(uint8 opcode){
    rf083_active=((unsigned)ICPU.Frame>=6069u &&
                  (unsigned)ICPU.Frame<=6079u &&
                  getenv("UR_QA01_RF083_ZOO_DP")!=NULL);
    if(!rf083_active) return;
    rf083_frame=(unsigned)ICPU.Frame;
    rf083_pc=((unsigned)Registers.PB<<16)|(unsigned)Registers.PCw;
    rf083_op=opcode;
    rf083_v=(unsigned)CPU.V_Counter;
    rf083_h=(int)CPU.Cycles;
    rf083_seen=0u;
    rf083_addr=0xffffffffu;
    rf083_value=0u;
    if(rf083_last_frame!=rf083_frame){
        rf083_last_frame=rf083_frame;
        fprintf(stderr,"QA01RF083ORIG_HEART frame=%u v=%u h=%d\n",
                rf083_frame,rf083_v,rf083_h);
    }
    for(unsigned i=0;i<4u;++i)
        rf083_before[i]=(unsigned)Memory.RAM[rf083_slots[i]];
}
/* S9xSetWord may commit WRAM without ever entering S9xSetByte.
 * This entry is NOT proof of commit; post-opcode raw RAM deltas are separate.
 * No additional guest bus read or write is performed. */
void rf083_setword_entry(uint16 word,uint32 address,int wrap,int order){
    if(!rf083_active || rf083_pc!=0x828154u ||
       (address&0xffffu)!=0x0063u) return;
    if(++rf083_word_rows>8192u){
        if(rf083_word_rows==8193u)
            fprintf(stderr,"QA01RF083ORIG_WORD_TRUNCATED\n");
        return;
    }
    unsigned before=(unsigned)Memory.RAM[0x63u] |
                    ((unsigned)Memory.RAM[0x64u]<<8);
    fprintf(stderr,
       "QA01RF083ORIG_WORD seq=%u frame=%u pc=%06X addr=%06X"
       " word=%04X wrap=%d order=%d rawBefore=%04X\n",
       rf083_word_rows,rf083_frame,rf083_pc,(unsigned)(address&0xffffffu),
       (unsigned)word,wrap,order,before);
}
void rf083_setbyte_entry(uint8 value,uint32 address){
    if(!rf083_active) return;
    const unsigned off=(unsigned)(address&0xffffu);
    for(unsigned i=0;i<4u;++i){
        if(off!=rf083_slots[i]) continue;
        ++rf083_seen;
        rf083_addr=(unsigned)(address&0xffffffu);
        rf083_value=value;
        /* BEFORE the existing setter maps/commits this address.
         * Low 16-bit alias alone does NOT prove WRAM mapping. */
        rf083_print("setter_entry",i,rf083_before[i],
                    (unsigned)Memory.RAM[rf083_slots[i]]);
        break;
    }
}
static void rf083_post(void){
    if(!rf083_active) return;
    for(unsigned i=0;i<4u;++i){
        unsigned value=(unsigned)Memory.RAM[rf083_slots[i]];
        if(value!=rf083_before[i])
            rf083_print("opcode_delta",i,rf083_before[i],value);
    }
    rf083_active=0;
}
'''
DECL="extern void rf083_setbyte_entry(uint8,uint32);\n"
WORD_DECL="extern void rf083_setword_entry(uint16,uint32,int,int);\n"

def patch(executor:str,getset:str)->tuple[str,str]:
    if STAMP in executor or STAMP in getset or "rf083_setbyte_entry" in getset:
        raise ValueError("RF083 already or partly staged")
    if executor.count(HEADER)!=1 or executor.count(OP)!=1 or getset.count(BYTE)!=1 or getset.count(WORD)!=1:
        raise ValueError("RF083 pinned opcode or source setter drift")
    if executor.count("Op = CPU.PCBase[Registers.PCw];")!=1 or \
       executor.count("Op = S9xGetByte(Registers.PBPC);")!=1:
        raise ValueError("RF083 genuine fast/slow original opcode fetch absent")
    old=[executor.count(s)+getset.count(s) for s in
         ("(*Opcodes[Op].S9xOpcode)();","Registers.PCw++;",
          "S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")]
    executor=executor.replace(HEADER,HEADER+C,1).replace(
        OP,"\t\t\trf083_pre(Op);\n"+OP+"\n\t\t\trf083_post();",1)
    getset=getset.replace(BYTE,DECL+BYTE+"\trf083_setbyte_entry(Byte,Address);\n",1)
    getset=getset.replace(WORD,WORD_DECL+WORD+
                          "\trf083_setword_entry(Word,Address,(int)w,(int)o);\n",1)
    new=[executor.count(s)+getset.count(s) for s in
         ("(*Opcodes[Op].S9xOpcode)();","Registers.PCw++;",
          "S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")]
    if new!=old:
        raise AssertionError("RF083 must not change genuine guest memory or dispatch calls")
    if (executor.count(STAMP)!=1 or getset.count("rf083_setbyte_entry(Byte,Address);")!=1 or
        getset.count("rf083_setword_entry(Word,Address,(int)w,(int)o);")!=1):
        raise AssertionError("RF083 source injection count")
    return executor,getset

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    x,y=a.root/EXEC,a.root/GETSET
    if not x.is_file() or not y.is_file() or x.is_symlink() or y.is_symlink():
        p.error("missing authentic disposable Snes9x source files")
    xx,yy=patch(x.read_text(),y.read_text())
    x.write_text(xx)
    y.write_text(yy)
    print("RF083 original real setter + opcode DP delta observer staged")

if __name__=="__main__":
    main()

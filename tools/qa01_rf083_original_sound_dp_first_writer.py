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
MACRO=Path("cpumacro.h")
PPU=Path("ppu.cpp")
STAMP="UR_QA01_RF083_ZOO_SOUND_DP_FIRST_WRITER"
HEADER='#include "movie.h"\n'
OP="\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
BYTE="inline void S9xSetByte (uint8 Byte, uint32 Address)\n{\n"
WORD="inline void S9xSetWord (uint16 Word, uint32 Address, enum s9xwrap_t w = WRAP_NONE, enum s9xwriteorder_t o = WRITE_01)\n{\n"
READ_BYTE_FUNC = "inline uint8 S9xGetByte (uint32 Address)\n{\n"
READ_BYTE_PPU = "\t\t\tbyte = S9xGetPPU(Address & 0xffff);\n\t\t\taddCyclesInMemoryAccess;\n\t\t\treturn (byte);"
READ_WORD_PPU = "\t\t\tword  = S9xGetPPU(Address & 0xffff);\n\t\t\taddCyclesInMemoryAccess;\n\t\t\tword |= S9xGetPPU((Address + 1) & 0xffff) << 8;\n\t\t\taddCyclesInMemoryAccess;\n\t\t\treturn (word);"
PPU_ENTRY = "void S9xSetPPU (uint8 Byte, uint16 Address)\n{\n"
PPU_APU = ("\tif ((Address & 0xffc0) == 0x2140) // APUIO0, APUIO1, APUIO2, APUIO3\n"
           "\t\t// write_port will run the APU until given clock before writing value\n"
           "\t\tS9xAPUWritePort(Address & 3, Byte);")
PPU_DECL = "extern void rf083_port_write(uint32,unsigned);\n"
PPU_STAMP = "UR_QA01_RF091_ORIGINAL_APU_WRITE"
C=r'''/* UR_QA01_RF083_ZOO_SOUND_DP_FIRST_WRITER */
static int rf083_active,rf083_early;
static unsigned rf083_pc,rf083_op,rf083_frame,rf083_v;
static int rf083_h;
static unsigned rf083_before[4],rf083_seen,rf083_addr,rf083_value;
static unsigned rf083_last_frame=0xffffffffu,rf083_rows;
static unsigned rf083_early_last_frame=0xffffffffu,rf083_early_rows;
static unsigned long long rf083_early_seq;
static unsigned long long rf083_seq;
static unsigned rf083_word_rows;
static unsigned rf083_inc16_rows;
/* RF089: optional original opcode/branch witness for the last Zoo seek to
 * first sound-data increment. No extra APU bus reads, guest writes or ticks.
 * CMP live Z comes from ICPU._Zero, not the lazily packed Registers.PL.
 * Live Z plus the following BNE next PC reveal echo retry outcomes,
 * but RF089 alone cannot disclose the actual returned SPC port byte;
 * RF090 below separately records actual already-returned PPU reads. */
static unsigned rf089_rows, rf089_a0, rf089_p0, rf089_z0;
static unsigned rf090_rows;
static unsigned rf091_rows;
/* RF092 reads the original frame through this CPU-TU accessor. Keep the
 * Bapu SMP translation unit independent of CPU execution/getset headers. */
unsigned rf083_original_frame(void){ return (unsigned)ICPU.Frame; }
static int rf089_target;
static const unsigned rf083_slots[4]={0x63u,0x64u,0x65u,0x69u};
static void rf083_print(const char *type,unsigned slot,unsigned old,unsigned now){
    unsigned *rows=rf083_early ? &rf083_early_rows : &rf083_rows;
    unsigned long long *seq=rf083_early ? &rf083_early_seq : &rf083_seq;
    const char *prefix=rf083_early ? "QA01RF085EARLY" : "QA01RF083ORIG";
    /* Real Zoo #40487975108 exceeded 8192 early rows by frame 6062.
     * Keep late RF083 at its proven 8192 cap; bound the distinct early
     * 6051..6065 source window at 16384 without dropping +5040 evidence. */
    const unsigned budget=rf083_early ? 16384u : 8192u;
    if(++*rows>budget){
        if(*rows==budget+1u){
            if(rf083_early)
                fprintf(stderr,"QA01RF085EARLY_TRUNCATED\n");
            else
                fprintf(stderr,"QA01RF083ORIG_TRUNCATED\n");
        }
        return;
    }
    fprintf(stderr,
      "%s seq=%llu type=%s frame=%u pc=%06X op=%02X"
      " pre_v=%u pre_h=%d post_v=%u post_h=%d"
      " slot=%04X old=%02X new=%02X setterCount=%u"
      " setterAddr=%06X setterVal=%02X clock=original_cpu\n",
      prefix,++*seq,type,rf083_frame,rf083_pc,rf083_op,rf083_v,rf083_h,
      (unsigned)CPU.V_Counter,(int)CPU.Cycles,rf083_slots[slot],old,now,
      rf083_seen,rf083_addr,rf083_value);
}
static void rf083_pre(uint8 opcode){
    const unsigned frame=(unsigned)ICPU.Frame;
    const int in_window=(frame>=6051u && frame<=6065u) ||
                        (frame>=6069u && frame<=6079u);
    const int enabled=in_window && getenv("UR_QA01_RF083_ZOO_DP")!=NULL;
    /* Original internal 6051..6065 covers Zoo +5034..+5048.
     * Retain the existing 6069..6079 writer stream separately. */
    rf083_early=enabled && frame>=6051u && frame<=6065u;
    rf083_active=enabled;
    if(!rf083_active) return;
    rf083_frame=(unsigned)ICPU.Frame;
    rf083_pc=((unsigned)Registers.PB<<16)|(unsigned)Registers.PCw;
    rf083_op=opcode;
    const char *rf089_flag=getenv("UR_QA01_RF089_ORIGINAL_ECHO");
    /* The genuine original log reports 82:8154, not 02:8154:
     * FastROM bank 82 mirrors bank 02. Preserve the full logged PC,
     * but compare the mirrored low 23 bits for echo opcode selection.
     * Do not preselect C6B0: the failed sequence-10 run logged zero
     * original echo rows and the true entry phase is still unknown. */
    const unsigned rf089_pc_mirrored=rf083_pc & 0x7fffffu;
    rf089_target=rf083_early && frame>=6054u && frame<=6059u &&
        rf089_flag && rf089_flag[0]=='1' && rf089_flag[1]=='\0' &&
        /* Zoo's executed Snd_UploadBlock uses 80DB CMP $2140 and
         * 80DE BNE; 8301/8304 belong to the separate block-list path. */
        (rf089_pc_mirrored==0x0280CEu || rf089_pc_mirrored==0x0280DBu ||
         rf089_pc_mirrored==0x0280DEu || rf089_pc_mirrored==0x0282A9u ||
         rf089_pc_mirrored==0x0282F2u || rf089_pc_mirrored==0x0282F6u ||
         rf089_pc_mirrored==0x028301u || rf089_pc_mirrored==0x028304u);
    if(rf089_target){
        rf089_a0=(unsigned)Registers.A.W;
        rf089_p0=(unsigned)Registers.PL; /* packed PL may be stale */
        rf089_z0=(unsigned)(ICPU._Zero==0);
    }
    rf083_v=(unsigned)CPU.V_Counter;
    rf083_h=(int)CPU.Cycles;
    rf083_seen=0u;
    rf083_addr=0xffffffffu;
    rf083_value=0u;
    if(rf083_early){
        if(rf083_early_last_frame!=rf083_frame){
            rf083_early_last_frame=rf083_frame;
            fprintf(stderr,"QA01RF085EARLY_HEART frame=%u v=%u h=%d\n",
                    rf083_frame,rf083_v,rf083_h);
        }
    } else if(rf083_last_frame!=rf083_frame){
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
    if(!rf083_active || rf083_early || rf083_pc!=0x828154u ||
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
/* Direct original INC16 opcode witness. The getset.h S9xSetWord hook
 * produced zero entries in genuine Zoo #40468773946 despite 1,481 raw
 * low-pointer opcode deltas. Capture the actual INC16 caller before and
 * after its existing S9xSetWord without an additional guest bus operation.
 * The call-site watch is captured before AddCycles can process H-events. */
unsigned rf083_inc16_watch(uint32 address){
    return rf083_active && !rf083_early && rf083_pc==0x828154u;
}
void rf083_inc16_commit(uint32 address,uint16 supplied,int wrap,unsigned before){
    if(++rf083_inc16_rows>8192u){
        if(rf083_inc16_rows==8193u)
            fprintf(stderr,"QA01RF083ORIG_INC16_TRUNCATED\n");
        return;
    }
    const unsigned after=(unsigned)Memory.RAM[0x63u] |
                         ((unsigned)Memory.RAM[0x64u]<<8);
    fprintf(stderr,
      "QA01RF083ORIG_INC16 seq=%u frame=%u pc=%06X addr=%06X"
      " wrap=%d old=%04X supplied=%04X rawAfter=%04X\n",
      rf083_inc16_rows,rf083_frame,rf083_pc,(unsigned)(address&0xffffffu),
      wrap,before,(unsigned)supplied,after);
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
/* RF090: actual returned original Snes9x APU port reads, not inferred
 * CMP/branch values. Observe the existing PPU-mapped read *after* its
 * real bus access and cycle charge, without an additional guest read.
 * Original frame/PC/pointer are not cross-core clock alignment. */
void rf083_port_read(uint32 address,unsigned width,unsigned value){
    if(!rf083_active || !rf083_early ||
       rf083_frame<6054u || rf083_frame>6059u) return;
    const char *flag=getenv("UR_QA01_RF089_ORIGINAL_ECHO");
    if(!flag || flag[0]!='1' || flag[1]!='\0') return;
    const unsigned port=(unsigned)(address & 0xffffu);
    if(port<0x2140u || port>0x2143u) return;
    if(++rf090_rows>32768u){
        if(rf090_rows==32769u)
            fprintf(stderr,"QA01RF090ORIG_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
      "QA01RF090ORIG seq=%u frame=%u pc=%06X op=%02X"
      " addr=%04X width=%u val=%04X v=%u h=%d"
      " ptr=%02X%02X clock=original_cpu\n",
      rf090_rows,rf083_frame,rf083_pc,rf083_op,port,width,value,
      (unsigned)CPU.V_Counter,(int)CPU.Cycles,
      (unsigned)Memory.RAM[0x64u],(unsigned)Memory.RAM[0x63u]);
}
/* RF091: observe the actual original CPU-to-APU command write after the
 * existing S9xAPUWritePort synchronizes the SPC and writes its port.
 * No extra bus operation, no inferred cross-core clock alignment. */
void rf083_port_write(uint32 address,unsigned value){
    if(!rf083_active || !rf083_early ||
       rf083_frame<6054u || rf083_frame>6059u) return;
    const char *flag=getenv("UR_QA01_RF089_ORIGINAL_ECHO");
    if(!flag || flag[0]!='1' || flag[1]!='\0') return;
    if(++rf091_rows>4096u){
        if(rf091_rows==4097u)
            fprintf(stderr,"QA01RF091ORIG_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
      "QA01RF091ORIG seq=%u frame=%u pc=%06X op=%02X"
      " addr=%04X val=%02X v=%u h=%d ptr=%02X%02X"
      " clock=original_cpu post_apu_write=1\n",
      rf091_rows,rf083_frame,rf083_pc,rf083_op,
      0x2140u | (unsigned)(address & 3u),value & 0xffu,
      (unsigned)CPU.V_Counter,(int)CPU.Cycles,
      (unsigned)Memory.RAM[0x64u],(unsigned)Memory.RAM[0x63u]);
}
static void rf083_post(void){
    if(!rf083_active) return;
    if(rf089_target){
        if(++rf089_rows<=32768u){
            fprintf(stderr,
              "QA01RF089ORIG seq=%u frame=%u pc=%06X op=%02X"
              " pre_v=%u pre_h=%d post_v=%u post_h=%d"
              " a0=%04X a1=%04X pl0=%02X pl1=%02X z0=%u z1=%u"
              " next=%06X ptr=%02X%02X clock=original_cpu\n",
              rf089_rows,rf083_frame,rf083_pc,rf083_op,
              rf083_v,rf083_h,(unsigned)CPU.V_Counter,(int)CPU.Cycles,
              rf089_a0,(unsigned)Registers.A.W,
              rf089_p0,(unsigned)Registers.PL,
              rf089_z0,(unsigned)(ICPU._Zero==0),
              ((unsigned)Registers.PB<<16)|(unsigned)Registers.PCw,
              (unsigned)Memory.RAM[0x64u],(unsigned)Memory.RAM[0x63u]);
        } else if(rf089_rows==32769u){
            fprintf(stderr,"QA01RF089ORIG_TRUNCATED\n");
        }
    }
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
PORT_DECL="extern void rf083_port_read(uint32,unsigned,unsigned);\n"

MACRO_INC16 = """static inline void INC16 (uint32 OpAddress, s9xwrap_t w)
{
\tuint16\tWork16 = S9xGetWord(OpAddress, w) + 1;
\tAddCycles(ONE_CYCLE);
\tS9xSetWord(Work16, OpAddress, w, WRITE_10);
\tOpenBus = Work16 & 0xff;
\tSetZN(Work16);
}"""
MACRO_DECL = ("extern unsigned rf083_inc16_watch(uint32);\n"
              "extern void rf083_inc16_commit(uint32,uint16,int,unsigned);\n")

def patch_macro(macro: str) -> str:
    if "rf083_inc16_watch" in macro or macro.count(MACRO_INC16) != 1:
        raise ValueError("RF083 original INC16 source drift or already staged")
    changed = MACRO_INC16.replace(
        "\tAddCycles(ONE_CYCLE);",
        "\tconst unsigned rf083_watch = rf083_inc16_watch(OpAddress);\n"
        "\tconst unsigned rf083_before = rf083_watch ?\n"
        "\t    ((unsigned)Memory.RAM[0x63u] |\n"
        "\t     ((unsigned)Memory.RAM[0x64u] << 8)) : 0u;\n"
        "\tAddCycles(ONE_CYCLE);").replace(
        "\tOpenBus = Work16 & 0xff;",
        "\tif (rf083_watch) rf083_inc16_commit(OpAddress, Work16, (int)w, rf083_before);\n"
        "\tOpenBus = Work16 & 0xff;")
    result = macro.replace(MACRO_INC16, MACRO_DECL + changed, 1)
    if (result.count("rf083_inc16_commit(OpAddress, Work16") != 1 or
            result.count("S9xSetWord(Work16, OpAddress, w, WRITE_10);") !=
            macro.count("S9xSetWord(Work16, OpAddress, w, WRITE_10);")):
        raise AssertionError("RF083 INC16 must preserve the existing guest write")
    return result

def patch(executor:str,getset:str)->tuple[str,str]:
    if STAMP in executor or STAMP in getset or "rf083_setbyte_entry" in getset:
        raise ValueError("RF083 already or partly staged")
    if (executor.count(HEADER)!=1 or executor.count(OP)!=1 or
            getset.count(BYTE)!=1 or getset.count(WORD)!=1 or
            getset.count(READ_BYTE_FUNC)!=1 or getset.count(READ_BYTE_PPU)!=1 or getset.count(READ_WORD_PPU)!=1):
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
    # Declare the observer before both inline reader definitions. The pinned
    # getset.h defines readers before S9xSetByte; a setter-local declaration
    # would leave both RF090 calls undeclared under C++11.
    getset=getset.replace(READ_BYTE_FUNC,PORT_DECL+READ_BYTE_FUNC,1)
    # Capture the actual returned PPU byte/word after the existing bus
    # access and cycle charge, without adding a second S9xGetPPU call.
    getset=getset.replace(READ_BYTE_PPU, READ_BYTE_PPU.replace(
        "\t\t\treturn (byte);",
        "\t\t\trf083_port_read(Address,1u,(unsigned)byte);\n\t\t\treturn (byte);"),1)
    getset=getset.replace(READ_WORD_PPU, READ_WORD_PPU.replace(
        "\t\t\treturn (word);",
        "\t\t\trf083_port_read(Address,2u,(unsigned)word);\n\t\t\treturn (word);"),1)
    new=[executor.count(s)+getset.count(s) for s in
         ("(*Opcodes[Op].S9xOpcode)();","Registers.PCw++;",
          "S9xGetByte(","S9xSetByte(","S9xGetWord(","S9xSetWord(")]
    if new!=old:
        raise AssertionError("RF083 must not change genuine guest memory or dispatch calls")
    if (executor.count(STAMP)!=1 or getset.count("rf083_setbyte_entry(Byte,Address);")!=1 or
        getset.count("rf083_setword_entry(Word,Address,(int)w,(int)o);")!=1):
        raise AssertionError("RF083 source injection count")
    return executor,getset

def patch_ppu(ppu: str) -> str:
    """Observe actual original $2140-$2143 writes in disposable PPU source."""
    if PPU_STAMP in ppu or "rf083_port_write(" in ppu:
        raise ValueError("RF091 original PPU observer already staged")
    if ppu.count(PPU_ENTRY) != 1 or ppu.count(PPU_APU) != 1:
        raise ValueError("RF091 pinned original PPU port writer drift")
    changed = PPU_APU.replace(
        "\t\tS9xAPUWritePort(Address & 3, Byte);",
        "\t{\n\t\tS9xAPUWritePort(Address & 3, Byte);\n"
        "\t\trf083_port_write(Address, (unsigned)Byte);\n\t}")
    result = ppu.replace(PPU_ENTRY, PPU_DECL + PPU_ENTRY, 1)
    result = result.replace(PPU_APU, changed + " // " + PPU_STAMP, 1)
    if (result.count("S9xAPUWritePort(") != ppu.count("S9xAPUWritePort(") or
            result.count("rf083_port_write(Address, (unsigned)Byte);") != 1 or
            result.index(PPU_DECL) > result.index(PPU_ENTRY)):
        raise AssertionError("RF091 must preserve original PPU/APU write count")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    x,y,z,ppu_path=a.root/EXEC,a.root/GETSET,a.root/MACRO,a.root/PPU
    if (not x.is_file() or not y.is_file() or not z.is_file() or not ppu_path.is_file() or
            x.is_symlink() or y.is_symlink() or z.is_symlink() or ppu_path.is_symlink()):
        p.error("missing authentic disposable Snes9x source files")
    xx,yy=patch(x.read_text(),y.read_text())
    zz=patch_macro(z.read_text())
    pp=patch_ppu(ppu_path.read_text())
    x.write_text(xx)
    y.write_text(yy)
    z.write_text(zz)
    ppu_path.write_text(pp)
    print("RF083/RF090/RF091 original setter, returned port reads and committed APU writes staged")

if __name__=="__main__":
    main()

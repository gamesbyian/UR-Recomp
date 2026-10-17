#!/usr/bin/env python3
"""RF044: actual Snes9x/native Zoo stack bus access and NMI witnesses.

Source-qualified disposable guests only, frame 1017..1025. Original Snes9x
real GetByte/GetWord/SetByte/SetWord access functions and non-opcode NMI;
native Baldosa real cpu_read8/16 and already-existing all-path WRAM writer
logger (cpu, indirect, DMA). No extra bus calls, no new stack operations.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ENV = "UR_QA01_RF044_STACK_BUS"
STAMP = "UR_QA01_RF044_STACK_BUS"
ORIG_HEADER=Path("getset.h")
ORIG_CPU=Path("cpuexec.cpp")
NATIVE_CPU=Path("snesrecomp/runner/src/cpu_state.c")

ORIG_FUNC=[
("inline uint8 S9xGetByte (uint32 Address)\n{\n", "rb", "Memory.RAM[Address & 0xffff]", "1"),
("inline uint16 S9xGetWord (uint32 Address, enum s9xwrap_t w = WRAP_NONE)\n{\n", "rw", "Memory.RAM[Address & 0xffff] | ((uint16)Memory.RAM[(Address + 1) & 0xffff] << 8)", "2"),
("inline void S9xSetByte (uint8 Byte, uint32 Address)\n{\n", "wb", "Byte", "1"),
("inline void S9xSetWord (uint16 Word, uint32 Address, enum s9xwrap_t w = WRAP_NONE, enum s9xwriteorder_t o = WRITE_01)\n{\n", "ww", "Word", "2")
]
ORIG_HELPER=r"""/* UR_QA01_RF044_STACK_BUS: genuine Snes9x bus function entry, observation
 * only. For WRAM stack mapping these sampled RAM bytes are the addressed data.
 * Logged reads are attempts at the true helper; not proof of subsequent use. */
static inline void ur_rf044_orig_bus(const char *kind, uint32 address,
                                     uint16 value, unsigned width) {
    if (!getenv("UR_QA01_RF044_STACK_BUS") ||
        (unsigned)ICPU.Frame < 1017u || (unsigned)ICPU.Frame > 1025u)
        return;
    unsigned bank=(unsigned)((address >> 16) & 0xffu);
    unsigned off=(unsigned)(address & 0xffffu);
    if (off > 0x01f1u || off + width - 1u < 0x01edu)
        return;
    if (!((bank==0x7eu) || (((bank & 0x7fu)<0x40u) && off<0x2000u)))
        return;
    static unsigned rows;
    if (rows++ < 8192u)
        fprintf(stderr,
            "QA01RF044ORIGBUS f=%u v=%u h=%d kind=%s bank=%02X addr=%04X w=%u value=%04X pb=%02X pc=%04X S=%04X\n",
            (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, (int)CPU.Cycles,
            kind,bank,off,width,(unsigned)value,(unsigned)Registers.PB,
            (unsigned)Registers.PCw,(unsigned)Registers.S.W);
    else if (rows==8193u)
        fprintf(stderr,"QA01RF044ORIGBUS_TRUNCATED\n");
}

"""
NMI_OLD="\t\t\t\tS9xOpcode_NMI();"
NMI_NEW=r"""                /* UR_QA01_RF044_STACK_BUS: real non-opcode NMI entry. */
                const bool rf044_nmi=getenv("UR_QA01_RF044_STACK_BUS") &&
                     (unsigned)ICPU.Frame>=1017u && (unsigned)ICPU.Frame<=1025u;
                const unsigned rf044_s0=(unsigned)Registers.S.W;
                const unsigned rf044_p0=((unsigned)Registers.PB<<16)|(unsigned)Registers.PCw;
                const unsigned rf044_f0=(unsigned)ICPU.Frame;
                const uint8 rf044_b0[5]={
                     Memory.RAM[0x01ed],Memory.RAM[0x01ee],Memory.RAM[0x01ef],
                     Memory.RAM[0x01f0],Memory.RAM[0x01f1]};
                S9xOpcode_NMI();
                if(rf044_nmi)
                    fprintf(stderr,
                       "QA01RF044ORIGNMI f=%u f1=%u pc=%06X S0=%04X S1=%04X"
                       " old=%02X%02X%02X%02X%02X new=%02X%02X%02X%02X%02X\n",
                       rf044_f0,(unsigned)ICPU.Frame,rf044_p0,rf044_s0,
                       (unsigned)Registers.S.W,
                       (unsigned)rf044_b0[0],(unsigned)rf044_b0[1],
                       (unsigned)rf044_b0[2],(unsigned)rf044_b0[3],
                       (unsigned)rf044_b0[4],
                       (unsigned)Memory.RAM[0x01ed],(unsigned)Memory.RAM[0x01ee],
                       (unsigned)Memory.RAM[0x01ef],(unsigned)Memory.RAM[0x01f0],
                       (unsigned)Memory.RAM[0x01f1]);"""

# RF035 and RF037 were previously installed in this exact native guest.
# Retain both actual observers and the original CPU bus return exactly once.
import qa01_rf037_sound_transaction_window as rf037
NATIVE_READ_8="""    if (off >= 0) {
        uint8 value = cpu->ram[off];
        ur_qa01_rf035_read(cpu, bank, addr, value, 1);
    ur_qa01_rf037_ptr(cpu, bank, addr, value, 1);
        return cpu_latch_read8(cpu, value);
    }
"""
NATIVE_READ_8_NEW=NATIVE_READ_8.replace(
    "        return cpu_latch_read8",
    "        ur_rf044_native_read(cpu,bank,addr,value,1);\n"
    "        return cpu_latch_read8",1)
NATIVE_READ_16="""        ur_qa01_rf035_read(cpu, bank, addr,
                            (uint16)lo | ((uint16)hi << 8), 2);
        ur_qa01_rf037_ptr(cpu, bank, addr,
                            (uint16)lo | ((uint16)hi << 8), 2);
        return cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8));
"""
NATIVE_READ_16_NEW=NATIVE_READ_16.replace(
    "        return cpu_latch_read16",
    "        ur_rf044_native_read(cpu,bank,addr,\n"
    "                            (uint16)lo | ((uint16)hi << 8),2);\n"
    "        return cpu_latch_read16",1)
NATIVE_WRITER_END="""    fputc('\\n', g_wlog_addr_fp);
    if (g_wlog_halt_off >= 0) {
"""
NATIVE_WRITER_END_NEW="""    /* UR_QA01_RF044_STACK_BUS: native original writer journal, no
     * diagnostic reads that might impersonate actual guest consumers. */
    if (getenv("UR_QA01_RF044_STACK_BUS"))
        fprintf(g_wlog_addr_fp," rf044_S=%04X IPC=%06X",
                (unsigned)g_cpu.S,(unsigned)(g_interp816_cur_pc & 0xffffffu));
    fputc('\\n', g_wlog_addr_fp);
    if (g_wlog_halt_off >= 0) {
"""
NATIVE_HEADER="extern Snes *g_snes;\n"
NATIVE_HELPER=r"""/* UR_QA01_RF044_STACK_BUS: actual native WRAM helper reads, including
 * word calls that bypass cpu_read8. Writer truth is the existing all-path
 * wlog_addr_note_via journal, filtered to host1017..1025 before capacity. */
static void ur_rf044_native_read(CpuState *cpu,uint8 bank,uint16 addr,
                                uint16 value,unsigned width) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    if (!getenv("UR_QA01_RF044_STACK_BUS") ||
        snes_frame_counter < 1017 || snes_frame_counter > 1025 ||
        addr>0x01f1u || (unsigned)addr+width-1u<0x01edu)
        return;
    static unsigned rows;
    if (rows++ < 8192u)
        fprintf(stderr,
           "QA01RF044NATIVEREAD f=%d kind=r%u bank=%02X addr=%04X value=%04X"
           " S=%04X IPC=%06X scope=%s\n",
           snes_frame_counter,width,(unsigned)bank,(unsigned)addr,
           (unsigned)value,(unsigned)cpu->S,
           (unsigned)(g_interp816_cur_pc & 0xffffffu),
           g_last_recomp_func ? g_last_recomp_func : "?");
    else if (rows==8193u)
        fprintf(stderr,"QA01RF044NATIVEREAD_TRUNCATED\n");
}
"""

def once(src:str,old:str,new:str,label:str)->str:
    if src.count(old)!=1:
        raise ValueError("RF044 missing/ambiguous source "+label)
    return src.replace(old,new,1)

def original_getset(src:str)->str:
    if STAMP in src:
        if src.count(ORIG_HELPER)!=1:raise ValueError("RF044 partial original getset")
        return src
    before=src.count("S9xGetByte(")+src.count("S9xSetByte(")
    src=once(src,ORIG_FUNC[0][0],ORIG_HELPER+ORIG_FUNC[0][0],"original getset helper")
    for marker,kind,value,width in ORIG_FUNC:
        src=once(src,marker,marker+f'    ur_rf044_orig_bus("{kind}",Address,{value},{width});\n',
                 "original "+kind)
    if src.count("S9xGetByte(")+src.count("S9xSetByte(")!=before:
        raise ValueError("RF044 duplicated original guest bus calls")
    return src

def original_cpu(src:str)->str:
    if STAMP in src:
        if src.count(NMI_NEW)!=1:raise ValueError("RF044 partial original NMI")
        return src
    return once(src,NMI_OLD,NMI_NEW,"original NMI entry")

def native_cpu(src:str)->str:
    if STAMP in src:
        if src.count(NATIVE_HELPER)!=1:raise ValueError("RF044 partial native reader")
        return src
    src=once(src,NATIVE_HEADER,NATIVE_HEADER+NATIVE_HELPER,"native declarations")
    for a,b,name in ((NATIVE_READ_8,NATIVE_READ_8_NEW,"native read8"),
                     (NATIVE_READ_16,NATIVE_READ_16_NEW,"native read16"),
                     (NATIVE_WRITER_END,NATIVE_WRITER_END_NEW,"native WRAM writer")):
        src=once(src,a,b,name)
    return src

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("side",choices=("original","native"))
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    ops=((ORIG_HEADER,original_getset),(ORIG_CPU,original_cpu)) if a.side=="original" else ((NATIVE_CPU,native_cpu),)
    prepared=[]
    for path,patch in ops:
        file=a.root.resolve()/path
        if not file.is_file():p.error("missing original/native source "+str(file))
        before=file.read_text(encoding="utf8")
        prepared.append((file,before,patch(before)))
    for file,before,after in prepared:
        if before!=after:file.write_text(after,encoding="utf8")
        print("RF044",file,"unchanged" if before==after else "read-only source witness staged")

if __name__=="__main__":main()

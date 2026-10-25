#!/usr/bin/env python3
"""RF084: real generated native 8/16-bit Zoo sound-DP write completions.

Patch one disposable, pinned Baldosa src/gen/bank82_part00_v2.c *after* native
regeneration and before its normal compilation. Never alter shipping sources,
memory helpers, original emulator, clock account or controller inputs.
"""
import argparse
from pathlib import Path

FILE=Path("src/gen/bank82_part00_v2.c")
STAMP="UR_QA01_RF084_NATIVE_SOUND_DP_COMMIT"
HEADER='#include "funcs.h"\n'
COUNTER='RecompReturn Snd_UploadBlock_M0X0(CpuState *cpu) {'
POINTER='RecompReturn Snd_IncDataPtr_FastRom_M1X0(CpuState *cpu) {'
COUNTER_LABEL="  L_80E0_M1X0:\n"
POINTER_LABEL="  L_8151_M1X0:\n"
COUNTER_WRITE='      cpu_write8_paced(cpu, 0x00, (uint16)(cpu->D + 0x0069), _im);\n'
POINTER_WRITE='      cpu_write16_paced(cpu, 0x00, (uint16)(cpu->D + 0x0063), _im);\n'
HOOK=r'''/* UR_QA01_RF084_NATIVE_SOUND_DP_COMMIT
 * Only called AFTER a real generated M1X0 paced write RETURNS. The caller
 * snapshots raw memory before the existing write. This does not execute a
 * second SNES write/read, charge a guest clock or mark original/native
 * semantic-phase equivalence. Whole-WRAM raw parity is independently tested.
 */
extern int snes_frame_counter;
static unsigned ur_rf084_rows;
static void ur_rf084_after(CpuState *cpu, unsigned pc, unsigned width,
                           uint16 addr, uint16 old, uint16 value) {
    const char *flag=getenv("UR_QA01_RF084_NATIVE_SOUND_DP");
    if(!flag || !*flag || snes_frame_counter<6054 ||
       snes_frame_counter>6068) return;
    if(++ur_rf084_rows>10000u) {
        if(ur_rf084_rows==10001u)
            fprintf(stderr,"QA01RF084NATIVE_TRUNCATED\n");
        return;
    }
    unsigned now=(unsigned)cpu->ram[addr];
    if(width==2u)
        now|=(unsigned)cpu->ram[(uint16)(addr+1u)]<<8;
    fprintf(stderr,
       "QA01RF084NATIVE seq=%u site=%06X width=%u variant=M1X0"
       " f=%d D=%04X addr=%04X old=%04X supplied=%04X rawAfter=%04X"
       " native_master=%llu\n",
       ur_rf084_rows,pc,width,snes_frame_counter,(unsigned)cpu->D,
       (unsigned)addr,(unsigned)old,(unsigned)value,now,
       (unsigned long long)cpu->master_cycles);
}
'''
COUNTER_INSERT=(
'      uint16 ur_rf084_addr=(uint16)(cpu->D + 0x0069);\n'
'      uint16 ur_rf084_pre=(uint16)cpu->ram[ur_rf084_addr];\n'
+COUNTER_WRITE+
'      ur_rf084_after(cpu,0x8280E0u,1u,ur_rf084_addr,ur_rf084_pre,(uint16)_im);\n')
POINTER_INSERT=(
'      uint16 ur_rf084_addr=(uint16)(cpu->D + 0x0063);\n'
'      uint16 ur_rf084_pre=(uint16)cpu->ram[ur_rf084_addr]\n'
'          | ((uint16)cpu->ram[(uint16)(ur_rf084_addr+1u)]<<8);\n'
+POINTER_WRITE+
'      ur_rf084_after(cpu,0x828154u,2u,ur_rf084_addr,ur_rf084_pre,_im);\n')

def instrument_function(text: str, name: str, marker: str,
                        source: str, replacement: str) -> str:
    if text.count(name)!=1:
        raise ValueError("RF084 pinned native generated function absent/ambiguous: "+name)
    begin=text.index(name)
    end=text.find("\nRecompReturn ", begin+len(name))
    if end<0:
        raise ValueError("RF084 expected next generated function")
    body=text[begin:end]
    if body.count(marker)!=1 or body.count(source)!=1:
        raise ValueError("RF084 real M1X0 decoded opcode/physical write callsite drift")
    # A single source write operation, with recorded pre/post raw memory
    # and no new CPU helper or direct guest bus accesses.
    return text[:begin]+body.replace(source,replacement,1)+text[end:]

def patch(text: str) -> str:
    if STAMP in text or "ur_rf084_after" in text:
        raise ValueError("RF084 native generated file already or partly patched")
    if text.count(HEADER)!=1:
        raise ValueError("RF084 genuine generated header drift")
    old=tuple(text.count(x) for x in
              ("cpu_read8_paced(", "cpu_read16_paced(",
               "cpu_write8_paced(", "cpu_write16_paced("))
    text=text.replace(HEADER,HEADER+HOOK,1)
    text=instrument_function(text,COUNTER,COUNTER_LABEL,
                             COUNTER_WRITE,COUNTER_INSERT)
    text=instrument_function(text,POINTER,POINTER_LABEL,
                             POINTER_WRITE,POINTER_INSERT)
    new=tuple(text.count(x) for x in
              ("cpu_read8_paced(", "cpu_read16_paced(",
               "cpu_write8_paced(", "cpu_write16_paced("))
    if old!=new:
        raise AssertionError("RF084 changed native actual guest helper call population")
    if text.count(STAMP)!=1 or text.count("ur_rf084_after(cpu,")!=2:
        raise AssertionError("RF084 actual commit site count changed")
    return text

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True,type=Path,
                    help="disposable pinned native root, after genuine regeneration")
    args=ap.parse_args()
    path=args.root/FILE
    if not path.is_file() or path.is_symlink():
        ap.error("actual generated native M1X0 bank 82 C file missing")
    patched=patch(path.read_text(encoding="utf8"))
    path.write_text(patched,encoding="utf8")
    print("RF084 generated native actual 8/16-bit sound-DP write-return hooks staged")

if __name__=="__main__":
    main()

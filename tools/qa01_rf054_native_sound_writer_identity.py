#!/usr/bin/env python3
"""RF054: native actual CPU sound publication and operand address candidates.

Disposable pinned Baldosa source only, after RF037 upstream and RF052.
RtlApuWrite is the one real CPU->APU publication (after existing filter).
cpu_read8/16 are actual bus helper invocations; RomPtr is a *ROM mapping
request*, NOT necessarily proof that generated AOT dereferenced it.
Nothing adds a CPU, SPC or ROM read, queue write, gameplay execution, input,
timing change or direct ROM dereference.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK="UR_QA01_RF054_NATIVE_SOUND_WRITER"
COMMON=Path("snesrecomp/runner/src/common_rtl.c")
CPU=Path("snesrecomp/runner/src/cpu_state.c")
COMMON_ROM_HEADER="uint8 *RomPtr(uint32_t addr) {\n  uint8_t bank = (uint8_t)(addr >> 16);\n  uint16_t lo = (uint16_t)addr;\n"
COMMON_APU_HEADER="void RtlApuWrite(uint16 adr, uint8 val) {\n"
COMMON_APU_SLOT="  uint8_t port = (uint8_t)(adr & 3);\n"
CPU_BYTE_HEADER="uint8 cpu_read8(CpuState *cpu, uint8 bank, uint16 addr) {\n"
CPU_WORD_HEADER="uint16 cpu_read16(CpuState *cpu, uint8 bank, uint16 addr) {\n"

COMMON_HELPER=r"""/* UR_QA01_RF054_NATIVE_SOUND_WRITER: read-only CPU/AOT source scope.
 * Direct g_cpu.ram slots are an observational snapshot, never new bus calls.
 * ROM mapping requests MUST NOT be promoted to executed CPU data reads. */
static void ur_rf054_native_observe(const char *kind, uint32_t addr, uint16_t value) {
  extern int snes_frame_counter;
  extern const char *g_last_recomp_func;
  if (!getenv("UR_QA01_RF054_NATIVE_SOUND_WRITER") ||
      snes_frame_counter != 6124) return;
  const uint8_t bank = (uint8_t)(addr >> 16);
  const uint16_t lo = (uint16_t)addr;
  const int is_rom = (bank >= 0x10 && bank <= 0x13 && lo >= 0x8000);
  if (kind[0] == 'r' && !is_rom) return;
  if (kind[0] == 'w' && !(lo >= 0x2142 && lo <= 0x2143)) return;
  static unsigned rf054_write, rf054_map, rf054_write_excess, rf054_map_excess;
  unsigned *count = kind[0] == 'w' ? &rf054_write : &rf054_map;
  unsigned *over = kind[0] == 'w' ? &rf054_write_excess : &rf054_map_excess;
  if (++*count <= 8192u)
    fprintf(stderr,
      "QA01RF054NATIVE kind=%s seq=%u frame=%d master=%llu addr=%06X val=%04X PB=%02X DB=%02X D=%04X Y=%04X A=%04X dp63=%02X dp64=%02X dp65=%02X scope=%s\n",
      kind,*count,snes_frame_counter,
      (unsigned long long)g_cpu.master_cycles,addr,value,
      (unsigned)g_cpu.PB,(unsigned)g_cpu.DB,(unsigned)g_cpu.D,
      (unsigned)g_cpu.Y,(unsigned)g_cpu.A,
      (unsigned)g_cpu.ram[0x63],(unsigned)g_cpu.ram[0x64],
      (unsigned)g_cpu.ram[0x65],
      g_last_recomp_func ? g_last_recomp_func : "?");
  else if (!(*over)++)
    fprintf(stderr,"QA01RF054NATIVE_TRUNCATED kind=%s\n",kind);
}

"""
COMMON_ROM_INSTRUMENT='  ur_rf054_native_observe("rom-map", addr, 0);\n'
COMMON_APU_INSTRUMENT='  if (port >= 2u) ur_rf054_native_observe("writer", adr, val);\n'

CPU_HELPER=r"""/* UR_QA01_RF054_NATIVE_SOUND_WRITER: bus helpers actually invoked.
 * Unlike RomPtr mapping requests, these are executed CPU memory-read calls.
 * Address logging adds no guest read and never replaces the read return. */
static void ur_rf054_actual_bus(const char *kind,CpuState *cpu,
                                uint8 bank,uint16 addr) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    if (!getenv("UR_QA01_RF054_NATIVE_SOUND_WRITER") ||
        snes_frame_counter != 6124 ||
        bank < 0x10 || bank > 0x13 || addr < 0x8000) return;
    static unsigned count,overflow;
    if (++count <= 8192u)
        fprintf(stderr,
          "QA01RF054NATIVEBUS kind=%s seq=%u frame=%d master=%llu addr=%02X%04X A=%04X Y=%04X D=%04X dp63=%02X dp64=%02X dp65=%02X scope=%s\n",
          kind,count,snes_frame_counter,
          (unsigned long long)cpu->master_cycles,
          (unsigned)bank,(unsigned)addr,
          (unsigned)cpu->A,(unsigned)cpu->Y,(unsigned)cpu->D,
          (unsigned)cpu->ram[0x63],(unsigned)cpu->ram[0x64],
          (unsigned)cpu->ram[0x65],
          g_last_recomp_func ? g_last_recomp_func : "?");
    else if (!overflow++)
        fprintf(stderr,"QA01RF054NATIVEBUS_TRUNCATED\n");
}

"""
CPU_BYTE_INSTRUMENT='    ur_rf054_actual_bus("read8", cpu, bank, addr);\n'
CPU_WORD_INSTRUMENT='    ur_rf054_actual_bus("read16", cpu, bank, addr);\n'

def patch_common(src:str)->str:
    if MARK in src:
        for fragment in (COMMON_HELPER,COMMON_ROM_INSTRUMENT,COMMON_APU_INSTRUMENT):
            if src.count(fragment)!=1:raise ValueError("partial/tampered RF054 native common RTL")
        return src
    for fragment in (COMMON_ROM_HEADER,COMMON_APU_HEADER,COMMON_APU_SLOT):
        if src.count(fragment)!=1:raise ValueError("RF054 unknown pinned native RTL anchor")
    out=src.replace(COMMON_ROM_HEADER,COMMON_HELPER+COMMON_ROM_HEADER+COMMON_ROM_INSTRUMENT,1)
    out=out.replace(COMMON_APU_HEADER,COMMON_APU_HEADER,1)
    out=out.replace(COMMON_APU_SLOT,COMMON_APU_SLOT+COMMON_APU_INSTRUMENT,1)
    if out.count("void RtlApuWrite(")!=src.count("void RtlApuWrite(") or out.count("uint8 *RomPtr(")!=src.count("uint8 *RomPtr("):
        raise AssertionError("RF054 duplicated native CPU/APU or ROM mapping path")
    return out

def patch_cpu(src:str)->str:
    if MARK in src:
        for fragment in (CPU_HELPER,CPU_BYTE_INSTRUMENT,CPU_WORD_INSTRUMENT):
            if src.count(fragment)!=1:raise ValueError("partial/tampered RF054 actual native CPU bus observer")
        return src
    for fragment in (CPU_BYTE_HEADER,CPU_WORD_HEADER):
        if src.count(fragment)!=1:raise ValueError("RF054 unknown pinned native CPU bus helper")
    out=src.replace(CPU_BYTE_HEADER,CPU_HELPER+CPU_BYTE_HEADER+CPU_BYTE_INSTRUMENT,1)
    out=out.replace(CPU_WORD_HEADER,CPU_WORD_HEADER+CPU_WORD_INSTRUMENT,1)
    for opcode in ("cpu_read8(","cpu_read16(","RomPtr("):
        if out.count(opcode)!=src.count(opcode):raise AssertionError("RF054 duplicated guest CPU bus call")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    a=p.parse_args()
    root=a.root.resolve()
    jobs=((COMMON,patch_common),(CPU,patch_cpu))
    staged=[]
    for path,fn in jobs:
        file=root/path
        if not file.is_file():p.error("missing pinned native source "+str(file))
        before=file.read_text(encoding="utf8")
        staged.append((file,before,fn(before)))
    for path,old,new in staged:
        if old!=new:path.write_text(new,encoding="utf8")
        print("RF054 native provenance",path,("already staged" if old==new else "read-only staged"))
    return 0
if __name__=="__main__":raise SystemExit(main())

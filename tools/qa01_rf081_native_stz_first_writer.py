#!/usr/bin/env python3
"""RF081 real native 82:D4F2 STZ D+$59 paced writer and committed value.

Stage after RF079/RF080 on pinned native source, before compiling. The hook
runs AFTER the pre-existing cpu_write8() returns, with no additional guest
read/write/clock adjustment. RF047 ordinal/strict sidecar remains authority.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import qa01_rf079_native_real_bit_branch as rf079
import qa01_rf080_rf047_strict_source_sidecar as rf080

BEAM=Path("snesrecomp/runner/src/beam_frame_driver.c")
CPU=Path("snesrecomp/runner/src/cpu_state.c")
STAMP="UR_QA01_RF081_NATIVE_STZ_TRUE_COMMIT"
RECORDER=rf079.RECORDER
PACE_TAIL=('    cpu_write8(cpu, bank, addr, v);\n'
           '}\n\nvoid cpu_write16_paced')
PACE_HEADER="void cpu_write8_paced(CpuState *cpu, uint8_t bank, uint16_t addr, uint8_t v) {\n"
HOOK = r'''/* UR_QA01_RF081_NATIVE_STZ_TRUE_COMMIT
 * Real tier-AOT 82:D4F2 marker arms the STZ observation, before the
 * actual existing paced writer. No extra guest bus calls, no scheduler
 * correction, no host-frame equality assertion. */
static unsigned ur_rf081_native_stz_armed;
static unsigned ur_rf081_native_stz_seen;
static void ur_rf081_native_opcode(uint32_t pc, unsigned tier) {
    if (!ur_rf079_enabled() || tier!=1u) return;
    if (pc==0x82D4F2u) {
        ur_rf081_native_stz_armed=1;
        ur_rf081_native_stz_seen=0;
    } else if (pc==0x82D4F4u) {
        if (ur_rf081_native_stz_armed && !ur_rf081_native_stz_seen) {
            ur_rf047_emit("QA01RF081NATIVE_STZ_MISSING_WRITE\n");
        }
        ur_rf081_native_stz_armed=0;
    }
}
void ur_rf081_native_committed_stz(CpuState *cpu, uint8 bank,
                                  uint16 addr, uint8 v) {
    extern int snes_frame_counter;
    if (!ur_rf081_native_stz_armed || !ur_rf079_enabled()) return;
    if (!ur_rf047_allow_row()) return;
    ++ur_rf081_native_stz_seen;
    ur_rf047_emit(
        "QA01RF047NATIVE seq=%llu stage=stz_real_commit f=%d"
        " guestPC=82D4F2 D=%04X bank=%02X addr=%04X"
        " written=%02X rawAfter=%02X master=%llu\n",
        ++ur_rf047_seq,snes_frame_counter,
        (unsigned)cpu->D,(unsigned)bank,(unsigned)addr,
        (unsigned)v,(unsigned)cpu->ram[addr],
        (unsigned long long)cpu->master_cycles);
}
'''

def patch(beam:str,cpu:str)->tuple[str,str]:
    if STAMP in beam or STAMP in cpu:
        raise ValueError("RF081 native STZ source already or partly staged")
    if (rf079.STAMP not in beam or rf080.STAMP not in beam or
        rf079.STAMP not in cpu):
        raise ValueError("RF081 requires real RF079 BIT and RF080 strict source log")
    for label, src, key in (("opcode",beam,RECORDER),("paced8",cpu,PACE_HEADER),
                            ("writer",cpu,PACE_TAIL)):
        if src.count(key)!=1:
            raise ValueError("RF081 exact native "+label+" source callsite drift")
    for bad in ("cpu_read8(", "cpu_write8(", "cpu_read16(", "cpu_write16("):
        if bad in HOOK:
            raise AssertionError("RF081 proposed hook includes a guest bus call")
    old_read=cpu.count("cpu_read8(")
    old_write=cpu.count("cpu_write8(cpu, bank, addr, v);")
    old_opcode=beam.count(RECORDER)
    beam=beam.replace(RECORDER,HOOK+RECORDER+
                      "    ur_rf081_native_opcode(pc,tier);\n",1)
    cpu=cpu.replace(PACE_HEADER,
      "extern void ur_rf081_native_committed_stz(CpuState *,uint8,uint16,uint8);\n"
      +PACE_HEADER,1)
    cpu=cpu.replace(PACE_TAIL,
      "    cpu_write8(cpu, bank, addr, v);\n"
      "    ur_rf081_native_committed_stz(cpu,bank,addr,v);\n"
      "}\n\nvoid cpu_write16_paced",1)
    if (cpu.count("cpu_read8(")!=old_read or
        cpu.count("cpu_write8(cpu, bank, addr, v);")!=old_write or
        beam.count(RECORDER)!=old_opcode):
        raise AssertionError("RF081 altered native guest bus/cpu decoder population")
    if beam.count(STAMP)!=1 or \
       cpu.count("ur_rf081_native_committed_stz(")!=2:
        raise AssertionError("RF081 source callsite missing")
    return beam,cpu

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,required=True)
    args=ap.parse_args()
    root=args.root.resolve()
    b,c=root/BEAM,root/CPU
    if not b.is_file() or not c.is_file():
        ap.error("pinned native beam/cpu files absent")
    newb,newc=patch(b.read_text(),c.read_text())
    b.write_text(newb);c.write_text(newc)
    print("RF081 native actual STZ committed output and real AOT marker staged")

if __name__=="__main__":
    main()

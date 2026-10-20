#!/usr/bin/env python3
"""RF079: native exact real BIT paced-read and BPL N-input witness.

Disposable pinned Baldosa after RF047 executed-PC source and RF076 capacity,
before native compilation. Records the EXISTING cpu_read8_paced return and
the already updated CpuState negative-flag mirror, without a second guest
read or an added instruction/cycle. Two NMI host frame labels only.
"""
from __future__ import annotations
import argparse
from pathlib import Path

BEAM=Path('snesrecomp/runner/src/beam_frame_driver.c')
CPU=Path('snesrecomp/runner/src/cpu_state.c')
STAMP='UR_QA01_RF079_NATIVE_POST_BIT_BRANCH'
RECORDER='void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {\n'
RECORDER_END='    return;\n  }\n  /* RF047'
READ_TAIL=('    return cpu_read8(cpu, bank, addr);\n'
           '}\n\nuint16_t cpu_read16_paced')
NOTE=r'''/* UR_QA01_RF079_NATIVE_POST_BIT_BRANCH: opt-in source-local.
 * Arm on REAL executed tier-AOT 82:D4EE marker, observe the returned
 * paced read at D+$57 and its actual returned byte, then capture the N
 * flag mirror at the genuine next executed tier-AOT BPL marker.
 * No new CPU bus operation, no emulator tick, no PC/SP adjustment. */
static unsigned ur_rf079_arm_bit;
static unsigned ur_rf079_bit_seen;
static unsigned ur_rf079_enabled(void) {
  extern int snes_frame_counter;
  const char *s=getenv("UR_QA01_RF079_NATIVE_BIT_BPL");
  return s && *s && (snes_frame_counter==1017 || snes_frame_counter==1018);
}
void ur_rf079_native_actual_bit_read(CpuState *cpu, uint8 bank,
                                     uint16 addr, uint8 value) {
  extern int snes_frame_counter;
  if (!ur_rf079_arm_bit || !ur_rf079_enabled()) return;
  if (bank!=0 || addr!=(uint16)(cpu->D+0x57u)) return;
  if (!ur_rf047_allow_row()) return;
  ur_rf079_bit_seen=1;
  ur_rf079_arm_bit=0;
  ur_rf047_emit(
      "QA01RF047NATIVE seq=%llu stage=bit_real_return f=%d"
      " guestPC=82D4EE D=%04X addr=%04X value=%02X"
      " master=%llu\n",
      ++ur_rf047_seq,snes_frame_counter,
      (unsigned)cpu->D,(unsigned)addr,(unsigned)value,
      (unsigned long long)cpu->master_cycles);
}
'''
MARKER_PATCH=r'''    if (ur_rf079_enabled() && tier==1u) {
      if (pc==0x82D4EEu) {
        ur_rf079_arm_bit=1;
        ur_rf079_bit_seen=0;
      } else if (pc==0x82D4F0u) {
        if (!ur_rf047_allow_row()) return;
        ur_rf047_emit(
            "QA01RF047NATIVE seq=%llu stage=bpl_actual_input f=%d"
            " guestPC=82D4F0 D=%04X N=%u bitReadSeen=%u"
            " master=%llu\n",
            ++ur_rf047_seq,snes_frame_counter,
            (unsigned)g_cpu.D,(unsigned)(g_cpu._flag_N!=0),
            ur_rf079_bit_seen,
            (unsigned long long)g_cpu.master_cycles);
        ur_rf079_arm_bit=0;
      }
    }
'''

def patch(beam:str,cpu:str)->tuple[str,str]:
    if STAMP in beam or STAMP in cpu:
        raise ValueError('RF079 native observer already/partially staged')
    if (beam.count(RECORDER)!=1 or beam.count(RECORDER_END)!=1 or
        'UR_QA01_RF047_EXECUTED_GUEST_OPCODE_PC' not in beam or
        'UR_QA01_RF076_FINITE_RECORDER_CAP_131072' not in beam or
        'QA01RF047NATIVE seq=' not in beam):
        raise ValueError('RF079 requires actual RF047/RF076 pinned native recorder')
    if cpu.count(READ_TAIL)!=1:
        raise ValueError('RF079 real paced bus return source changed')
    # No actual guest read or guest timing work may appear in observer source.
    for bus in ('cpu_read8(', 'cpu_read16(', 'cpu_write8(', 'cpu_write16('):
        if bus in NOTE+MARKER_PATCH:
            raise AssertionError('RF079 observer would call a guest bus operation')
    before={needle:cpu.count(needle) for needle in ('cpu_read8(cpu, bank, addr)',
                                                    'cpu_read8_paced(')}
    beam=beam.replace(RECORDER, NOTE+RECORDER,1)
    beam=beam.replace(RECORDER_END,MARKER_PATCH+RECORDER_END,1)
    cpu=cpu.replace(READ_TAIL,
        '    const uint8_t ur_rf079_actual_value=cpu_read8(cpu, bank, addr);\n'
        '    ur_rf079_native_actual_bit_read(cpu,bank,addr,ur_rf079_actual_value);\n'
        '    return ur_rf079_actual_value;\n'
        '}\n\nuint16_t cpu_read16_paced',1)
    cpu=cpu.replace('uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n',
        'extern void ur_rf079_native_actual_bit_read(CpuState *,uint8,uint16,uint8);\n'
        'uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n',1)
    if any(cpu.count(k)!=value for k,value in before.items()):
        raise AssertionError('RF079 changed real native bus read call population')
    if beam.count(STAMP)!=1 or cpu.count('ur_rf079_native_actual_bit_read(')!=2:
        raise AssertionError('RF079 native callsites unexpectedly changed')
    return beam,cpu

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    opts=ap.parse_args()
    root=opts.root.resolve()
    b,c=root/BEAM,root/CPU
    if not b.is_file() or not c.is_file():
        ap.error('pinned native real beam/CPU source missing')
    patched=patch(b.read_text(),c.read_text())
    b.write_text(patched[0]);c.write_text(patched[1])
    print('RF079 true AOT BIT returned byte and BPL N recorded, no new guest bus or tick')

if __name__=='__main__':main()

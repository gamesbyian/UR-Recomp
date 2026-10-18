#!/usr/bin/env python3
"""RF047: read-only native NMI frame, handler-return, and real-stack-read observer.

Opt-in disposable Baldosa native guest only. Inject after RF044 native read
observer in cpu_state.c; stage before the clean research guest build.
Records independently measured native PC/SP/status/beam/master and one strictly
sequenced native log. Never introduces an emulated bus read/write or CPU cost.
"""
from __future__ import annotations
import argparse
from pathlib import Path

BEAM = Path("snesrecomp/runner/src/beam_frame_driver.c")
CPU = Path("snesrecomp/runner/src/cpu_state.c")
BRIDGE = Path("snesrecomp/runner/src/snes/interp_bridge.c")
BRIDGE_DECL = "extern Snes *g_snes;\n"
BRIDGE_INTERP = "        if (stop_on_rti && op == 0x40) {\n            sync_interp_to_cpu(&in, cpu);\n"
BRIDGE_COMPILED = "        if (stop_on_rti)\n            return 1;  /* compiled RTI consumed the interrupt frame */\n"
STAMP = "UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN"
BEAM_INCLUDE = "#include <stdint.h>\n"
BEAM_RUN = "  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);\n"
BEAM_RETURN = "  update_resume_pc();\n}"
BEAM_NMI = "    run_interrupt(nmi_vector(), frame_end);\n"
CPU_HOOK = "    static unsigned rows;\n    if (rows++ < 8192u)\n"
CPU_ANCHOR = "static void ur_rf044_native_read(CpuState *cpu,uint8 bank,uint16 addr,\n"

NOTE = r"""/* UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN
 * Frame 1017..1025 native guest timing and actual stack-helper reads.
 * Every RF047 event uses its OWN sequence counter in this process, so mixed
 * stdout/stderr lines cannot be mistaken for native execution order. */
static int ur_rf047_enabled = -1;
static int ur_rf047_in_nmi = 0;
static unsigned ur_rf047_events = 0;
static unsigned long long ur_rf047_seq = 0;
static int ur_rf047_allowed(void) {
  extern int snes_frame_counter;
  if (ur_rf047_enabled < 0) {
    const char *flag = getenv("UR_QA01_RF047_NATIVE_NMI_RETURN");
    ur_rf047_enabled = (flag && *flag) ? 1 : 0;
  }
  return ur_rf047_enabled && snes_frame_counter >= 1017 &&
         snes_frame_counter <= 1025;
}
static int ur_rf047_allow_row(void) {
  if (!ur_rf047_allowed()) return 0;
  if (ur_rf047_events++ >= 8192u) {
    if (ur_rf047_events == 8193u)
      fputs("QA01RF047NATIVE_TRUNCATED\n", stderr);
    return 0;
  }
  return 1;
}
static void ur_rf047_nmi_snapshot(const char *stage, uint32_t vector) {
  extern int snes_frame_counter;
  if (!ur_rf047_in_nmi || !ur_rf047_allow_row()) return;
  fprintf(stderr,
      "QA01RF047NATIVE seq=%llu stage=%s f=%d resume=%06X vector=%06X"
      " PB=%02X P=%02X S=%04X emu=%u master=%llu beamMaster=%llu"
      " beamV=%u beamH=%u stack=%02X%02X%02X%02X\n",
      ++ur_rf047_seq, stage, snes_frame_counter, (unsigned)s_resume_pc,
      (unsigned)vector, (unsigned)g_cpu.PB, (unsigned)g_cpu.P,
      (unsigned)g_cpu.S, (unsigned)g_cpu.emulation,
      (unsigned long long)g_cpu.master_cycles,
      (unsigned long long)g_snes->beamMasterLast,
      (unsigned)g_snes->vPos, (unsigned)g_snes->hPos,
      (unsigned)g_cpu.ram[0x01ed], (unsigned)g_cpu.ram[0x01ee],
      (unsigned)g_cpu.ram[0x01ef], (unsigned)g_cpu.ram[0x01f0]);
}
void ur_rf047_native_stack_read(CpuState *cpu, uint8 bank,
                                  uint16 addr, uint16 value, unsigned width) {
  extern int snes_frame_counter;
  if (!ur_rf047_allowed() || addr > 0x01f1u ||
      (unsigned)addr + width - 1u < 0x01edu ||
      !ur_rf047_allow_row()) return;
  fprintf(stderr,
      "QA01RF047NATIVE seq=%llu stage=read f=%d bank=%02X"
      " addr=%04X width=%u value=%04X PB=%02X P=%02X S=%04X"
      " master=%llu beamV=%u beamH=%u nmi=%u\n",
      ++ur_rf047_seq, snes_frame_counter, (unsigned)bank,
      (unsigned)addr, width, (unsigned)value, (unsigned)cpu->PB,
      (unsigned)cpu->P, (unsigned)cpu->S,
      (unsigned long long)cpu->master_cycles,
      (unsigned)g_snes->vPos, (unsigned)g_snes->hPos,
      (unsigned)ur_rf047_in_nmi);
}

void ur_rf047_native_rti_opcode(CpuState *cpu, uint32_t opcode_pc,
                                 uint32_t return_pc, unsigned compiled) {
  extern int snes_frame_counter;
  if (!ur_rf047_in_nmi || !ur_rf047_allow_row()) return;
  fprintf(stderr,
      "QA01RF047NATIVE seq=%llu stage=%s f=%d opcodePC=%06X returnPC=%06X"
      " P=%02X S=%04X master=%llu beamV=%u beamH=%u\n",
      ++ur_rf047_seq, compiled ? "compiled_rti" : "interp_rti",
      snes_frame_counter, (unsigned)opcode_pc, (unsigned)return_pc,
      (unsigned)cpu->P, (unsigned)cpu->S,
      (unsigned long long)cpu->master_cycles,
      (unsigned)g_snes->vPos, (unsigned)g_snes->hPos);
}
"""

def patch(beam: str, cpu: str, bridge: str) -> tuple[str,str,str]:
    if STAMP in beam or STAMP in cpu:
        raise ValueError("RF047 already/partially installed")
    if any(beam.count(a) != 1 for a in
           (BEAM_INCLUDE, BEAM_RUN, BEAM_RETURN, BEAM_NMI)):
        raise ValueError("RF047 pinned Baldosa beam interrupt source drift")
    if "UR_QA01_RF044_STACK_BUS" not in cpu or \
       cpu.count(CPU_HOOK) != 1 or cpu.count(CPU_ANCHOR) != 1:
        raise ValueError("RF047 requires precise RF044 native real-read observer")

    if any(bridge.count(x)!=1 for x in
           (BRIDGE_DECL, BRIDGE_INTERP, BRIDGE_COMPILED)):
        raise ValueError("RF047 pinned native interpreter RTI source drift")
    beam = beam.replace(BEAM_INCLUDE, BEAM_INCLUDE +
                        "#include <stdio.h>\n#include <stdlib.h>\n", 1)
    beam = beam.replace("static void run_interrupt(uint32_t vector, uint64_t deadline) {\n",
                        NOTE +
                        "static void run_interrupt(uint32_t vector, uint64_t deadline) {\n", 1)
    beam = beam.replace(BEAM_RUN,
                        "  ur_rf047_nmi_snapshot(\"entry\", vector);\n" +
                        BEAM_RUN +
                        "  ur_rf047_nmi_snapshot(\"after_push\", vector);\n", 1)
    beam = beam.replace(BEAM_RETURN, "  update_resume_pc();\n" +
                        "  ur_rf047_nmi_snapshot(\"handler_return\", vector);\n}", 1)
    beam = beam.replace(BEAM_NMI,
                        "    const uint32_t ur_rf047_vector = nmi_vector();\n"
                        "    ur_rf047_in_nmi = 1;\n"
                        "    run_interrupt(ur_rf047_vector, frame_end);\n"
                        "    ur_rf047_in_nmi = 0;\n", 1)
    cpu = cpu.replace(CPU_ANCHOR,
                      "extern void ur_rf047_native_stack_read(CpuState *,uint8,uint16,uint16,unsigned);\n"
                      + CPU_ANCHOR, 1)
    cpu = cpu.replace(CPU_HOOK,
                      "    ur_rf047_native_stack_read(cpu,bank,addr,value,width);\n"
                      + CPU_HOOK, 1)
    for operation in ("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc)",
                      "interp_bridge_run_interrupt(&g_cpu, vector)",
                      "nmi_vector()"):
        if beam.count(operation) != 1:
            raise AssertionError("RF047 changed real NMI call count: " + operation)
    if cpu.count("ur_rf047_native_stack_read(cpu,bank,addr,value,width);") != 1:
        raise AssertionError("RF047 duplicate source read observer")
    bridge = bridge.replace(BRIDGE_DECL,
        BRIDGE_DECL + "extern void ur_rf047_native_rti_opcode(CpuState *,uint32_t,uint32_t,unsigned);\n",1)
    bridge = bridge.replace(BRIDGE_INTERP,
        BRIDGE_INTERP +
        '            ur_rf047_native_rti_opcode(cpu, pc_before,\n'
        '                ((uint32_t)in.k << 16) | in.pc, 0);\n',1)
    bridge = bridge.replace(BRIDGE_COMPILED,
        '        if (stop_on_rti) {\n'
        '            ur_rf047_native_rti_opcode(cpu, target,\n'
        '                ((uint32_t)in->k << 16) | in->pc, 1);\n'
        '            return 1;  /* compiled RTI consumed the interrupt frame */\n'
        '        }\n',1)
    if bridge.count("ur_rf047_native_rti_opcode(cpu,") != 2:
        raise AssertionError("RF047 native interp/compiled RTI callsite count")
    return beam,cpu,bridge

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True,type=Path)
    a=ap.parse_args()
    root=a.root.resolve()
    b=root/BEAM
    c=root/CPU
    d=root/BRIDGE
    if not b.is_file() or not c.is_file() or not d.is_file():
        ap.error("missing pinned disposable Baldosa source files")
    old_b=b.read_text(encoding="utf8")
    old_c=c.read_text(encoding="utf8")
    old_d=d.read_text(encoding="utf8")
    nb,nc,nd=patch(old_b,old_c,old_d)
    b.write_text(nb,encoding="utf8")
    c.write_text(nc,encoding="utf8")
    d.write_text(nd,encoding="utf8")
    print("RF047 staged native true NMI entry/return/stack-read source observer")

if __name__=="__main__":main()

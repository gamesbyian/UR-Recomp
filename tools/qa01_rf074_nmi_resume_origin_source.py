#!/usr/bin/env python3
"""RF074 opt-in source-only native NMI scheduler RESUME ORIGIN witness.

Staged after RF044/RF047 and before native regeneration, in disposable pinned
Baldosa source. Reads the bridge's EXISTING always-on resume assignment ring
immediately before the real cpu_push_interrupt_frame_at call. Does not emit
any ROM/WRAM guest read/write, change P/S/PC, scheduling, or ticks.

An event is evidence of a scheduler resume-PC ASSIGNMENT; it is never a proof
of a real executed fetched opcode at the recorded address.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import qa01_rf047_native_nmi_phase_witness as rf47

STAMP="UR_QA01_RF074_NMI_SCHEDULER_RESUME_ORIGIN"
BEAM=rf47.BEAM
BEFORE_PUSH='  ur_rf047_nmi_snapshot("entry", vector);\n'
INTERRUPT='static void run_interrupt(uint32_t vector, uint64_t deadline) {\n'

HELPER=r"""/* UR_QA01_RF074_NMI_SCHEDULER_RESUME_ORIGIN
 * The permanently-on bridge resume ring stores old/new PC, assignment site,
 * frame, SP and nesting, WITHOUT requiring interpreter instructions to run.
 * Sample its LAST SET/RESTORE event, NOT an older arbitrary event that happens
 * to match today's resume PC. Snapshot is before real native interrupt push.
 * If origin not recoverable, print matched=0 and HOLD; never invent a PC. */
static void ur_rf074_native_nmi_resume_origin(uint32_t vector) {
  extern int snes_frame_counter;
  if (!ur_rf047_in_nmi || !ur_rf047_allowed()) return;
  const char *enabled = getenv("UR_QA01_RF074_NMI_RESUME_ORIGIN");
  if (!enabled || !*enabled) return;
  if (!ur_rf047_allow_row()) return;
  const uint64_t n = interp_bridge_resume_total();
  const int cap = interp_bridge_resume_capacity();
  InterpResumeEvent source = {0};
  uint64_t seq = 0;
  unsigned found = 0;
  const uint64_t available = n < (uint64_t)cap ? n : (uint64_t)cap;
  for (uint64_t i = 0; i < available; ++i) {
    uint64_t this_seq = n - i - 1u;
    InterpResumeEvent row;
    if (!interp_bridge_resume_get(this_seq, &row)) break;
    if (row.kind != INTERP_RESUME_KIND_SET &&
        row.kind != INTERP_RESUME_KIND_RESTORE) continue;
    source = row;
    seq = this_seq;
    found = 1;
    break;
  }
  const unsigned matches = found && ((source.new_pc24 & 0xFFFFFFu) ==
                                      (s_resume_pc & 0xFFFFFFu));
  ur_rf047_emit(
      "QA01RF047NATIVE seq=%llu stage=resume_origin f=%d"
      " phase=before_real_interrupt_push resume=%06X vector=%06X"
      " sourceFound=%u originMatches=%u"
      " ringTotal=%llu ringSeq=%llu"
      " oldPC=%06X newPC=%06X"
      " kind=%s site=%s sourceFrame=%d sourceS=%04X"
      " bridgeDepth=%d schedDepth=%d"
      " waiHalted=%u master=%llu beamV=%u beamH=%u\n",
      ++ur_rf047_seq, snes_frame_counter,
      (unsigned)(s_resume_pc & 0xFFFFFFu), (unsigned)(vector & 0xFFFFFFu),
      found, matches, (unsigned long long)n, (unsigned long long)seq,
      (unsigned)source.old_pc24, (unsigned)source.new_pc24,
      found ? interp_bridge_resume_kind_name(source.kind) : "missing",
      found ? interp_bridge_resume_site_name(source.site) : "missing",
      found ? source.frame : -1, (unsigned)source.sp,
      found ? (int)source.bridge_depth : -1,
      found ? (int)source.sched_depth : -1,
      s_wai_halted ? 1u : 0u,
      (unsigned long long)g_cpu.master_cycles,
      (unsigned)g_snes->vPos, (unsigned)g_snes->hPos);
}
"""

def patch(beam: str)->str:
    if STAMP in beam:
        raise ValueError("RF074 already or partially staged")
    if (rf47.STAMP not in beam or beam.count(INTERRUPT)!=1 or
        beam.count(BEFORE_PUSH)!=1 or
        "ur_rf047_allow_row" not in beam or
        '#include "snes/interp_bridge.h"' not in beam or
        "cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);" not in beam):
        raise ValueError("RF074 requires staged original RF047 NMI + pinned Baldosa source")
    for op in ("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc)",
               "interp_bridge_run_interrupt(&g_cpu, vector)",
               "snes_read(g_snes,", "cpu_read8(", "cpu_write8("):
        # Observer must not introduce a new emulated memory operation.
        if HELPER.count(op)!=0:
            raise AssertionError("RF074 helper would introduce guest operations: "+op)
    updated=beam.replace(INTERRUPT, HELPER+INTERRUPT,1)
    updated=updated.replace(BEFORE_PUSH,
                            BEFORE_PUSH+
                            "  ur_rf074_native_nmi_resume_origin(vector);\n",1)
    if updated.count(STAMP)!=1 or updated.count("ur_rf074_native_nmi_resume_origin(")!=2:
        raise AssertionError("RF074 source stage ambiguity")
    return updated

def main()->None:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--root",required=True,type=Path)
    opt=a.parse_args()
    path=opt.root.resolve()/BEAM
    if not path.is_file():
        a.error("RF074 original pinned beam driver missing")
    src=path.read_text(encoding="utf8")
    path.write_text(patch(src),encoding="utf8")
    print("RF074 bounded NMI resume-origin history staged; no guest execution proof or gameplay change")

if __name__=="__main__":
    main()

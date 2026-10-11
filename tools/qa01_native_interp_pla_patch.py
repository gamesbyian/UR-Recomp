#!/usr/bin/env python3
"""Bounded native interpreter PLA observer for disposable pinned Baldosa only.

Observe the interpreter's own SP/A/M/E *at opcode execution*, as distinct
from CpuState state sampled in the shared bus-read bridge. No guest opcode,
return value, stack movement, CPU scheduling, or input is changed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

STAMP = "UR_QA01_NATIVE_INTERPRETER_PLA_V1"
INCLUDE = '#include "interp816.h"\n'
PULLBYTE = """static uint8_t interp816_pullByte(Interp816* cpu) {
  cpu->sp++;
  if(cpu->e) cpu->sp = (cpu->sp & 0xff) | 0x100;
  return interp816_read(cpu, cpu->sp);
}
"""
OPCODE = """    case 0x68: { // pla imp
      if(cpu->mf) {
        cpu->a = (cpu->a & 0xff00) | interp816_pullByte(cpu);
      } else {
        cpu->cyclesUsed++; // 16-bit m: 1 extra cycle
        cpu->a = interp816_pullWord(cpu);
      }
      interp816_setZN(cpu, cpu->a, cpu->mf);
      break;
    }
"""


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("original native interpreter PLA observer already installed")
    if (source.count(OPCODE) != 1 or source.count(INCLUDE) != 1
            or source.count(PULLBYTE) != 1):
        raise ValueError("pinned interpreter case-68/opcode header absent or ambiguous")
    if source.count("static uint16_t interp816_pullWord(Interp816* cpu) {") != 1:
        raise ValueError("pinned 16-bit interpreter pull implementation absent")
    helper = r"""
/* UR_QA01_NATIVE_INTERPRETER_PLA_V1.
 * The paired probe first attests the real native I_NMI 4004 word writer.
 * arm_seen is a callback ordering witness from disposable cpu_state.c.
 * PC here is the interpreter's POST-OPCODE-FETCH cursor. */
extern unsigned ur_qa01_stack_saved_writer_seen(void);
extern int snes_frame_counter;
/* Record the byte reads within the *current* PLA, not other bus traffic. */
static unsigned ur_qa01_pla_active = 0;
static unsigned ur_qa01_pla_read_count = 0;
static uint16_t ur_qa01_pla_read_addr[2] = {0, 0};
static uint8_t ur_qa01_pla_read_value[2] = {0, 0};
static FILE *ur_qa01_interp_pla_output(void) {
    static int initialized = 0;
    static FILE *fp = NULL;
    if (!initialized) {
        const char *path = getenv("UR_QA_NATIVE_INTERP_PLA_PATH");
        if (path && path[0]) {
            fp = fopen(path, "w");
            if (fp) {
                setvbuf(fp, NULL, _IONBF, 0);
                /* A zero-PLA report requires proof the observer started. */
                fputs("QANATIVEINTPLAREADY\n", fp);
            }
        }
        initialized = 1;
    }
    return fp;
}
/* Real production interp_bridge.c constructs a LOCAL Interp816 in;
 * interp816_init() is not part of this game's live fallback path.
 * The attested native 4004 NMI writer invokes this from cpu_state.c. */
void ur_qa01_interp_pla_arm(void) {
    (void)ur_qa01_interp_pla_output();
}
static void ur_qa01_note_interp_pla(Interp816 *cpu, uint16_t sp0,
                                    uint16_t a0, unsigned m0, unsigned e0) {
    int frame = snes_frame_counter;
    if (frame < 5778 || frame > 5782 ||
        sp0 < 0x01DBu || sp0 > 0x01DDu)
        return;
    static unsigned count = 0;
    FILE *fp = ur_qa01_interp_pla_output();
    if (!fp) return;
    if (count == 64) {
        fputs("QANATIVEINTPLAOVERFLOW\n", fp);
        ++count;
        return;
    }
    if (count > 64) return;
    ++count;
    fprintf(fp, "QANATIVEINTPLA f=%d k=%02X pcnext=%04X"
            " sp0=%04X sp1=%04X a0=%04X a1=%04X"
            " m0=%u e0=%u armed=%u"
            " reads=%u ra0=%04X rv0=%02X ra1=%04X rv1=%02X\n",
            frame, (unsigned)cpu->k, (unsigned)cpu->pc,
            (unsigned)sp0, (unsigned)cpu->sp,
            (unsigned)a0, (unsigned)cpu->a, m0, e0,
            ur_qa01_stack_saved_writer_seen() ? 1u : 0u,
            ur_qa01_pla_read_count,
            (unsigned)ur_qa01_pla_read_addr[0], (unsigned)ur_qa01_pla_read_value[0],
            (unsigned)ur_qa01_pla_read_addr[1], (unsigned)ur_qa01_pla_read_value[1]);
}
"""
    before = """    case 0x68: { // pla imp
      /* Observed interpreter registers, not stale host CpuState S/M. */
      const uint16_t ur_qa_pla_sp0 = cpu->sp;
      const uint16_t ur_qa_pla_a0 = cpu->a;
      const unsigned ur_qa_pla_m0 = (unsigned)(cpu->mf != 0);
      const unsigned ur_qa_pla_e0 = (unsigned)(cpu->e != 0);
      if(cpu->mf) {
        cpu->a = (cpu->a & 0xff00) | interp816_pullByte(cpu);
      } else {
        cpu->cyclesUsed++; // 16-bit m: 1 extra cycle
        cpu->a = interp816_pullWord(cpu);
      }
      interp816_setZN(cpu, cpu->a, cpu->mf);
      ur_qa01_note_interp_pla(cpu, ur_qa_pla_sp0, ur_qa_pla_a0,
                              ur_qa_pla_m0, ur_qa_pla_e0);
      break;
    }
"""
    # Activate only within the existing original PLA opcode and capture
    # the single returned byte from each original interpreter read.
    before = before.replace(
        "      if(cpu->mf) {",
        """      ur_qa01_pla_read_count = 0;
      ur_qa01_pla_read_addr[0] = ur_qa01_pla_read_addr[1] = 0;
      ur_qa01_pla_read_value[0] = ur_qa01_pla_read_value[1] = 0;
      ur_qa01_pla_active = 1;
      if(cpu->mf) {""", 1)
    before = before.replace(
        "      ur_qa01_note_interp_pla(cpu,",
        "      ur_qa01_pla_active = 0;\n      ur_qa01_note_interp_pla(cpu,", 1)
    if before.count("interp816_pullWord(cpu)") != 1:
        raise AssertionError("original 16-bit PLA implementation must remain unchanged")
    observed_byte = """static uint8_t interp816_pullByte(Interp816* cpu) {
  cpu->sp++;
  if(cpu->e) cpu->sp = (cpu->sp & 0xff) | 0x100;
  uint8_t ur_qa_pla_byte = interp816_read(cpu, cpu->sp);
  if (ur_qa01_pla_active && ur_qa01_pla_read_count < 2) {
    unsigned i = ur_qa01_pla_read_count++;
    ur_qa01_pla_read_addr[i] = cpu->sp;
    ur_qa01_pla_read_value[i] = ur_qa_pla_byte;
  }
  return ur_qa_pla_byte;
}
"""
    if observed_byte.count("interp816_read(cpu, cpu->sp)") != 1:
        raise AssertionError("read-only interpreter byte observation must not double-read")
    return (source.replace(INCLUDE, INCLUDE + helper, 1)
                  .replace(PULLBYTE, observed_byte, 1)
                  .replace(OPCODE, before, 1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    target = args.source.resolve()
    if target.name != "interp816.c" or "snesrecomp" not in target.parts:
        raise ValueError("require disposable snesrecomp/runner/src/snes/interp816.c")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

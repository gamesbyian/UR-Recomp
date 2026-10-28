#!/usr/bin/env python3
"""RF093: opt-in executed native SPC receipt/ready and CPU-port queue clock witness.

Patch only the pinned disposable Baldosa snesrecomp/runner/src/snes/apu.c,
after RF088 and before native compilation. Preserve every original MMIO,
queue and tick operation. Native portClock is SPC-relative, not a CPU master
clock or a calibrated original Snes9x SPC clock.
"""
from __future__ import annotations

import argparse
from pathlib import Path

FILE = Path("snesrecomp/runner/src/snes/apu.c")
STAMP = "UR_QA01_RF093_NATIVE_SPC_EDGES"
ENTRY = "static const uint8_t bootRom[0x40] = {"
NOW = "  apu->inPorts[port] = val;\n  audio_trace_on_cpu_port_apply(port, val);"
QUEUE = "  apu_writePortNow(apu, w->port, w->val);"
SCHEDULE = "  apu->portQTail++;\n  apu->portLastGuest = guest_cycle;"
READ = ("      uint8_t v = apu->inPorts[adr - 0xf4];\n"
        "      audio_trace_on_spc_port_read((uint8_t)(adr - 0xf4), v);")
WRITE = ("      audio_trace_on_spc_port_write((uint8_t)(adr - 0xf4), val);\n"
         "      apu->outPorts[adr - 0xf4] = val;")

HOOK = r'''
/* UR_QA01_RF093_NATIVE_SPC_EDGES
 * All timestamps use native APU portClock, advanced once per apu_cycle.
 * The native SPC bus accesses currently execute at the opcode's first
 * cycle; PC is a next-PC hint, NOT a hardware-cycle-accurate opcode clock.
 * An APPLY row is the actual input-port mutation. QUEUE_APPLY separately
 * identifies its queued provenance, while immediate HLE writes lack it.
 */
extern int snes_frame_counter;
static unsigned ur_rf093_rows;
static void ur_rf093_note(Apu *apu, const char *kind, unsigned port,
                          unsigned value, uint64_t target, uint64_t guest) {
  const char *flag = getenv("UR_QA01_RF093_NATIVE_SPC");
  if (!flag || flag[0] != '1' || flag[1] != '\0') return;
  /* Native result +265..+269 is frame 6447..6451 in sequence 17.
   * Keep the earlier 6054..6059 control window. */
  if (!((snes_frame_counter >= 6054 && snes_frame_counter <= 6059) ||
        (snes_frame_counter >= 6447 && snes_frame_counter <= 6451)) ||
      port > 3u) return;
  if (++ur_rf093_rows > 32768u) {
    if (ur_rf093_rows == 32769u)
      fprintf(stderr, "QA01RF093NATIVE_TRUNCATED\n");
    return;
  }
  fprintf(stderr,
    "QA01RF093NATIVE seq=%u f=%d kind=%s addr=%04X val=%02X"
    " spc_ticks=%llu spc_next_pc=%04X q=%u target=%llu guest=%llu"
    " clock=native_spc\n",
    ur_rf093_rows, snes_frame_counter, kind, 0xf4u + port, value & 0xffu,
    (unsigned long long)apu->portClock, (unsigned)apu->spc->pc,
    (unsigned)(apu->portQTail - apu->portQHead),
    (unsigned long long)target, (unsigned long long)guest);
}
'''

def patch(source: str) -> str:
    if STAMP in source or "ur_rf093_note(" in source:
        raise ValueError("RF093 already or partially staged")
    for anchor in (ENTRY, NOW, QUEUE, SCHEDULE, READ, WRITE):
        if source.count(anchor) != 1:
            raise ValueError("RF093 pinned native APU source drift: " + anchor[:45])
    calls = ("apu_writePortNow(", "audio_trace_on_cpu_port_apply(",
             "audio_trace_on_spc_port_read(", "audio_trace_on_spc_port_write(",
             "apu->inPorts[adr - 0xf4]", "apu->outPorts[adr - 0xf4] = val;",
             "apu->portQTail++;", "apu->portClock++;")
    before = tuple(source.count(call) for call in calls)
    source = source.replace(ENTRY, HOOK + "\n" + ENTRY, 1)
    source = source.replace(
        NOW, NOW + '\n  ur_rf093_note(apu, "CPU_TO_SPC_APPLY", port, val, 0, 0);', 1)
    source = source.replace(
        QUEUE, QUEUE +
        '\n  ur_rf093_note(apu, "QUEUE_APPLY", w->port, w->val, w->target_cycle, 0);', 1)
    source = source.replace(
        SCHEDULE, SCHEDULE +
        '\n  ur_rf093_note(apu, "QUEUE_SCHEDULE", w->port, w->val, target, guest_cycle);', 1)
    source = source.replace(
        READ, READ +
        '\n      ur_rf093_note(apu, "CPU_TO_SPC_READ", adr - 0xf4, v, 0, 0);', 1)
    source = source.replace(
        WRITE, WRITE +
        '\n      ur_rf093_note(apu, "SPC_TO_CPU_WRITE", adr - 0xf4, val, 0, 0);', 1)
    if tuple(source.count(call) for call in calls) != before:
        raise AssertionError("RF093 altered actual bus/queue/tick call population")
    if source.count(STAMP) != 1 or source.count("ur_rf093_note(apu,") != 5:
        raise AssertionError("RF093 observer population incorrect")
    return source

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    path = args.root / FILE
    if not path.is_file() or path.is_symlink():
        parser.error("pinned disposable native APU source missing or symlinked")
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    print("RF093 native SPC executed edges and queue timing staged")

if __name__ == "__main__":
    main()

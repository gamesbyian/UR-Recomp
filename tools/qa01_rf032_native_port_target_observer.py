#!/usr/bin/env python3
"""RF-032: read-only pinned Baldosa queued-port target/CPU echo observers.

Apply AFTER RF-030's native observer to the disposable full original/native
research guest. Do not touch original Snes9x, guest clocks, ROM, queue policy,
controllers, Windows, or Modern. All RF-032 events use native portClock only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA01_RF032_TARGET_ECHO"
APU = Path("snesrecomp/runner/src/snes/apu.c")
SNES = Path("snesrecomp/runner/src/snes/snes.c")

APU_HELPER_OLD = "static void apu_applyPortWrite(Apu* apu, const ApuPortWrite *w) {"
APU_HELPER_NEW = r"""/* UR_QA01_RF032_TARGET_ECHO: read-only, opt-in, first IPL handshake. */
static void ur_qa01_rf032_port(Apu* apu, const char* kind,
                             uint8_t port, uint8_t value,
                             uint64_t guest, uint64_t target) {
  static unsigned count;
  if (port != 0 || !getenv("UR_QA01_RF032_TARGET_ECHO") ||
      apu->portClock < 103322420ull || apu->portClock > 103323100ull) return;
  if (count++ < 2000) {
    fprintf(stderr,
      "QA01RF032 kind=%s age=%llu guest=%llu target=%llu port=%u value=%02X in=%02X out=%02X pc=%04X qhead=%u qtail=%u guestanchor=%llu targetanchor=%llu\n",
      kind, (unsigned long long)apu->portClock,
      (unsigned long long)guest, (unsigned long long)target,
      (unsigned)port, (unsigned)value,
      (unsigned)apu->inPorts[0], (unsigned)apu->outPorts[0],
      (unsigned)apu->spc->pc,
      (unsigned)apu->portQHead, (unsigned)apu->portQTail,
      (unsigned long long)apu->portGuestAnchor,
      (unsigned long long)apu->portTargetAnchor);
  } else if (count == 2001) {
    fprintf(stderr, "QA01RF032_TRUNCATED\n");
  }
}

""" + APU_HELPER_OLD

APU_APPLY_OLD = "  apu_writePortNow(apu, w->port, w->val);"
APU_APPLY_NEW = """  ur_qa01_rf032_port(apu, "apply", w->port, w->val, 0, w->target_cycle);
""" + APU_APPLY_OLD

APU_SCHEDULE_OLD = """  if ((port & 3) == 0) ur_qa01_rf030_native(apu, "schedule", val);
  return true;"""
APU_SCHEDULE_NEW = """  if ((port & 3) == 0) ur_qa01_rf030_native(apu, "schedule", val);
  ur_qa01_rf032_port(apu, "schedule", (uint8_t)(port & 3), val, guest_cycle, w->target_cycle);
  return true;"""

SNES_READ_OLD = """    uint8_t v = snes->apu->outPorts[adr & 0x3];
    v = rtl_apu_port_observers_read(0x2100 + adr, v);
    audio_trace_on_cpu_port_read((uint8_t)(adr & 0x3), v);
    RtlApuUnlock();"""
SNES_READ_NEW = r"""    uint8_t v = snes->apu->outPorts[adr & 0x3];
    uint8_t raw_apu_value = v;
    v = rtl_apu_port_observers_read(0x2100 + adr, v);
    audio_trace_on_cpu_port_read((uint8_t)(adr & 0x3), v);
    /* UR_QA01_RF032_TARGET_ECHO: actual native CPU $2140 read, AFTER sync. */
    if ((adr & 3) == 0 && getenv("UR_QA01_RF032_TARGET_ECHO") &&
        snes->apu->portClock >= 103322420ull &&
        snes->apu->portClock <= 103323100ull) {
      static unsigned rf032_cpu_read_count;
      if (rf032_cpu_read_count++ < 2000) {
        fprintf(stderr,
          "QA01RF032 kind=cpu-poll age=%llu guest=0 target=0 port=0 value=%02X raw=%02X in=%02X out=%02X pc=%04X qhead=%u qtail=%u guestanchor=%llu targetanchor=%llu\n",
          (unsigned long long)snes->apu->portClock,
          (unsigned)v, (unsigned)raw_apu_value,
          (unsigned)snes->apu->inPorts[0], (unsigned)snes->apu->outPorts[0],
          (unsigned)snes->apu->spc->pc,
          (unsigned)snes->apu->portQHead, (unsigned)snes->apu->portQTail,
          (unsigned long long)snes->apu->portGuestAnchor,
          (unsigned long long)snes->apu->portTargetAnchor);
      } else if (rf032_cpu_read_count == 2001) {
        fprintf(stderr, "QA01RF032_CPU_TRUNCATED\n");
      }
    }
    RtlApuUnlock();"""

def _pin(source: str, anchors: tuple[tuple[str, str], ...], name: str) -> str:
    if MARK in source:
        # Marker occurs exactly once per target file, and every replacement
        # must be present. Refuse a partial/tampered instrumentation stage.
        if not all(source.count(new) == 1 for _, new in anchors):
            raise ValueError(f"partial {name} RF032 source stage")
        return source
    if not all(source.count(old) == 1 for old, _ in anchors):
        raise ValueError(f"unknown pinned {name} source or absent RF030 stage")
    for old, new in anchors:
        source = source.replace(old, new, 1)
    return source

def patch_apu(source: str) -> str:
    if 'ur_qa01_rf030_native(apu, "schedule", val)' not in source:
        raise ValueError("RF030 native source prerequisite absent")
    return _pin(source, ((APU_HELPER_OLD, APU_HELPER_NEW),
                         (APU_APPLY_OLD, APU_APPLY_NEW),
                         (APU_SCHEDULE_OLD, APU_SCHEDULE_NEW)), "Baldosa apu.c")

def patch_snes(source: str) -> str:
    return _pin(source, ((SNES_READ_OLD, SNES_READ_NEW),), "Baldosa snes.c")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    a = p.parse_args()
    root = a.game.resolve()
    targets = ((root / APU, patch_apu), (root / SNES, patch_snes))
    # Do not leave half an installed observer when a second source is unknown.
    updates = []
    for path, patch in targets:
        if not path.is_file():
            p.error(f"missing pinned source {path}")
        original = path.read_text(encoding="utf-8")
        updates.append((path, original, patch(original)))
    for path, old, new in updates:
        if old != new:
            path.write_text(new, encoding="utf-8")
        print(f"RF032 {path}: {'unchanged' if old == new else 'read-only observer staged'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

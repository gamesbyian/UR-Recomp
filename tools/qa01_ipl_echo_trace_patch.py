#!/usr/bin/env python3
"""RF-030 disposable read-only original/native CPU-to-SPC IPL echo observer.

No gameplay corrections. Install only into exact pinned Snes9x and Baldosa
checkouts, after the existing RF-015..028 research stage. Actual source clocks
stay independent; neither trace format silently assumes frame equivalence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA01_RF030_IPL_ECHO"
ORIGINAL_CORE = Path("apu/bapu/smp/core.cpp")
ORIGINAL_APU = Path("apu/apu.cpp")
NATIVE_APU = Path("snesrecomp/runner/src/snes/apu.c")

CORE_HEAD = """void SMP::tick() {
  timer0.tick();"""
CORE_REPLACEMENT = """uint64_t ur_qa01_rf030_spc_age = 0; /* UR_QA01_RF030_IPL_ECHO */

static bool ur_qa01_rf030_enabled() {
  static const bool on = getenv("UR_QA01_IPL_ECHO_TRACE") != nullptr;
  return on;
}
static bool ur_qa01_rf030_original_window() {
  return ur_qa01_rf030_enabled() &&
         ur_qa01_rf030_spc_age >= 103300000ull &&
         ur_qa01_rf030_spc_age <= 103345000ull;
}
static unsigned ur_qa01_rf030_spc_records = 0;

void SMP::tick() {
  ++ur_qa01_rf030_spc_age;
  timer0.tick();"""
TICK_BULK_OLD = """void SMP::tick(unsigned clocks) {
  timer0.tick(clocks);"""
TICK_BULK_NEW = """void SMP::tick(unsigned clocks) {
  ur_qa01_rf030_spc_age += clocks;
  timer0.tick(clocks);"""
READ_OLD = """uint8 SMP::op_read(uint16 addr) {
  tick();
  if((addr & 0xfff0) == 0x00f0) return mmio_read(addr);
  if(addr >= 0xffc0 && status.iplrom_enable) return iplrom[addr & 0x3f];
  return apuram[addr];
}"""
READ_NEW = """uint8 SMP::op_read(uint16 addr) {
  tick();
  if (addr == 0xf4) {
    uint8 observed = mmio_read(addr);
    if (ur_qa01_rf030_original_window()) {
      if (ur_qa01_rf030_spc_records++ < 2000)
        fprintf(stderr, "QA01IPLORIG side=spc kind=read frame=0 v=%u h=%d age=%llu pc=%04X op=%02X value=%02X ipl=%u\\n",
                (unsigned)::CPU.V_Counter,
                (int)::CPU.Cycles, (unsigned long long)ur_qa01_rf030_spc_age,
                (unsigned)regs.pc, (unsigned)opcode_number,
                (unsigned)observed, (unsigned)status.iplrom_enable);
      else if (ur_qa01_rf030_spc_records == 2001)
        fprintf(stderr, "QA01IPLORIG_TRUNCATED\\n");
    }
    return observed;
  }
  if((addr & 0xfff0) == 0x00f0) return mmio_read(addr);
  if(addr >= 0xffc0 && status.iplrom_enable) return iplrom[addr & 0x3f];
  return apuram[addr];
}"""
WRITE_OLD = """void SMP::op_write(uint16 addr, uint8 data) {
  tick();
  if((addr & 0xfff0) == 0x00f0) mmio_write(addr, data);
  apuram[addr] = data;  //all writes go to RAM, even MMIO writes
}"""
WRITE_NEW = """void SMP::op_write(uint16 addr, uint8 data) {
  tick();
  if((addr & 0xfff0) == 0x00f0) mmio_write(addr, data);
  if (addr == 0xf4 && ur_qa01_rf030_original_window()) {
    if (ur_qa01_rf030_spc_records++ < 2000)
      fprintf(stderr, "QA01IPLORIG side=spc kind=echo frame=0 v=%u h=%d age=%llu pc=%04X op=%02X value=%02X ipl=%u\\n",
              (unsigned)::CPU.V_Counter,
              (int)::CPU.Cycles, (unsigned long long)ur_qa01_rf030_spc_age,
              (unsigned)regs.pc, (unsigned)opcode_number,
              (unsigned)data, (unsigned)status.iplrom_enable);
    else if (ur_qa01_rf030_spc_records == 2001)
      fprintf(stderr, "QA01IPLORIG_TRUNCATED\\n");
  }
  apuram[addr] = data;  //all writes go to RAM, even MMIO writes
}"""

ORIGINAL_APU_ANCHOR = """CPU cpu;
} // namespace SNES"""
ORIGINAL_APU_REPLACEMENT = """CPU cpu;
extern uint64_t ur_qa01_rf030_spc_age; /* UR_QA01_RF030_IPL_ECHO */
} // namespace SNES"""
CPU_READ_OLD = """uint8 S9xAPUReadPort(int port)
{
    S9xAPUExecute();
    return ((uint8)SNES::smp.port_read(port & 3));
}"""
CPU_READ_NEW = """uint8 S9xAPUReadPort(int port)
{
    S9xAPUExecute();
    uint8 observed = (uint8)SNES::smp.port_read(port & 3);
    if ((port & 3) == 0 && getenv("UR_QA01_IPL_ECHO_TRACE") &&
        SNES::ur_qa01_rf030_spc_age >= 103300000ull &&
        SNES::ur_qa01_rf030_spc_age <= 103345000ull) {
        static unsigned n = 0;
        if (n++ < 2000)
            fprintf(stderr, "QA01IPLORIG side=cpu kind=poll frame=0 v=%u h=%d age=%llu pc=0000 op=00 value=%02X ipl=0\\n",
                    (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
                    (unsigned long long)SNES::ur_qa01_rf030_spc_age, (unsigned)observed);
        else if (n == 2001) fprintf(stderr, "QA01IPLORIG_CPU_TRUNCATED\\n");
    }
    return observed;
}"""
CPU_WRITE_OLD = """void S9xAPUWritePort(int port, uint8 byte)
{
    S9xAPUExecute();
    SNES::cpu.port_write(port & 3, byte);
}"""
CPU_WRITE_NEW = """void S9xAPUWritePort(int port, uint8 byte)
{
    S9xAPUExecute();
    SNES::cpu.port_write(port & 3, byte);
    if ((port & 3) == 0 && getenv("UR_QA01_IPL_ECHO_TRACE") &&
        SNES::ur_qa01_rf030_spc_age >= 103300000ull &&
        SNES::ur_qa01_rf030_spc_age <= 103345000ull) {
        static unsigned n = 0;
        if (n++ < 2000)
            fprintf(stderr, "QA01IPLORIG side=cpu kind=write frame=0 v=%u h=%d age=%llu pc=0000 op=00 value=%02X ipl=0\\n",
                    (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
                    (unsigned long long)SNES::ur_qa01_rf030_spc_age, (unsigned)byte);
        else if (n == 2001) fprintf(stderr, "QA01IPLORIG_CPU_TRUNCATED\\n");
    }
}"""

NATIVE_HELPER_ANCHOR = """void apu_writePortNow(Apu* apu, uint8_t port, uint8_t val) {"""
NATIVE_HELPER = """/* UR_QA01_RF030_IPL_ECHO; read-only opt-in SPC/CPU transport observer.
 * Do not interpret portClock as an original Snes9x CPU clock or frame. */
static void ur_qa01_rf030_native(Apu* apu, const char *kind, uint8_t val) {
  static int initialized = 0, enabled;
  static unsigned count;
  if (!initialized) {
    enabled = getenv("UR_QA01_IPL_ECHO_TRACE") != NULL;
    initialized = 1;
  }
  if (!enabled || apu->portClock < 103300000ull ||
      apu->portClock > 103345000ull) return;
  if (count++ < 2000)
    fprintf(stderr, "QA01IPLNATIVE kind=%s age=%llu pc=%04X value=%02X q=%u in=%02X out=%02X\\n",
            kind, (unsigned long long)apu->portClock,
            (unsigned)apu->spc->pc, (unsigned)val,
            apu->portQTail - apu->portQHead,
            (unsigned)apu->inPorts[0], (unsigned)apu->outPorts[0]);
  else if (count == 2001)
    fprintf(stderr, "QA01IPLNATIVE_TRUNCATED\\n");
}

""" + NATIVE_HELPER_ANCHOR
NATIVE_APPLY_OLD = """  apu->inPorts[port] = val;
  audio_trace_on_cpu_port_apply(port, val);"""
NATIVE_APPLY_NEW = """  apu->inPorts[port] = val;
  if (port == 0) ur_qa01_rf030_native(apu, "apply", val);
  audio_trace_on_cpu_port_apply(port, val);"""
NATIVE_SCHEDULE_OLD = """  apu->portLastGuest = guest_cycle;
  apu->portLastTarget = target;
  return true;"""
NATIVE_SCHEDULE_NEW = """  apu->portLastGuest = guest_cycle;
  apu->portLastTarget = target;
  if ((port & 3) == 0) ur_qa01_rf030_native(apu, "schedule", val);
  return true;"""
NATIVE_READ_OLD = """      uint8_t v = apu->inPorts[adr - 0xf4];
      audio_trace_on_spc_port_read((uint8_t)(adr - 0xf4), v);"""
NATIVE_READ_NEW = """      uint8_t v = apu->inPorts[adr - 0xf4];
      if (adr == 0xf4) ur_qa01_rf030_native(apu, "read", v);
      audio_trace_on_spc_port_read((uint8_t)(adr - 0xf4), v);"""
NATIVE_ECHO_OLD = """      audio_trace_on_spc_port_write((uint8_t)(adr - 0xf4), val);
      apu->outPorts[adr - 0xf4] = val;"""
NATIVE_ECHO_NEW = """      audio_trace_on_spc_port_write((uint8_t)(adr - 0xf4), val);
      apu->outPorts[adr - 0xf4] = val;
      if (adr == 0xf4) ur_qa01_rf030_native(apu, "echo", val);"""


def _splice(text: str, substitutions: tuple[tuple[str, str], ...], scope: str) -> str:
    if MARK in text:
        if not all(text.count(new) == 1 for _, new in substitutions):
            raise ValueError(f"partial/tampered RF-030 {scope} stage")
        return text
    for old, new in substitutions:
        if text.count(old) != 1:
            raise ValueError(f"unknown pinned {scope}: missing or duplicate anchor")
        text = text.replace(old, new, 1)
    return text


def patch_original_core(text: str) -> str:
    return _splice(text, (
        (CORE_HEAD, CORE_REPLACEMENT), (TICK_BULK_OLD, TICK_BULK_NEW),
        (READ_OLD, READ_NEW), (WRITE_OLD, WRITE_NEW)), "Snes9x SMP")


def patch_original_apu(text: str) -> str:
    return _splice(text, ((ORIGINAL_APU_ANCHOR, ORIGINAL_APU_REPLACEMENT),
                          (CPU_READ_OLD, CPU_READ_NEW),
                          (CPU_WRITE_OLD, CPU_WRITE_NEW)), "Snes9x CPU/APU")


def patch_native_apu(text: str) -> str:
    return _splice(text, ((NATIVE_HELPER_ANCHOR, NATIVE_HELPER),
                          (NATIVE_APPLY_OLD, NATIVE_APPLY_NEW),
                          (NATIVE_SCHEDULE_OLD, NATIVE_SCHEDULE_NEW),
                          (NATIVE_READ_OLD, NATIVE_READ_NEW),
                          (NATIVE_ECHO_OLD, NATIVE_ECHO_NEW)), "Baldosa APU")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--original-root", type=Path)
    p.add_argument("--game", type=Path)
    a = p.parse_args()
    if a.side == "original":
        if a.original_root is None or a.game is not None:
            p.error("original needs --original-root only")
        root = a.original_root.resolve()
        targets = [(root / ORIGINAL_CORE, patch_original_core),
                   (root / ORIGINAL_APU, patch_original_apu)]
    else:
        if a.game is None or a.original_root is not None:
            p.error("native needs --game only")
        root = a.game.resolve()
        targets = [(root / NATIVE_APU, patch_native_apu)]
    for path, patch in targets:
        if not path.is_file():
            p.error(f"missing exact pinned checkout source {path}")
        old = path.read_text(encoding="utf-8")
        new = patch(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
        print(f"RF-030 {path}: {'unchanged' if new == old else 'instrumented'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

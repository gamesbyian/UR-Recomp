#!/usr/bin/env python3
"""QA-01/RF-015 disposable original/native APU-result-edge observers.

Opt-in source edits ONLY for an independently checked-out, disposable Snes9x
cpuexec.cpp and pinned Baldosa snesrecomp/runner/src/common_rtl.c. This tool
does not patch ROM, persistent framework checkouts, generated guest logic,
controller inputs or result timing. Source/native frame clocks remain separate.
The resulting logs must be executed and qualified independently.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SOURCE_MARKER = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
NATIVE_READ_MARKER = """  } else if (reg >= 0x2140 && reg < 0x2180) {
    // APU read — route through emulator (real SPC700 outPorts).
    return snes_read(g_snes, reg);
"""
NATIVE_WRITE_MARKER = """void WriteRegWord(uint16 reg, uint16 value) {
  if (reg == 0x2118) {"""
SOURCE_STAMP = "UR_QA01_RF015_ORIGINAL_APU_PC_V1"
NATIVE_STAMP = "UR_QA01_RF015_BALDOSA_APU_PORT_V1"
SOURCE_LIMIT = 6000
NATIVE_LIMIT = 6000

SOURCE_BEFORE = r"""
            /* UR_QA01_RF015_ORIGINAL_APU_PC_V1: never changes guest state.
             * Execute true original USA PC, store pre/post register+queue
             * state, but do NOT equate ICPU.Frame to native host frames. */
            static const unsigned ur_rf015_first = []() -> unsigned {
                const char *p = getenv("UR_QA01_APU_ORIGINAL_FIRST");
                return p ? (unsigned)strtoul(p, nullptr, 10) : 0xffffffffu;
            }();
            static const unsigned ur_rf015_last = []() -> unsigned {
                const char *p = getenv("UR_QA01_APU_ORIGINAL_LAST");
                return p ? (unsigned)strtoul(p, nullptr, 10) : 0u;
            }();
            static unsigned ur_rf015_emitted = 0;
            const uint32 ur_rf015_pc = ((uint32)Registers.PB << 16) | Registers.PCw;
            const bool ur_rf015_target =
                ur_rf015_first <= (unsigned)ICPU.Frame &&
                (unsigned)ICPU.Frame <= ur_rf015_last &&
                (ur_rf015_pc == 0x82803Cu || /* 8-bit $2142 read */
                 ur_rf015_pc == 0x828043u || /* APU toggle branch */
                 ur_rf015_pc == 0x82804Eu || /* empty-queue branch */
                 ur_rf015_pc == 0x828059u || /* toggle update */
                 ur_rf015_pc == 0x828066u || /* queue read pointer */
                 ur_rf015_pc == 0x82806Du || /* 16-bit port write */
                 ur_rf015_pc == 0x80FADBu || /* wait completed JSR */
                 ur_rf015_pc == 0x80FAE2u); /* cursor timer DEC */
            const unsigned ur_rf015_f0 = ur_rf015_target ? (unsigned)ICPU.Frame : 0u;
            const unsigned ur_rf015_v0 = ur_rf015_target ? (unsigned)CPU.V_Counter : 0u;
            const int ur_rf015_h0 = ur_rf015_target ? (int)CPU.Cycles : 0;
            const uint16 ur_rf015_a0 = ur_rf015_target ? Registers.A.W : 0;
            const uint8 ur_rf015_p0 = ur_rf015_target ? Registers.PL : 0;
            const uint8 ur_rf015_db0 = ur_rf015_target ? Registers.DB : 0;
            const uint8 ur_rf015_rd0 = ur_rf015_target ? Memory.RAM[0x2000] : 0;
            const uint8 ur_rf015_wr0 = ur_rf015_target ? Memory.RAM[0x2002] : 0;
            const uint8 ur_rf015_ack0 = ur_rf015_target ? Memory.RAM[0x2004] : 0;
            const uint8 ur_rf015_c60 = ur_rf015_target ? Memory.RAM[0x00C6] : 0;
"""

SOURCE_AFTER = r"""
            if (ur_rf015_target) {
                if (ur_rf015_emitted < 6000u)
                    fprintf(stderr,
                        "QA01APUORIG f0=%u f1=%u v0=%u v1=%u h0=%d h1=%d pc=%06X next=%06X op=%02X p0=%02X p1=%02X db0=%02X db1=%02X a0=%04X a1=%04X rd0=%02X rd1=%02X wr0=%02X wr1=%02X ack0=%02X ack1=%02X c60=%02X c61=%02X\n",
                        ur_rf015_f0, (unsigned)ICPU.Frame,
                        ur_rf015_v0, (unsigned)CPU.V_Counter,
                        ur_rf015_h0, (int)CPU.Cycles,
                        (unsigned)ur_rf015_pc,
                        (unsigned)(((uint32)Registers.PB << 16) | Registers.PCw),
                        (unsigned)Op,
                        (unsigned)ur_rf015_p0, (unsigned)Registers.PL,
                        (unsigned)ur_rf015_db0, (unsigned)Registers.DB,
                        (unsigned)ur_rf015_a0, (unsigned)Registers.A.W,
                        (unsigned)ur_rf015_rd0, (unsigned)Memory.RAM[0x2000],
                        (unsigned)ur_rf015_wr0, (unsigned)Memory.RAM[0x2002],
                        (unsigned)ur_rf015_ack0, (unsigned)Memory.RAM[0x2004],
                        (unsigned)ur_rf015_c60, (unsigned)Memory.RAM[0x00C6]);
                else if (ur_rf015_emitted == 6000u)
                    fprintf(stderr, "QA01APUORIG_TRUNCATED limit=6000\n");
                ++ur_rf015_emitted;
            }
"""


def patch_original(source: str) -> str:
    if SOURCE_STAMP in source:
        raise ValueError("already installed original APU opcode observer")
    if source.count(SOURCE_MARKER) != 1:
        raise ValueError("ambiguous original pinned Snes9x opcode dispatch")
    replacement = SOURCE_BEFORE + SOURCE_MARKER + "\n" + SOURCE_AFTER
    if replacement.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise ValueError("instrumentation cannot duplicate original CPU dispatch")
    return source.replace(SOURCE_MARKER, replacement, 1)


NATIVE_HELPER = r"""
/* UR_QA01_RF015_BALDOSA_APU_PORT_V1
 * Bounded read-only diagnostic; executes only if the two opt-in frame bounds
 * are set. 'f' is the native framework's own host index, not Snes9x ICPU.Frame.
 * Port 2's single-byte return is logged AFTER SPC sync, and is never changed.
 * 'guest_apu_cycle' is the framework's estimated synchronized APU clock.
 */
static void ur_rf015_apu_log(uint16 reg, uint16 val, unsigned width, char side) {
  static int initialized = 0;
  static unsigned first, last, count;
  if (!initialized) {
    const char *a = getenv("UR_QA01_APU_NATIVE_FIRST");
    const char *b = getenv("UR_QA01_APU_NATIVE_LAST");
    first = a ? (unsigned)strtoul(a, NULL, 10) : 0xffffffffu;
    last = b ? (unsigned)strtoul(b, NULL, 10) : 0u;
    initialized = 1;
  }
  if (reg != 0x2142 || first > last ||
      (unsigned)snes_frame_counter < first ||
      (unsigned)snes_frame_counter > last)
    return;
  if (count >= 6000u) {
    if (count == 6000u)
      fprintf(stderr, "QA01APUNATIVE_TRUNCATED limit=6000\n");
    ++count;
    return;
  }
  ++count;
  fprintf(stderr,
      "QA01APUNATIVE f=%d dir=%c reg=%04X width=%u value=%04X cpu_master=%llu apu_cycle=%llu spc_portclock=%llu frame_clock=%u extended=%u memsel=%u rd=%02X wr=%02X ack=%02X c6=%02X\n",
      snes_frame_counter, side, (unsigned)reg, width, (unsigned)val,
      (unsigned long long)g_cpu.master_cycles,
      (unsigned long long)rtl_apu_guest_cycle(),
      (unsigned long long)(g_snes && g_snes->apu ? g_snes->apu->portClock : 0u),
      (unsigned)g_apu_frame_time_valid, (unsigned)g_extended_frame_timing,
      (unsigned)g_memsel, (unsigned)g_ram[0x2000],
      (unsigned)g_ram[0x2002], (unsigned)g_ram[0x2004],
      (unsigned)g_ram[0x00C6]);
}
"""

# At the $2142 APU read, note actual outgoing read value and effective SPC
# clock AFTER the native model has synchronized its SPC700. Do not log the
# pre-sync port latch as though it were the CPU's observed value.
NATIVE_READ = """  } else if (reg >= 0x2140 && reg < 0x2180) {
    // APU read — route through emulator (real SPC700 outPorts).
    uint8 observed = snes_read(g_snes, reg);
    if (reg == 0x2142)
      ur_rf015_apu_log(reg, observed, 1u, 'R');
    return observed;
"""

NATIVE_WRITE = """void WriteRegWord(uint16 reg, uint16 value) {
  if (reg == 0x2142)
    ur_rf015_apu_log(reg, value, 2u, 'W');
  if (reg == 0x2118) {"""


def patch_native(source: str) -> str:
    if NATIVE_STAMP in source:
        raise ValueError("already installed native APU port observer")
    if source.count(NATIVE_READ_MARKER) != 1:
        raise ValueError("ambiguous Baldosa APU read dispatch")
    if source.count(NATIVE_WRITE_MARKER) != 1:
        raise ValueError("ambiguous Baldosa 16-bit register writer")
    if source.count("static uint64_t rtl_apu_guest_cycle(void)") != 1:
        raise ValueError("Baldosa guest APU clock definition moved")
    if source.count("static bool g_apu_frame_time_valid;") != 1:
        raise ValueError("Baldosa frame-clock mode declaration moved")
    out = source.replace(NATIVE_READ_MARKER, NATIVE_READ, 1)
    out = out.replace(NATIVE_WRITE_MARKER, NATIVE_WRITE, 1)
    # Helper definition must come after rtl_apu_guest_cycle and globals,
    # but before the first modified ReadRegOpenBus call site.
    anchor = "uint8 ReadRegOpenBus(uint16 reg, uint8 open_bus) {"
    if out.count(anchor) != 1:
        raise ValueError("Baldosa APU port observer insertion point drifted")
    out = out.replace(anchor, NATIVE_HELPER + "\n" + anchor, 1)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tier", choices=("original", "native"))
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    p = args.source.resolve()
    if args.tier == "original":
        if p.name != "cpuexec.cpp" or "snes9x-libretro" not in p.parts:
            parser.error("only a disposable snes9x-libretro/cpuexec.cpp")
    else:
        if p.name != "common_rtl.c" or "snesrecomp" not in p.parts:
            parser.error("only a disposable Baldosa snesrecomp/runner/src/common_rtl.c")
    original = p.read_text(encoding="utf-8")
    p.write_text((patch_original(original) if args.tier == "original"
                  else patch_native(original)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

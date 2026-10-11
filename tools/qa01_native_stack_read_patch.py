#!/usr/bin/env python3
"""Observe real native read attempts touching $01DD/$01DE in disposable Baldosa.

Requires the existing frame gate and NMI writer beam patch. This instruments
the pinned cpu_read8/cpu_read16 WRAM branches, including native word reads
which bypass cpu_read8 entirely. It must not alter returned values, frame
pacing, generated guest code, SRAM, or original source game.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import qa01_native_nmi_beam_patch as beam
import qa01_native_switcher_stack_gate as gate

STAMP = "UR_QA01_NATIVE_STACK_BUS_READ_V1"
B8 = "    if (off >= 0) return cpu_latch_read8(cpu, cpu->ram[off]);\n"
B16 = """        uint8 hi = (hi_off >= 0)
            ? cpu->ram[hi_off]
            : cpu_read8(cpu, bank, hi_addr);
        return cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8));
"""
HEADER = 'extern Snes *g_snes;\n'
LOGGER_START = '    fprintf(g_wlog_addr_fp, "f%-6d %02X:%04X=%0*X w%d %s%s%s",\n'
LOGGER_END = "    fputc('\\n', g_wlog_addr_fp);\n    if (g_wlog_halt_off >= 0) {\n"


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("native read scope already installed")
    if gate.STAMP not in source or beam.STAMP not in source:
        raise ValueError("original native frame-gate and writer-beam prerequisites absent")
    if any(source.count(marker) != 1 for marker in (B8, B16, HEADER, LOGGER_START, LOGGER_END)):
        raise ValueError("pinned Baldosa cpu_read8/16 WRAM source marker absent or ambiguous")
    read_fn = r"""
/* UR_QA01_NATIVE_STACK_BUS_READ_V1: never change guest-visible return data.
 * Native bus attempts in fresh replay f5778..5782; not instruction-PC parity.
 * Output is optional and bounded. S is register value *at* bus helper call. */
static int ur_qa01_read_suppressed = 0;
static void ur_qa01_read_01dd(CpuState *cpu, uint8 bank, uint16 addr,
                              uint16 value, unsigned width) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    if (ur_qa01_read_suppressed) return;
    if (snes_frame_counter < 5778 || snes_frame_counter > 5782)
        return;
    if (!(width == 1 ? (addr == 0x01DDu || addr == 0x01DEu)
          : (addr >= 0x01DCu && addr <= 0x01DEu)))
        return;
    static int ready = 0;
    static FILE *fp = NULL;
    static unsigned count = 0;
    if (!ready) {
        const char *out = getenv("UR_QA_NATIVE_STACK_READ_PATH");
        if (out && out[0]) {
            fp = fopen(out, "w");
            if (fp) setvbuf(fp, NULL, _IONBF, 0);
        }
        ready = 1;
    }
    if (!fp || count >= 512) return;
    ++count;
    fprintf(fp, "QANATIVEREAD f=%d bank=%02X addr=%04X width=%u value=%04X"
            " A=%04X S=%04X M=%u scope=%s\n",
            snes_frame_counter, (unsigned)bank, (unsigned)addr, width,
            (unsigned)(width == 1 ? (value & 0xFFu) : value),
            (unsigned)cpu->A, (unsigned)cpu->S, (unsigned)(cpu->m_flag & 1),
            g_last_recomp_func ? g_last_recomp_func : "?");
}
"""
    source = source.replace(HEADER, HEADER + read_fn, 1)
    # The pinned WRAM *write* logger prints extensive read8/read16 snapshot
    # fields. Those diagnostic reads must not impersonate game consumers.
    source = source.replace(LOGGER_START,
                            "    ++ur_qa01_read_suppressed;\n"
                            + LOGGER_START, 1)
    source = source.replace(LOGGER_END,
                            "    --ur_qa01_read_suppressed;\n"
                            + LOGGER_END, 1)
    source = source.replace(B8, """    if (off >= 0) {
        ur_qa01_read_01dd(cpu, bank, addr, cpu->ram[off], 1);
        return cpu_latch_read8(cpu, cpu->ram[off]);
    }
""", 1)
    source = source.replace(B16, B16.replace(
        "        return cpu_latch_read16",
        "        ur_qa01_read_01dd(cpu, bank, addr,\n"
        "                            (uint16)lo | ((uint16)hi << 8), 2);\n"
        "        return cpu_latch_read16"), 1)
    return source


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    target = args.source.resolve()
    if target.name != "cpu_state.c" or "snesrecomp" not in target.parts:
        raise ValueError("requires disposable snesrecomp/.../cpu_state.c")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

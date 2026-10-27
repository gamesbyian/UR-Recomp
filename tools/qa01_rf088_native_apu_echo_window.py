#!/usr/bin/env python3
"""RF088: opt-in native APU echo read/write witness in the already-pinned CPU bus.

Patch only the disposable Baldosa runner, after RF086 and before compilation.
Capture $2140-$2143 traffic across the first Zoo seek/upload boundary,
including the actual pointer at each access; do not assume it is C6B0. The CPU bus performs
exactly its original ReadReg/WriteReg operations; observations follow them.
This is native-only evidence, not an original/native clock registration.
"""
from __future__ import annotations

import argparse
from pathlib import Path

FILE = Path("snesrecomp/runner/src/cpu_state.c")
STAMP = "UR_QA01_RF088_NATIVE_APU_ECHO_WINDOW"
ENTRY = "uint8 cpu_read8(CpuState *cpu, uint8 bank, uint16 addr) {"
READ8 = "        return cpu_latch_read8(cpu, ReadRegOpenBus(addr, cpu->open_bus));"
READ16 = ("        if (addr >= 0x2140 && addr <= 0x217F)\n"
          "            return cpu_latch_read16(cpu, ReadRegWord(addr));")
WRITE8 = ("    if (is_hw_reg(bank, addr)) { cpu_pace_cycles(addr); "
          "cpu_hw_log(addr, 0, v); WriteReg(addr, v); return; }")
WRITE16 = ("        cpu_hw_log(addr, 0, v);\n"
           "        WriteRegWord(addr, v);\n"
           "        cpu->open_bus = (uint8)(v >> 8);")

HOOK = r'''/* UR_QA01_RF088_NATIVE_APU_ECHO_WINDOW
 * Native CPU bus witness only. Function label is advisory across interpreter
 * fallback; native_master is not registered to original Snes9x v/h.
 * All ReadReg/WriteReg calls and guest bus charges are unchanged.
 */
extern int snes_frame_counter;
extern const char *g_last_recomp_func;
static unsigned ur_rf088_rows;
static void ur_rf088_note(CpuState *cpu, uint8 bank, uint16 addr,
                          unsigned width, unsigned value, char kind) {
    static int enabled = -1;
    if (enabled < 0) {
        const char *flag = getenv("UR_QA01_RF088_NATIVE_APU_ECHO");
        enabled = flag && flag[0] == '1' && flag[1] == '\0';
    }
    /* Keep the actual four APU ports narrow, but do not preselect the
     * unproven pointer phase. The sequence-10 combined run produced zero
     * RF088 rows; log the pointer alongside each observed port access. */
    if (!enabled || snes_frame_counter < 6055 || snes_frame_counter > 6060 ||
        (addr < 0x2140 || addr > 0x2143)) return;
    if (++ur_rf088_rows > 32768u) {
        if (ur_rf088_rows == 32769u)
            fprintf(stderr, "QA01RF088NATIVE_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
        "QA01RF088NATIVE seq=%u f=%d kind=%c width=%u bank=%02X"
        " addr=%04X val=%04X native_master=%llu ptr=%02X%02X scope=%s\n",
        ur_rf088_rows, snes_frame_counter, kind, width, (unsigned)bank,
        (unsigned)addr, value, (unsigned long long)cpu->master_cycles,
        (unsigned)cpu->ram[0x64], (unsigned)cpu->ram[0x63],
        g_last_recomp_func ? g_last_recomp_func : "unknown");
}
'''

READ8_REPLACE = ("        uint8 ur_rf088_value = ReadRegOpenBus(addr, cpu->open_bus);\n"
                 "        ur_rf088_note(cpu, bank, addr, 1u, ur_rf088_value, 'R');\n"
                 "        return cpu_latch_read8(cpu, ur_rf088_value);")
READ16_REPLACE = ("        if (addr >= 0x2140 && addr <= 0x217F) {\n"
                  "            uint16 ur_rf088_value = ReadRegWord(addr);\n"
                  "            ur_rf088_note(cpu, bank, addr, 2u, ur_rf088_value, 'R');\n"
                  "            return cpu_latch_read16(cpu, ur_rf088_value);\n"
                  "        }")
WRITE8_REPLACE = ("    if (is_hw_reg(bank, addr)) { cpu_pace_cycles(addr); "
                  "cpu_hw_log(addr, 0, v); WriteReg(addr, v); "
                  "ur_rf088_note(cpu, bank, addr, 1u, v, 'W'); return; }")
WRITE16_REPLACE = ("        cpu_hw_log(addr, 0, v);\n"
                   "        WriteRegWord(addr, v);\n"
                   "        ur_rf088_note(cpu, bank, addr, 2u, v, 'W');\n"
                   "        cpu->open_bus = (uint8)(v >> 8);")


def patch(source: str) -> str:
    if STAMP in source or "ur_rf088_note(" in source:
        raise ValueError("RF088 already or partially applied")
    for anchor in (ENTRY, READ8, READ16, WRITE8, WRITE16):
        if source.count(anchor) != 1:
            raise ValueError("RF088 pinned bus anchor missing or ambiguous")
    calls = ("ReadRegOpenBus(", "ReadRegWord(", "WriteReg(",
             "WriteRegWord(", "cpu_pace_cycles(", "cpu_pace_cycles_word(",
             "cpu_read8_paced(", "cpu_read16_paced(",
             "cpu_write8_paced(", "cpu_write16_paced(")
    before = tuple(source.count(c) for c in calls)
    source = source.replace(ENTRY, HOOK + "\n" + ENTRY, 1)
    for old, new in ((READ8, READ8_REPLACE), (READ16, READ16_REPLACE),
                     (WRITE8, WRITE8_REPLACE), (WRITE16, WRITE16_REPLACE)):
        source = source.replace(old, new, 1)
    if tuple(source.count(c) for c in calls) != before:
        raise AssertionError("RF088 altered real guest read/write/pacing population")
    if source.count(STAMP) != 1 or source.count("ur_rf088_note(cpu,") != 4:
        raise AssertionError("RF088 hook population invalid")
    return source


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    path = args.root / FILE
    if not path.is_file() or path.is_symlink():
        ap.error("pinned disposable cpu_state.c missing or symlinked")
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    print("RF088 native APU echo witness staged in disposable CPU bus")


if __name__ == "__main__":
    main()

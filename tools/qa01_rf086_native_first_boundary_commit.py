#!/usr/bin/env python3
"""RF086: witness *committed* native sound-DP bus writes in disposable cpu_state.c.

The retained first-boundary WLOG names are g_last_recomp_func labels, NOT
proof that those names have generated C definitions. The actual pinned bank82
has only FastRom variants. Hook the common WRAM commit instead: both AOT and
interpreter-fallback stores pass through cpu_write8/cpu_write16. No extra
guest bus operations, changed write values, or guest clock charges.
"""
from __future__ import annotations

import argparse
from pathlib import Path

FILE = Path("snesrecomp/runner/src/cpu_state.c")
STAMP = "UR_QA01_RF086_NATIVE_WRAM_POSTCOMMIT"
ENTRY = "void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 v) {"
BYTE = """        cpu->ram[off] = v;
        /* Optional title hook"""
WORD = """        cpu->ram[off + 1] = (uint8)(v >> 8);
        cpu->open_bus = (uint8)(v >> 8);"""
HOOK = r'''/* UR_QA01_RF086_NATIVE_WRAM_POSTCOMMIT
 * Called AFTER an actual WRAM byte/word store, not in the pre-write logger.
 * The function label is advisory (last AOT function), not a callsite proof.
 * Interpreter and native master clocks are not registered to original v/h.
 */
extern int snes_frame_counter;
extern const char *g_last_recomp_func;
static unsigned ur_rf086_rows;
static void ur_rf086_after(CpuState *cpu, unsigned width, uint16 addr,
                           unsigned before, unsigned supplied, unsigned after) {
    const char *flag = getenv("UR_QA01_RF084_NATIVE_SOUND_DP");
    if (!flag || flag[0] != '1' || flag[1] != '\0' ||
        snes_frame_counter < 6056 || snes_frame_counter > 6060) return;
    if (++ur_rf086_rows > 8192u) {
        if (ur_rf086_rows == 8193u)
            fprintf(stderr, "QA01RF086NATIVE_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
        "QA01RF086NATIVE seq=%u scope=%s f=%d width=%u D=%04X"
        " addr=%04X old=%04X supplied=%04X rawAfter=%04X"
        " native_master=%llu\n",
        ur_rf086_rows, g_last_recomp_func ? g_last_recomp_func : "unknown",
        snes_frame_counter, width, (unsigned)cpu->D, (unsigned)addr,
        before, supplied, after, (unsigned long long)cpu->master_cycles);
}
'''
BYTE_REPLACE = """        cpu->ram[off] = v;
        if (bank == 0x00 && off == 0x0069)
            ur_rf086_after(cpu, 1u, addr, old, v, (unsigned)cpu->ram[off]);
        /* Optional title hook"""
WORD_REPLACE = """        cpu->ram[off + 1] = (uint8)(v >> 8);
        if (bank == 0x00 && off == 0x0063)
            ur_rf086_after(cpu, 2u, addr, old, v,
                (unsigned)cpu->ram[off] |
                ((unsigned)cpu->ram[off + 1] << 8));
        cpu->open_bus = (uint8)(v >> 8);"""


def patch(text: str) -> str:
    if STAMP in text or "ur_rf086_after" in text:
        raise ValueError("RF086 common WRAM source already or partly patched")
    for anchor in (ENTRY, BYTE, WORD):
        if text.count(anchor) != 1:
            raise ValueError("RF086 pinned WRAM commit anchor missing/ambiguous")
    calls = ("cpu_read8_paced(", "cpu_read16_paced(",
             "cpu_write8_paced(", "cpu_write16_paced(")
    before = tuple(text.count(x) for x in calls)
    text = text.replace(ENTRY, HOOK + "\n" + ENTRY, 1)
    text = text.replace(BYTE, BYTE_REPLACE, 1)
    text = text.replace(WORD, WORD_REPLACE, 1)
    if tuple(text.count(x) for x in calls) != before:
        raise AssertionError("RF086 changed guest paced-bus helper population")
    if text.count(STAMP) != 1 or text.count("ur_rf086_after(cpu,") != 2:
        raise AssertionError("RF086 postcommit hook population changed")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    target = args.root / FILE
    if not target.is_file() or target.is_symlink():
        parser.error("actual disposable framework cpu_state.c missing")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    print("RF086 native WRAM post-commit observer staged at real bus stores")


if __name__ == "__main__":
    main()

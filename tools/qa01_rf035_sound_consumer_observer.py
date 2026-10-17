#!/usr/bin/env python3
"""RF035 read-only original opcode / native DP-consumer observer.

Install in DISPOSABLE source-qualified guests after RF030..034. This does not
move clocks, rephase inputs, replace CPU reads or edit any generated game code.
Original logs actual 65816 opcode execution in the sound-upload routine;
native logs WRAM bus-helper reads (not necessarily every AOT direct load).
Absence of a native helper read is inconclusive, never proof of dead code.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA01_RF035_SOUND_CONSUMER"
ORIG = Path("cpuexec.cpp")
NATIVE = Path("snesrecomp/runner/src/snes/cpu_state.c")

ORIG_DISPATCH = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
NATIVE_BYTE = "    if (off >= 0) return cpu_latch_read8(cpu, cpu->ram[off]);\n"
NATIVE_WORD = """        uint8 hi = (hi_off >= 0)
            ? cpu->ram[hi_off]
            : cpu_read8(cpu, bank, hi_addr);
        return cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8));
"""
NATIVE_HEADER = 'extern Snes *g_snes;\n'

ORIG_BEFORE = r"""            /* UR_QA01_RF035_SOUND_CONSUMER: pre-dispatch only. */
            const unsigned ur_rf035_bank = (unsigned)Registers.PB;
            const unsigned ur_rf035_pc = (unsigned)Registers.PCw;
            const bool ur_rf035_sound =
                getenv("UR_QA01_RF035_SOUND_CONSUMER") != NULL &&
                ur_rf035_bank == 0x02u &&
                (ur_rf035_pc == 0x82F0u || ur_rf035_pc == 0x82F2u ||
                 ur_rf035_pc == 0x82F6u || ur_rf035_pc == 0x8301u);
            const unsigned ur_rf035_op = ur_rf035_sound ? (unsigned)Op : 0u;
            const unsigned ur_rf035_a0 = ur_rf035_sound ? (unsigned)Registers.A.W : 0u;
            const unsigned ur_rf035_y0 = ur_rf035_sound ? (unsigned)Registers.Y.W : 0u;
            const unsigned ur_rf035_dp63 = ur_rf035_sound ? (unsigned)Memory.RAM[0x63] : 0u;
            const unsigned ur_rf035_dp64 = ur_rf035_sound ? (unsigned)Memory.RAM[0x64] : 0u;
            const unsigned ur_rf035_dp69 = ur_rf035_sound ? (unsigned)Memory.RAM[0x69] : 0u;
"""
ORIG_AFTER = r"""            if (ur_rf035_sound) {
                static unsigned ur_rf035_observed;
                if (ur_rf035_observed++ < 1024u)
                    fprintf(stderr,
                        "QA01RF035ORIG frame=%u v=%u h=%d pc=%02X:%04X op=%02X a0=%04X a1=%04X y0=%04X dp63=%02X dp64=%02X dp69=%02X\n",
                        (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
                        (int)CPU.Cycles, ur_rf035_bank, ur_rf035_pc,
                        ur_rf035_op, ur_rf035_a0, (unsigned)Registers.A.W,
                        ur_rf035_y0, ur_rf035_dp63, ur_rf035_dp64, ur_rf035_dp69);
                else if (ur_rf035_observed == 1025u)
                    fprintf(stderr, "QA01RF035ORIG_TRUNCATED\n");
            }
"""
NATIVE_HELPER = r"""/* UR_QA01_RF035_SOUND_CONSUMER: optional native WRAM read helper
 * evidence only. AOT direct-memory loads and interpreter bypasses must be
 * independently checked; no trace row means no observed helper call. */
static void ur_qa01_rf035_read(CpuState *cpu, uint8 bank, uint16 addr,
                              uint16 value, unsigned width) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    if (!getenv("UR_QA01_RF035_SOUND_CONSUMER") ||
        snes_frame_counter < 6053 || snes_frame_counter > 6068)
        return;
    const unsigned start = (unsigned)addr;
    const unsigned end = start + width;
    if (!(start <= 0x63u && 0x63u < end) &&
        !(start <= 0x64u && 0x64u < end) &&
        !(start <= 0x69u && 0x69u < end))
        return;
    static unsigned rows;
    if (rows++ < 4096u)
        fprintf(stderr,
            "QA01RF035NATIVE frame=%d bank=%02X addr=%04X width=%u value=%04X A=%04X S=%04X scope=%s\n",
            snes_frame_counter, (unsigned)bank, (unsigned)addr, width,
            (unsigned)value, (unsigned)cpu->A, (unsigned)cpu->S,
            g_last_recomp_func ? g_last_recomp_func : "?");
    else if (rows == 4097u)
        fprintf(stderr, "QA01RF035NATIVE_TRUNCATED\n");
}

"""

def patch_original(src: str) -> str:
    if MARK in src:
        if src.count(ORIG_BEFORE) != 1 or src.count(ORIG_AFTER) != 1:
            raise ValueError("partial/tampered original RF035 observer")
        return src
    if src.count(ORIG_DISPATCH) != 1:
        raise ValueError("unknown original Snes9x opcode-dispatch site")
    replacement = ORIG_BEFORE + ORIG_DISPATCH + "\n" + ORIG_AFTER.rstrip("\n")
    if replacement.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise AssertionError("original CPU opcode dispatch altered")
    return src.replace(ORIG_DISPATCH, replacement, 1)


def patch_native(src: str) -> str:
    if MARK in src:
        if src.count(NATIVE_HELPER) != 1 or "ur_qa01_rf035_read(cpu, bank, addr" not in src:
            raise ValueError("partial/tampered native RF035 observer")
        return src
    for anchor in (NATIVE_HEADER, NATIVE_BYTE, NATIVE_WORD):
        if src.count(anchor) != 1:
            raise ValueError("unknown native WRAM byte/word read source")
    src = src.replace(NATIVE_HEADER, NATIVE_HEADER + NATIVE_HELPER, 1)
    src = src.replace(NATIVE_BYTE, """    if (off >= 0) {
        uint8 value = cpu->ram[off];
        ur_qa01_rf035_read(cpu, bank, addr, value, 1);
        return cpu_latch_read8(cpu, value);
    }
""", 1)
    src = src.replace(NATIVE_WORD, NATIVE_WORD.replace(
        "        return cpu_latch_read16",
        "        ur_qa01_rf035_read(cpu, bank, addr,\n"
        "                            (uint16)lo | ((uint16)hi << 8), 2);\n"
        "        return cpu_latch_read16"), 1)
    return src


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    args = p.parse_args()
    path = args.root.resolve() / (ORIG if args.side == "original" else NATIVE)
    if not path.is_file() or (args.side == "native" and "snesrecomp" not in path.parts):
        p.error("RF035 requires an existing disposable pinned emulator checkout")
    before = path.read_text(encoding="utf8")
    after = (patch_original if args.side == "original" else patch_native)(before)
    if before != after:
        path.write_text(after, encoding="utf8")
    print("RF035 " + args.side + ": " + ("already staged" if before == after else "read-only observer staged"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

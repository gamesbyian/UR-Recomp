#!/usr/bin/env python3
"""Read-only original Snes9x 65816 opcode-byte capture near proven HDMA writers.

Patch a disposable original libretro core only. No guest instruction, RAM,
ROM, memory-mapped IO, or execution timing is modified; it only prints the
already fetched opcode and direct PCBase ROM bytes when explicitly armed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_ORIGINAL_HDMA_OPCODE"
ANCHOR = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
SNIPPET = r'''
            /* UR_QA08_ORIGINAL_HDMA_OPCODE: true executed ROM instruction
             * bytes surrounding independently observed Snes9x table writers.
             * Direct PCBase access only; never a mapped bus read or guest poke.
             * off by default; exactly frame1781, bank82:D5C0..D66F. */
            {
                static int qa08_opcode_init = 0;
                static int qa08_opcode_on = 0;
                static unsigned qa08_opcode_count = 0;
                if (!qa08_opcode_init) {
                    const char *arm = getenv("UR_QA08_ORIGINAL_HDMA_OPCODE_FRAME");
                    char *end = NULL;
                    qa08_opcode_init = 1;
                    if (arm && *arm) {
                        unsigned long v = strtoul(arm, &end, 10);
                        if (end != arm && *end == '\0' && v == 1781UL)
                            qa08_opcode_on = 1;
                    }
                }
                const unsigned qa08_codepc = (unsigned)Registers.PCw;
                if (qa08_opcode_on && (unsigned)ICPU.Frame == 1781u &&
                    (unsigned)Registers.PB == 0x82u &&
                    qa08_codepc >= 0xD5C0u && qa08_codepc <= 0xD66Fu) {
                    if (qa08_opcode_count >= 512u) {
                        if (qa08_opcode_count == 512u)
                            fprintf(stderr,
                                "UR_QA08_ORIGINAL_HDMA_OPCODE_OVERFLOW frame=1781 max=512\n");
                        qa08_opcode_count++;
                    } else {
                        const unsigned mapped = (CPU.PCBase != NULL);
                        unsigned char opbytes[4] = {0,0,0,0};
                        if (mapped)
                            for (unsigned n = 0; n < 4; ++n)
                                opbytes[n] = CPU.PCBase[qa08_codepc + n];
                        fprintf(stderr,
                            "UR_QA08_ORIGINAL_HDMA_OPCODE frame=%u pc=%02X%04X "
                            "op=%02X oplen=%u bytes=%02X%02X%02X%02X "
                            "mapped=%u fetched=%u\n",
                            (unsigned)ICPU.Frame, (unsigned)Registers.PB,
                            qa08_codepc, (unsigned)Op,
                            (unsigned)ICPU.S9xOpLengths[Op],
                            (unsigned)opbytes[0], (unsigned)opbytes[1],
                            (unsigned)opbytes[2], (unsigned)opbytes[3],
                            mapped, (unsigned)(mapped && opbytes[0] == Op));
                        /* UR_QA08_ORIGINAL_RACER_LUT: sampled only at four
                         * original executed ROM PCs after selector load and
                         * TAX respectively. Direct PCBase ROM data, never
                         * an extra mapped-bus read or a guest write. */
                        if (qa08_codepc == 0xD5D1u || qa08_codepc == 0xD61Eu) {
                            fprintf(stderr,
                                "UR_QA08_ORIGINAL_RACER_LUT frame=%u pc=82%04X "
                                "kind=selector a=%04X x=%04X\n",
                                (unsigned)ICPU.Frame, qa08_codepc,
                                (unsigned)Registers.A.W, (unsigned)Registers.X.W);
                        }
                        if (qa08_codepc == 0xD5D4u || qa08_codepc == 0xD621u) {
                            const unsigned qa08_lut_idx = (unsigned)Registers.X.W;
                            const unsigned qa08_lut_base = 0xD52Au + qa08_lut_idx;
                            if (!mapped || qa08_lut_idx > 255u ||
                                qa08_lut_base + 3u > 0xD66Fu) {
                                fprintf(stderr,
                                    "UR_QA08_ORIGINAL_RACER_LUT_INVALID "
                                    "frame=%u pc=82%04X x=%04X\n",
                                    (unsigned)ICPU.Frame, qa08_codepc, qa08_lut_idx);
                            } else {
                                fprintf(stderr,
                                    "UR_QA08_ORIGINAL_RACER_LUT frame=%u pc=82%04X "
                                    "kind=lookup a=%04X x=%04X bytes=%02X%02X%02X%02X\n",
                                    (unsigned)ICPU.Frame, qa08_codepc,
                                    (unsigned)Registers.A.W, qa08_lut_idx,
                                    (unsigned)CPU.PCBase[qa08_lut_base],
                                    (unsigned)CPU.PCBase[qa08_lut_base + 1u],
                                    (unsigned)CPU.PCBase[qa08_lut_base + 2u],
                                    (unsigned)CPU.PCBase[qa08_lut_base + 3u]);
                            }
                        }
                        qa08_opcode_count++;
                    }
                }
            }
'''

def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("original Snes9x HDMA opcode probe already present")
    if (source.count(ANCHOR) != 1
            or 'void S9xMainLoop (void)' not in source
            or '#include "memmap.h"' not in source
            or 'Op = CPU.PCBase[Registers.PCw]' not in source):
        raise ValueError("original Snes9x opcode fetch source anchor changed")
    source = source.replace('#include "memmap.h"',
                            '#include "memmap.h"\n#include <stdio.h>\n#include <stdlib.h>', 1)
    return source.replace(ANCHOR, SNIPPET + ANCHOR, 1)

def apply(source_path: Path, check_only: bool = False) -> Path:
    new = patch_source(source_path.read_text(encoding="utf8"))
    if not check_only:
        source_path.write_text(new, encoding="utf8")
    return source_path

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    try:
        path = apply(args.source, args.check_only)
    except (OSError, ValueError) as exc:
        ap.exit(2, f"QA08 original opcode source patch refused: {exc}\n")
    print(f"QA08 original HDMA writer opcode source patch staged={not args.check_only} file={path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

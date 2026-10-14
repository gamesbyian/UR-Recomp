#!/usr/bin/env python3
"""Disposable original Snes9x CPU opcode observer for exact 2P seed 50036056.

Read-only original CPU dispatch instrumentation; never changes ROM, WRAM,
controller input or host frame progression. Frame scope deliberately includes
the documented possible ICPU.Frame versus zero-frame host-sample boundary.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
STAMP = "UR-QA01-DUAL-AIR-ORIGINAL-PC-WRITER-20261014"
FIRST, LAST = 2574, 2586
# Both low and upper bytes of each 16-bit original guest field, and temporary
# 16-bit scratch shared by per-player movement before the public writes.
TARGETS = (
    0x0545, 0x0546, 0x0547, 0x0548,
    0x0415, 0x0416, 0x0417, 0x0418,
    0x04BB, 0x04BC, 0x04BD, 0x04BE,
    0x0F29, 0x0F2A, 0x0FA1, 0x0FA2,
    0x00A7, 0x00A8,
)
# Historical disassembly candidate PCs. Their EXECUTION is observed, not
# presumed a verified USA homolog. Capture no-op stores at these scopes too.
CANDIDATE_PCS = (0x818E26, 0x818F7A)

INSTRUMENT = r"""            /* UR-QA01-DUAL-AIR-ORIGINAL-PC-WRITER-20261014:
             * Read-only bounded pre/post opcode scope. Dynamic PC candidate
             * checks DO NOT assert PAL/USA homology or store attribution. */
            static const uint16 ur_qa_air_addr[] = {%%ADDRESSES%%};
            const bool ur_qa_air_gate =
                (unsigned)ICPU.Frame >= %%FIRST%% &&
                (unsigned)ICPU.Frame <= %%LAST%%;
            uint8 ur_qa_air_before[sizeof(ur_qa_air_addr) /
                                  sizeof(ur_qa_air_addr[0])];
            uint32 ur_qa_air_pc = ((uint32)Registers.PB << 16) | Registers.PCw;
            if (ur_qa_air_gate)
                for (unsigned ur_i = 0; ur_i <
                     sizeof(ur_qa_air_addr) / sizeof(ur_qa_air_addr[0]); ++ur_i)
                    ur_qa_air_before[ur_i] = Memory.RAM[ur_qa_air_addr[ur_i]];
            Registers.PCw++;
            (*Opcodes[Op].S9xOpcode)();
            if (ur_qa_air_gate)
                for (unsigned ur_i = 0; ur_i <
                     sizeof(ur_qa_air_addr) / sizeof(ur_qa_air_addr[0]); ++ur_i)
                {
                    uint8 ur_new = Memory.RAM[ur_qa_air_addr[ur_i]];
                    const bool ur_qa_candidate =
                        ((ur_qa_air_pc == 0x818E26 &&
                          ur_qa_air_addr[ur_i] == 0x0545) ||
                         (ur_qa_air_pc == 0x818F7A &&
                          ur_qa_air_addr[ur_i] == 0x0547));
                    if (ur_new != ur_qa_air_before[ur_i] || ur_qa_candidate)
                        fprintf(stderr,
                                "QA01AIRPC f=%u v=%u pc=%06X addr=%04X old=%02X new=%02X candidate=%u\n",
                                (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
                                (unsigned)ur_qa_air_pc,
                                (unsigned)ur_qa_air_addr[ur_i],
                                (unsigned)ur_qa_air_before[ur_i],
                                (unsigned)ur_new, (unsigned)ur_qa_candidate);
                }
"""


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("original 2P opcode observer already installed")
    if source.count(MARKER) != 1:
        raise ValueError("ambiguous pinned original Snes9x CPU opcode dispatch")
    replacement = (INSTRUMENT.replace(
        "%%ADDRESSES%%", ", ".join(f"0x{a:04X}" for a in TARGETS))
        .replace("%%FIRST%%", str(FIRST)).replace("%%LAST%%", str(LAST)))
    if replacement.count("Registers.PCw++;") != 1 or replacement.count(
            "(*Opcodes[Op].S9xOpcode)();") != 1:
        raise ValueError("instrumented CPU dispatch not exactly once")
    return source.replace(MARKER, replacement, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_cpuexec_cpp", type=Path)
    args = parser.parse_args()
    original = args.original_cpuexec_cpp.read_text(encoding="utf-8")
    args.original_cpuexec_cpp.write_text(patch(original), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

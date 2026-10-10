#!/usr/bin/env python3
"""Disposable original Snes9x Switcher stack-page opcode probe.

The single source of game truth remains the unpatched original Snes9x run.
This adds read-only observation to a *disposable* original core, and only
after the independently qualified 2014 source result. No input retiming,
guest memory writes, source patches or Baldosa execution modifications.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
STAMP = "UR-QA01 SWITCHER STACK OPCODE SCOPE"
# Actual independent same-host Switcher WRAM differences (2026-10-10).
# The last two did not appear in Bowl's eight sampled score-tally frames.
TARGETS = (0x01DD, 0x01E6, 0x01E7, 0x01EF, 0x01F0, 0x01F1, 0x01F2, 0x01F3)


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("Switcher stack opcode probe already installed")
    if source.count(MARKER) != 1:
        raise ValueError("pinned Snes9x opcode dispatch marker missing or ambiguous")
    addresses = ", ".join(f"0x{addr:04X}" for addr in TARGETS)
    instrumented = f"""\t\t\t/* {STAMP}: original-only, read-only, bounded. */
\t\t\tstatic const uint16 ur_qa_stack_addr[] = {{{addresses}}};
\t\t\tstatic const unsigned ur_qa_stack_first = []() -> unsigned {{
\t\t\t\tconst char *s = getenv("UR_QA_STACK_FIRST");
\t\t\t\treturn s ? (unsigned)strtoul(s, nullptr, 10) : 0xffffffffu;
\t\t\t}}();
\t\t\tstatic const unsigned ur_qa_stack_last = []() -> unsigned {{
\t\t\t\tconst char *s = getenv("UR_QA_STACK_LAST");
\t\t\t\treturn s ? (unsigned)strtoul(s, nullptr, 10) : 0u;
\t\t\t}}();
\t\t\tstatic bool ur_qa_stack_started = false;
\t\t\tconst bool ur_qa_stack_gate = ur_qa_stack_first <= (unsigned)ICPU.Frame &&
\t\t\t\t(unsigned)ICPU.Frame <= ur_qa_stack_last;
\t\t\tuint8 ur_qa_stack_before[sizeof(ur_qa_stack_addr) / sizeof(ur_qa_stack_addr[0])];
\t\t\tconst uint16 ur_qa_stack_sp0 = Registers.S.W;
\t\t\tconst uint32 ur_qa_stack_pc = ((uint32)Registers.PB << 16) | Registers.PCw;
\t\t\tif (ur_qa_stack_gate)
\t\t\t{{
\t\t\t\tif (!ur_qa_stack_started)
\t\t\t\t{{
\t\t\t\t\tfprintf(stderr, "QASTACKBEGIN f=%u v=%u pc=%06X sp=%04X\\n",
\t\t\t\t\t\t(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
\t\t\t\t\t\t(unsigned)ur_qa_stack_pc, (unsigned)ur_qa_stack_sp0);
\t\t\t\t\tur_qa_stack_started = true;
\t\t\t\t}}
\t\t\t\tfor (unsigned ur_i = 0; ur_i < sizeof(ur_qa_stack_addr) / sizeof(ur_qa_stack_addr[0]); ++ur_i)
\t\t\t\t\tur_qa_stack_before[ur_i] = Memory.RAM[ur_qa_stack_addr[ur_i]];
\t\t\t}}
\t\t\tRegisters.PCw++;
\t\t\t(*Opcodes[Op].S9xOpcode)();
\t\t\tif (ur_qa_stack_gate)
\t\t\t{{
\t\t\t\tfor (unsigned ur_i = 0; ur_i < sizeof(ur_qa_stack_addr) / sizeof(ur_qa_stack_addr[0]); ++ur_i)
\t\t\t\t{{
\t\t\t\t\tuint8 ur_new = Memory.RAM[ur_qa_stack_addr[ur_i]];
\t\t\t\t\tif (ur_new != ur_qa_stack_before[ur_i])
\t\t\t\t\t\tfprintf(stderr,
\t\t\t\t\t\t\t"QASTACKWRITE f=%u v=%u pc=%06X op=%02X sp0=%04X sp1=%04X addr=%04X old=%02X new=%02X\\n",
\t\t\t\t\t\t\t(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
\t\t\t\t\t\t\t(unsigned)ur_qa_stack_pc, (unsigned)Op,
\t\t\t\t\t\t\t(unsigned)ur_qa_stack_sp0, (unsigned)Registers.S.W,
\t\t\t\t\t\t\t(unsigned)ur_qa_stack_addr[ur_i],
\t\t\t\t\t\t\t(unsigned)ur_qa_stack_before[ur_i], (unsigned)ur_new);
\t\t\t\t}}
\t\t\t}}
"""
    return source.replace(MARKER, instrumented, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path,
                        help="disposable .tools/src/snes9x-libretro/cpuexec.cpp")
    args = parser.parse_args()
    args.source.write_text(patch(args.source.read_text(encoding="utf-8")),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

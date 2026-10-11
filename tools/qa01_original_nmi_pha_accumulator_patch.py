#!/usr/bin/env python3
"""Instrument exact original Snes9x I_NMI+6 PHA register state in disposable core.

Apply *after* instrument_snesref_qa01_switcher_stack.py --single-address 0x01DD
--watch-nmi, never in checked-in Snes9x or to any source ROM/game code.
Read-only PHA observation respects the already validated ICPU.Frame gate.
"""
from __future__ import annotations

import argparse
from pathlib import Path

STAMP = "UR-QA01 ORIGINAL I_NMI+6 PHA ACCUMULATOR OBSERVER"
MARKER = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
PREREQUISITE = "UR-QA01 SWITCHER STACK OPCODE SCOPE"
REQUIRE_NMI = "UR-QA01 SWITCHER NMI ENTRY STACK SCOPE"


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("original PHA accumulator observer already installed")
    if PREREQUISITE not in source or REQUIRE_NMI not in source:
        raise ValueError("only valid after original bounded opcode + NMI entry observer")
    if source.count(MARKER) != 1:
        raise ValueError("pinned Snes9x opcode call site missing or not unique")
    before = r"""            /* UR-QA01 ORIGINAL I_NMI+6 PHA ACCUMULATOR OBSERVER */
            const bool ur_qa_pha_gate = ur_qa_stack_gate &&
                (Op == 0x48) && ((ur_qa_stack_pc & 0x7F0000u) == 0) &&
                ((ur_qa_stack_pc & 0xFFFFu) == 0x858Eu);
            const unsigned ur_qa_pha_frame0 = (unsigned)ICPU.Frame;
            const unsigned ur_qa_pha_v0 = (unsigned)CPU.V_Counter;
            const uint16 ur_qa_pha_a0 = Registers.A.W;
            const uint16 ur_qa_pha_s0 = Registers.S.W;
            const uint8 ur_qa_pha_pl0 = Registers.PL;
            const uint8 ur_qa_pha_low0 = ur_qa_pha_gate ? Memory.RAM[0x01DD] : 0;
            const uint8 ur_qa_pha_high0 = ur_qa_pha_gate ? Memory.RAM[0x01DE] : 0;
"""
    after = r"""            if (ur_qa_pha_gate)
                fprintf(stderr,
                    "QAPHAREG f=%u v=%u pc=%06X op=%02X sp0=%04X sp1=%04X a0=%04X a1=%04X pl0=%02X pl1=%02X m0=%u m1=%u dd0=%02X dd1=%02X de0=%02X de1=%02X f1=%u\n",
                    ur_qa_pha_frame0, ur_qa_pha_v0,
                    (unsigned)ur_qa_stack_pc, (unsigned)Op,
                    (unsigned)ur_qa_pha_s0, (unsigned)Registers.S.W,
                    (unsigned)ur_qa_pha_a0, (unsigned)Registers.A.W,
                    (unsigned)ur_qa_pha_pl0, (unsigned)Registers.PL,
                    (unsigned)((ur_qa_pha_pl0 & 0x20u) != 0),
                    (unsigned)((Registers.PL & 0x20u) != 0),
                    (unsigned)ur_qa_pha_low0, (unsigned)Memory.RAM[0x01DD],
                    (unsigned)ur_qa_pha_high0, (unsigned)Memory.RAM[0x01DE],
                    (unsigned)ICPU.Frame);
"""
    # Format uses *original* C++ declarations in Snes9x and never changes its
    # CPU state. Keep the actual original call exactly once and in sequence.
    replaced = before + MARKER + "\n" + after.rstrip("\n")
    if replaced.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise AssertionError("real original opcode must remain once")
    return source.replace(MARKER, replaced, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    target = args.source.resolve()
    if target.name != "cpuexec.cpp" or "snes9x-libretro" not in target.parts:
        raise ValueError("require a disposable snes9x-libretro/cpuexec.cpp path")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

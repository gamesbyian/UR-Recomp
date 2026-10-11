#!/usr/bin/env python3
"""Opt-in source Snes9x stack-pull scope observer for the Switcher NMI residue.

Install only in a disposable original Snes9x cpuexec.cpp, after the existing
Switcher opcode/NMI and full-accumulator observers. This uses architectural
stack-pull widths to select candidate readers; it is NOT a bus-read trace.
No original input, RAM, CPU, interrupt dispatch or timing is modified.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import instrument_snesref_qa01_switcher_stack as stack
import qa01_original_nmi_pha_accumulator_patch as pha

STAMP = "UR-QA01 ORIGINAL SWITCHER NMI STACK PULL SCOPE"


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("Switcher NMI stack pull observer already installed")
    if any(stamp not in source for stamp in (stack.STAMP, stack.NMI_STAMP, pha.STAMP)):
        raise ValueError("require prior read-only original stack/NMI/PHA observers")
    if source.count(stack.MARKER) != 1:
        raise ValueError("pinned original opcode dispatch marker missing or ambiguous")
    before = r"""
            /* UR-QA01 ORIGINAL SWITCHER NMI STACK PULL SCOPE: pre-opcode.
               Architectural stack reads only; no guest memory mutation. */
            const uint8 ur_qa_pull_op = Op;
            const uint16 ur_qa_pull_sp0 = Registers.S.W;
            const uint8 ur_qa_pull_pl0 = Registers.PL;
            const uint16 ur_qa_pull_a0 = Registers.A.W;
            const unsigned ur_qa_pull_f0 = (unsigned)ICPU.Frame;
            const unsigned ur_qa_pull_v0 = (unsigned)CPU.V_Counter;
            unsigned ur_qa_pull_width = 0;
            switch (ur_qa_pull_op) {
              case 0x68: /* PLA: accumulator M bit */
                ur_qa_pull_width = (ur_qa_pull_pl0 & 0x20) ? 1 : 2; break;
              case 0xFA: /* PLX: index X bit */
              case 0x7A: /* PLY */
                ur_qa_pull_width = (ur_qa_pull_pl0 & 0x10) ? 1 : 2; break;
              case 0x2B: /* PLD: always 16-bit */
                ur_qa_pull_width = 2; break;
              case 0xAB: /* PLB: always 8-bit */
              case 0x28: /* PLP: always 8-bit */
                ur_qa_pull_width = 1; break;
              default: break;
            }
            const bool ur_qa_pull_dd =
                ur_qa_pull_sp0 < 0x01DDu &&
                (unsigned)ur_qa_pull_sp0 + ur_qa_pull_width >= 0x01DDu;
            const bool ur_qa_pull_de =
                ur_qa_pull_sp0 < 0x01DEu &&
                (unsigned)ur_qa_pull_sp0 + ur_qa_pull_width >= 0x01DEu;
            const bool ur_qa_pull_gate = ur_qa_stack_gate &&
                ur_qa_pull_width != 0 && (ur_qa_pull_dd || ur_qa_pull_de);
            const uint8 ur_qa_pull_dd0 = ur_qa_pull_gate ? Memory.RAM[0x01DD] : 0;
            const uint8 ur_qa_pull_de0 = ur_qa_pull_gate ? Memory.RAM[0x01DE] : 0;
            /* RTI restores the interrupted PC/P from the hardware frame.
               The pinned core CHECK_FOR_IRQ() is empty (cpuops.h).
               Observe ALL RTIs in this tiny source CPU window; they may
               include IRQ/BRK, so the report must not call them NMI returns. */
            const bool ur_qa_rti_gate = ur_qa_stack_gate && (Op == 0x40);
            const unsigned ur_qa_rti_emu0 = ur_qa_rti_gate ? (unsigned)(CheckEmulation() != 0) : 0;
            const uint8 ur_qa_rti_pb0 = ur_qa_rti_gate ? Registers.PB : 0;
            const int ur_qa_rti_cycle0 = ur_qa_rti_gate ? (int)CPU.Cycles : 0;
            /* Pre-RTI stack image independently reconstructs P/PC/PB.
               Guard the four-byte native frame against stack-page
               overflow; 6502 emulation-mode only pulls the first 3. */
            const bool ur_qa_rti_stack4 = ur_qa_rti_gate &&
                ur_qa_pull_sp0 >= 0x0100u && ur_qa_pull_sp0 <= 0x01FBu;
            const uint8 ur_qa_rti_b1 = ur_qa_rti_stack4 ? Memory.RAM[ur_qa_pull_sp0 + 1u] : 0;
            const uint8 ur_qa_rti_b2 = ur_qa_rti_stack4 ? Memory.RAM[ur_qa_pull_sp0 + 2u] : 0;
            const uint8 ur_qa_rti_b3 = ur_qa_rti_stack4 ? Memory.RAM[ur_qa_pull_sp0 + 3u] : 0;
            const uint8 ur_qa_rti_b4 = ur_qa_rti_stack4 ? Memory.RAM[ur_qa_pull_sp0 + 4u] : 0;
"""
    after = r"""
            if (ur_qa_pull_gate)
                fprintf(stderr,
                    "QANMIPULL f=%u v=%u pc=%06X op=%02X sp0=%04X sp1=%04X width=%u pl0=%02X pl1=%02X a0=%04X a1=%04X dd=%02X de=%02X touches_dd=%u touches_de=%u f1=%u\n",
                    ur_qa_pull_f0, ur_qa_pull_v0, (unsigned)ur_qa_stack_pc,
                    (unsigned)ur_qa_pull_op, (unsigned)ur_qa_pull_sp0,
                    (unsigned)Registers.S.W, ur_qa_pull_width,
                    (unsigned)ur_qa_pull_pl0, (unsigned)Registers.PL,
                    (unsigned)ur_qa_pull_a0, (unsigned)Registers.A.W,
                    (unsigned)ur_qa_pull_dd0, (unsigned)ur_qa_pull_de0,
                    (unsigned)ur_qa_pull_dd, (unsigned)ur_qa_pull_de,
                    (unsigned)ICPU.Frame);
            if (ur_qa_rti_gate)
                fprintf(stderr,
                    "QANMIRTI f=%u v0=%u v1=%u pc=%06X postpc=%06X pb0=%02X pb1=%02X sp0=%04X sp1=%04X a0=%04X a1=%04X pl0=%02X pl1=%02X emu0=%u stack4=%u b1=%02X b2=%02X b3=%02X b4=%02X cyc0=%d cyc1=%d f1=%u\n",
                    ur_qa_pull_f0, ur_qa_pull_v0, (unsigned)CPU.V_Counter,
                    (unsigned)ur_qa_stack_pc,
                    (unsigned)(((uint32)Registers.PB << 16) | Registers.PCw),
                    (unsigned)ur_qa_rti_pb0,
                    (unsigned)Registers.PB, (unsigned)ur_qa_pull_sp0,
                    (unsigned)Registers.S.W, (unsigned)ur_qa_pull_a0,
                    (unsigned)Registers.A.W, (unsigned)ur_qa_pull_pl0,
                    (unsigned)Registers.PL,
                    ur_qa_rti_emu0, (unsigned)ur_qa_rti_stack4,
                    (unsigned)ur_qa_rti_b1, (unsigned)ur_qa_rti_b2,
                    (unsigned)ur_qa_rti_b3, (unsigned)ur_qa_rti_b4,
                    ur_qa_rti_cycle0, (int)CPU.Cycles, (unsigned)ICPU.Frame);
"""
    replacement = before + stack.MARKER + "\n" + after
    if replacement.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise AssertionError("must retain exactly one real opcode dispatch")
    return source.replace(stack.MARKER, replacement, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="disposable snes9x-libretro/cpuexec.cpp")
    args = parser.parse_args()
    target = args.source.resolve()
    if target.name != "cpuexec.cpp" or "snes9x-libretro" not in target.parts:
        raise ValueError("require disposable original snes9x-libretro/cpuexec.cpp")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

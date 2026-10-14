#!/usr/bin/env python3
"""QA-01: add a narrow read-only collision branch observer to disposable Snes9x.

Patch *after* instrument_snesref_2p_air_writes.py, whose original opcode
dispatch must remain single-execution. Distinguishes original CPU opcode
frame / V-counter from the host-script dump and native pre-run clocks.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import instrument_snesref_2p_air_writes as base

STAMP = "UR-QA01-P1P2-SOURCE-COLLISION-BRANCH-20261014"
OLD = ("            Registers.PCw++;\n"
       "            (*Opcodes[Op].S9xOpcode)();\n"
       "            if (ur_qa_air_gate)\n")
PCS = (0x819253, 0x819255, 0x819258, 0x81925A, 0x81925F,
       0x819262, 0x819263, 0x819266, 0x819268)
NEW = r"""            /* UR-QA01-P1P2-SOURCE-COLLISION-BRANCH-20261014:
             * Original CPU opcode boundaries only. Never rewrite state,
             * input, status, ROM, frame counters or the opcode dispatch. */
            const bool ur_qa_coll_gate = ur_qa_air_gate &&
                (ur_qa_air_pc == 0x819253 || ur_qa_air_pc == 0x819255 ||
                 ur_qa_air_pc == 0x819258 || ur_qa_air_pc == 0x81925A ||
                 ur_qa_air_pc == 0x81925F || ur_qa_air_pc == 0x819262 ||
                 ur_qa_air_pc == 0x819263 || ur_qa_air_pc == 0x819266 ||
                 ur_qa_air_pc == 0x819268);
            uint32 ur_qa_coll_pre_f = 0, ur_qa_coll_pre_v = 0;
            uint16 ur_qa_coll_pre_state = 0, ur_qa_coll_pre_seat = 0;
            uint16 ur_qa_coll_pre_y = 0, ur_qa_coll_pre_vy = 0;
            uint8 ur_qa_coll_pre_contact = 0;
            if (ur_qa_coll_gate)
            {
                ur_qa_coll_pre_f = (unsigned)ICPU.Frame;
                ur_qa_coll_pre_v = (unsigned)CPU.V_Counter;
                ur_qa_coll_pre_contact = Memory.RAM[0x02C0];
                ur_qa_coll_pre_state = (uint16)Memory.RAM[0x0F29] |
                    ((uint16)Memory.RAM[0x0F2A] << 8);
                ur_qa_coll_pre_seat = (uint16)Memory.RAM[0x0FEF] |
                    ((uint16)Memory.RAM[0x0FF0] << 8);
                ur_qa_coll_pre_y = (uint16)Memory.RAM[0x00A7] |
                    ((uint16)Memory.RAM[0x00A8] << 8);
                ur_qa_coll_pre_vy = (uint16)Memory.RAM[0x0FA1] |
                    ((uint16)Memory.RAM[0x0FA2] << 8);
            }
            Registers.PCw++;
            (*Opcodes[Op].S9xOpcode)();
            if (ur_qa_coll_gate)
            {
                const uint16 ur_qa_coll_after_state =
                    (uint16)Memory.RAM[0x0F29] |
                    ((uint16)Memory.RAM[0x0F2A] << 8);
                const uint16 ur_qa_coll_after_seat =
                    (uint16)Memory.RAM[0x0FEF] |
                    ((uint16)Memory.RAM[0x0FF0] << 8);
                const uint16 ur_qa_coll_after_y =
                    (uint16)Memory.RAM[0x00A7] |
                    ((uint16)Memory.RAM[0x00A8] << 8);
                const uint16 ur_qa_coll_after_vy =
                    (uint16)Memory.RAM[0x0FA1] |
                    ((uint16)Memory.RAM[0x0FA2] << 8);
                const uint32 ur_qa_coll_next =
                    ((uint32)Registers.PB << 16) | Registers.PCw;
                fprintf(stderr,
                        "QA01COLLBR pre_f=%u post_f=%u pre_v=%u post_v=%u pc=%06X next=%06X contact=%02X/%02X state=%04X/%04X seat=%04X/%04X y=%04X/%04X vy=%04X/%04X\n",
                        (unsigned)ur_qa_coll_pre_f,
                        (unsigned)ICPU.Frame,
                        (unsigned)ur_qa_coll_pre_v,
                        (unsigned)CPU.V_Counter,
                        (unsigned)ur_qa_air_pc,
                        (unsigned)ur_qa_coll_next,
                        (unsigned)ur_qa_coll_pre_contact,
                        (unsigned)Memory.RAM[0x02C0],
                        (unsigned)ur_qa_coll_pre_state,
                        (unsigned)ur_qa_coll_after_state,
                        (unsigned)ur_qa_coll_pre_seat,
                        (unsigned)ur_qa_coll_after_seat,
                        (unsigned)ur_qa_coll_pre_y,
                        (unsigned)ur_qa_coll_after_y,
                        (unsigned)ur_qa_coll_pre_vy,
                        (unsigned)ur_qa_coll_after_vy);
            }
            if (ur_qa_air_gate)
"""


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("collision branch observer already installed")
    if base.STAMP not in source:
        raise ValueError("original bounded P1/P2 opcode observer must be installed first")
    if source.count(OLD) != 1:
        raise ValueError("ambiguous original single-execution opcode dispatch")
    result = source.replace(OLD, NEW, 1)
    if (result.count("(*Opcodes[Op].S9xOpcode)();") != 1
            or result.count("Registers.PCw++;") != 1
            or result.count(STAMP) != 1):
        raise ValueError("original Snes9x opcode could execute twice")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_cpuexec_cpp", type=Path)
    args = p.parse_args()
    path = args.original_cpuexec_cpp
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

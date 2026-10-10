#!/usr/bin/env python3
"""Instrument pinned original Snes9x's *opcode dispatch* to identify Zoo menu writers.

Disposable QA-only core patch, never modifies game ROM, guest state, native
Baldosa, input timing or any checked-in third-party source. The caller passes
the absolute original frame window *measured* at fresh guest scene entry.

A pre/post-opcode byte delta establishes the executing CPU instruction scope
(or a synchronous side effect); further source/PC verification is required
before attributing an individual store instruction. Host frame tags are not
identical to guest logical relative frames by assumption.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
STAMP = "UR-QA01 original Zoo menu opcode writer probe"
# Exact 69-byte WRAM original(+5156)/Baldosa(+5156) difference surface,
# plus authoritatively observed menu/track/race mode controls.
# These are observation targets, not semantic writer attributions.
CHANGED = (
    0x008B,
    *range(0x0187, 0x018F),
    *range(0x01EE, 0x01F8),
    0x0B90, 0x0B92, 0x0B94, 0x0B96, 0x0B98, 0x0B9A, 0x0B9C, 0x0B9E,
    0x0BA1, 0x0BA2, 0x0BA3, 0x0BA5, 0x0BA6, 0x0BA7,
    0x0BA9, 0x0BAA, 0x0BAB, 0x0BAD, 0x0BAF, 0x0BB1,
    0x0BB2, 0x0BB3, 0x0BB5, 0x0BB6, 0x0BB7,
    0x0BB9, 0x0BBA, 0x0BBB, 0x0BBD, 0x0BBE, 0x0BBF,
    0x0BDC, 0x0BDD, 0x0BDF, 0x0BFC, 0x0BFD, 0x0BFF,
    0x0C1A, 0x0C1B, 0x0C1D, 0x0C1F,
    0x0C61, 0x0C62, 0x0C63, 0x0C67, 0x0C69,
    0x0C6A, 0x0C6B, 0x0C6C, 0x0C6E,
)
CONTROLS = (0x009F, 0x00CE, 0x0313)
TARGETS = tuple(dict.fromkeys((*CONTROLS, *CHANGED)))


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("original Zoo opcode writer probe already installed")
    if source.count(MARKER) != 1:
        raise ValueError("pinned cpuexec.cpp opcode marker missing or ambiguous")
    addresses = ", ".join(f"0x{a:04X}" for a in TARGETS)
    before = f"""\t\t\t/* {STAMP}. */
\t\t\tstatic const uint16 ur_qa_zoo_addr[] = {{{addresses}}};
\t\t\tstatic unsigned ur_qa_zoo_frame_first = []() -> unsigned {{
\t\t\t\tconst char *v = getenv("UR_QA_ZOO_TRACE_FIRST");
\t\t\t\treturn v ? (unsigned)strtoul(v, nullptr, 10) : 0xffffffffu;
\t\t\t}}();
\t\t\tstatic unsigned ur_qa_zoo_frame_last = []() -> unsigned {{
\t\t\t\tconst char *v = getenv("UR_QA_ZOO_TRACE_LAST");
\t\t\t\treturn v ? (unsigned)strtoul(v, nullptr, 10) : 0u;
\t\t\t}}();
\t\t\tbool ur_qa_zoo_gate = ur_qa_zoo_frame_first <= (unsigned)ICPU.Frame &&
\t\t\t\t(unsigned)ICPU.Frame <= ur_qa_zoo_frame_last;
\t\t\tuint8 ur_qa_zoo_before[sizeof(ur_qa_zoo_addr) / sizeof(ur_qa_zoo_addr[0])];
\t\t\tuint32 ur_qa_zoo_pc = ((uint32)Registers.PB << 16) | Registers.PCw;
\t\t\tif (ur_qa_zoo_gate)
\t\t\t\tfor (unsigned ur_i = 0; ur_i < sizeof(ur_qa_zoo_addr) / sizeof(ur_qa_zoo_addr[0]); ++ur_i)
\t\t\t\t\tur_qa_zoo_before[ur_i] = Memory.RAM[ur_qa_zoo_addr[ur_i]];
\t\t\tRegisters.PCw++;
\t\t\t(*Opcodes[Op].S9xOpcode)();
\t\t\tif (ur_qa_zoo_gate)
\t\t\t{{
\t\t\t\tfor (unsigned ur_i = 0; ur_i < sizeof(ur_qa_zoo_addr) / sizeof(ur_qa_zoo_addr[0]); ++ur_i)
\t\t\t\t{{
\t\t\t\t\tuint8 ur_new = Memory.RAM[ur_qa_zoo_addr[ur_i]];
\t\t\t\t\tif (ur_new != ur_qa_zoo_before[ur_i])
\t\t\t\t\t\tfprintf(stderr,
\t\t\t\t\t\t\t"ZOOPCWRITE f=%u v=%u pc=%06X addr=%04X old=%02X new=%02X\\n",
\t\t\t\t\t\t\t(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
\t\t\t\t\t\t\t(unsigned)ur_qa_zoo_pc, (unsigned)ur_qa_zoo_addr[ur_i],
\t\t\t\t\t\t\t(unsigned)ur_qa_zoo_before[ur_i], (unsigned)ur_new);
\t\t\t\t}}
\t\t\t}}
"""
    return source.replace(MARKER, before, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    s = args.source.read_text(encoding="utf-8")
    args.source.write_text(patch(s), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

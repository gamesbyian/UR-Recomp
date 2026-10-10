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
NMI_MARKER = "\t\t\t\tS9xOpcode_NMI();"
NMI_STAMP = "UR-QA01 SWITCHER NMI ENTRY STACK SCOPE"
# Actual independent same-host Switcher WRAM differences (2026-10-10).
# The last two did not appear in Bowl's eight sampled score-tally frames.
TARGETS = (0x01DD, 0x01E6, 0x01E7, 0x01EF, 0x01F0, 0x01F1, 0x01F2, 0x01F3)


def patch(source: str, *, targets: tuple[int, ...] = TARGETS, watch_nmi: bool = False) -> str:
    if STAMP in source:
        raise ValueError("Switcher stack opcode probe already installed")
    if source.count(MARKER) != 1:
        raise ValueError("pinned Snes9x opcode dispatch marker missing or ambiguous")
    if not targets or len(set(targets)) != len(targets) or any(addr not in TARGETS for addr in targets):
        raise ValueError("original opcode observer target must be a unique approved stack address")
    addresses = ", ".join(f"0x{addr:04X}" for addr in targets)
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
    patched = source.replace(MARKER, instrumented, 1)
    if watch_nmi:
        if targets != (0x01DD,):
            raise ValueError("original NMI observation requires only vetted 0x01DD")
        if source.count(NMI_MARKER) != 1 or NMI_STAMP in source:
            raise ValueError("pinned original Snes9x NMI entry marker missing or already instrumented")
        nmi = f"""\t\t\t\t/* {NMI_STAMP}: original NMI entry, NOT an opcode dispatch. */
\t\t\t\tstatic const unsigned ur_qa_nmi_first = []() -> unsigned {{
\t\t\t\t\tconst char *s = getenv("UR_QA_STACK_FIRST");
\t\t\t\t\treturn s ? (unsigned)strtoul(s, nullptr, 10) : 0xffffffffu;
\t\t\t\t}}();
\t\t\t\tstatic const unsigned ur_qa_nmi_last = []() -> unsigned {{
\t\t\t\t\tconst char *s = getenv("UR_QA_STACK_LAST");
\t\t\t\t\treturn s ? (unsigned)strtoul(s, nullptr, 10) : 0u;
\t\t\t\t}}();
\t\t\t\tconst unsigned ur_qa_nmi_frame0 = (unsigned)ICPU.Frame;\n\t\t\t\tconst unsigned ur_qa_nmi_v0 = (unsigned)CPU.V_Counter;\n\t\t\t\tconst bool ur_qa_nmi_gate = ur_qa_nmi_frame0 >= ur_qa_nmi_first &&
\t\t\t\t\tur_qa_nmi_frame0 <= ur_qa_nmi_last;
\t\t\t\tconst uint16 ur_qa_nmi_sp0 = Registers.S.W;
\t\t\t\tconst uint32 ur_qa_nmi_pc0 = ((uint32)Registers.PB << 16) | Registers.PCw;
\t\t\t\tconst uint8 ur_qa_nmi_old = ur_qa_nmi_gate ? Memory.RAM[0x01DD] : 0;
\t\t\t\tS9xOpcode_NMI();
\t\t\t\tif (ur_qa_nmi_gate)
\t\t\t\t\tfprintf(stderr,
\t\t\t\t\t\t"QASTACKNMI f=%u v=%u pc=%06X sp0=%04X sp1=%04X addr=01DD old=%02X new=%02X\\n",
\t\t\t\t\t\tur_qa_nmi_frame0, ur_qa_nmi_v0,
\t\t\t\t\t\t(unsigned)ur_qa_nmi_pc0, (unsigned)ur_qa_nmi_sp0,
\t\t\t\t\t\t(unsigned)Registers.S.W,
\t\t\t\t\t\t(unsigned)ur_qa_nmi_old, (unsigned)Memory.RAM[0x01DD]);
"""
        # Consume one native Snes9x NMI call exactly once.
        patched = patched.replace(NMI_MARKER, nmi, 1)
    return patched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path,
                        help="disposable .tools/src/snes9x-libretro/cpuexec.cpp")
    parser.add_argument("--single-address", type=lambda x: int(x, 0),
                        help="read-only observe one already-approved Switcher stack address")
    parser.add_argument("--watch-nmi", action="store_true",
                        help="also capture original NMI entry pre/post SP and 01DD byte")
    args = parser.parse_args()
    targets = (args.single_address,) if args.single_address is not None else TARGETS
    args.source.write_text(patch(args.source.read_text(encoding="utf-8"),
                                 targets=targets, watch_nmi=args.watch_nmi),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

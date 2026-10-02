#!/usr/bin/env python3
"""Inject a narrow intra-frame preparation-list trace into pinned Snes9x.

This is workflow-only instrumentation. It observes the already-recovered
producer stores at 81:A8FF / 81:AA34 and consumer entry at 82:D37F without
changing guest ROM state.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"""

SNIPPET = r'''			/* UR-Recomp preparation-list causal probe. */
			{
				uint16 prep_pcw = Registers.PCw;\n\t\t\t\tuint32 prep_pc = ((uint32)Registers.PB << 16) | prep_pcw;
				if (prep_pcw == 0xA8FF || prep_pcw == 0xAA34 || prep_pcw == 0xD37F)
				{
					auto prep_w16 = [](uint16 a) -> uint16 {
						return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
					};
					uint16 ca = prep_pc == 0x81A8FF ? Registers.Y.W : prep_w16(0x0DCD);
					uint16 cb = prep_pc == 0x81AA34 ? Registers.Y.W : prep_w16(0x0DCF);
					fprintf(stderr,
						"PREPTRACE frame=%u v=%u cycles=%d pc=%06X y=%04X ca=%u cb=%u "
						"camx=%u camy=%u edgex=%u edgey=%u camdx=%u ",
						(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
						(unsigned)prep_pc, (unsigned)Registers.Y.W,
						(unsigned)ca, (unsigned)cb,
						(unsigned)prep_w16(0x0419), (unsigned)prep_w16(0x041D),
						(unsigned)prep_w16(0x0505), (unsigned)prep_w16(0x050D),
						(unsigned)Memory.RAM[0x04F5]);
					fprintf(stderr, "a=");
					for (unsigned i = 0; i < ca && i < 16; i++)
						fprintf(stderr, "%s%04X:%02X", i ? "," : "",
							(unsigned)prep_w16((uint16)(0x0D8D + i * 2)),
							(unsigned)Memory.RAM[0x0D6D + i]);
					fprintf(stderr, " b=");
					for (unsigned i = 0; i < cb && i < 16; i++)
						fprintf(stderr, "%s%04X:%02X", i ? "," : "",
							(unsigned)prep_w16((uint16)(0x0DAD + i * 2)),
							(unsigned)Memory.RAM[0x0D7D + i]);
					fprintf(stderr, "\n");
				}
			}
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")
    if "UR-Recomp preparation-list causal probe" in text:
        return 0
    if MARKER not in text:
        raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
    text = text.replace(MARKER, SNIPPET + "\n" + MARKER, 1)
    args.source.write_text(text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

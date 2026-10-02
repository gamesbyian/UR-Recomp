#!/usr/bin/env python3
"""Inject narrow runtime tracing for the active race VRAM streaming queue."""
from __future__ import annotations
import argparse
from pathlib import Path

MARKER = """			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();"""

SNIPPET = r'''			/* UR-Recomp active race streaming queue causal probe. */
			{
				uint16 q_pcw = Registers.PCw;
				uint32 q_pc = ((uint32)Registers.PB << 16) | q_pcw;
				if (q_pcw == 0xF0BB || q_pcw == 0xF292 || q_pcw == 0xB8AB)
				{
					auto q_w16 = [](uint16 a) -> uint16 {
						return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
					};
					fprintf(stderr,
						"STREAMTRACE frame=%u v=%u cycles=%d pc=%06X "
						"ready=%u camx=%u camy=%u edgex=%u edgey=%u camdx=%u "
						"r0=%04X r1=%04X c0=%04X c1=%04X "
						"f0=%u f1=%u q=",
						(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
						(unsigned)q_pc, (unsigned)Memory.RAM[0x0306],
						(unsigned)q_w16(0x0419), (unsigned)q_w16(0x041D),
						(unsigned)q_w16(0x0505), (unsigned)q_w16(0x050D),
						(unsigned)Memory.RAM[0x04F5],
						(unsigned)q_w16(0x0FE9), (unsigned)q_w16(0x0FEB),
						(unsigned)q_w16(0x0D3F), (unsigned)q_w16(0x0D41),
						(unsigned)q_w16(0x0D1B), (unsigned)q_w16(0x0D1D));
					for (unsigned i = 0; i < 40; i++)
					{
						uint16 off = (uint16)(i * 2);
						uint16 bank = q_w16((uint16)(0x15A1 + off));
						if (bank == 0xFFFF) {
							fprintf(stderr, "%sEND", i ? "," : "");
							break;
						}
						fprintf(stderr, "%s%04X:%04X:%04X", i ? "," : "",
							(unsigned)bank,
							(unsigned)q_w16((uint16)(0x1645 + off)),
							(unsigned)q_w16((uint16)(0x16E9 + off)));
					}
					fprintf(stderr, "\n");
				}
			}
'''

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path)
    args=ap.parse_args()
    text=args.source.read_text(encoding="utf-8")
    if "UR-Recomp active race streaming queue causal probe" in text:
        return 0
    if MARKER not in text:
        raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
    args.source.write_text(text.replace(MARKER,SNIPPET+"\n"+MARKER,1),encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

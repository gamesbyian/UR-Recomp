#!/usr/bin/env python3
"""Inject narrow tracing around the camera-driven VRAM DMA descriptor queue."""
from __future__ import annotations
import argparse
from pathlib import Path

MARKER="""			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();"""

SNIPPET=r'''			/* UR-Recomp camera DMA queue causal probe. */
			{
				uint16 q_pcw = Registers.PCw;
				uint32 q_pc = ((uint32)Registers.PB << 16) | q_pcw;
				if ((Registers.PB == 0x81 && (q_pcw == 0xA59A || q_pcw == 0xA59D)) ||
				    (Registers.PB == 0x82 && (q_pcw == 0xD19B || q_pcw == 0xD2D1)))
				{
					auto q_w16 = [](uint16 a) -> uint16 {
						return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
					};
					fprintf(stderr,
						"CAMDMA frame=%u v=%u cycles=%d pc=%06X "
						"camx=%u camy=%u camdx=%d camdy=%d "
						"edgex=%u edgey=%u edgex2=%u edgey2=%u "
						"cnt=%u,%u,%u,%u mirror=%u desc=",
						(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
						(unsigned)q_pc,
						(unsigned)q_w16(0x0419), (unsigned)q_w16(0x041D),
						(int16)q_w16(0x04F5), (int16)q_w16(0x04F9),
						(unsigned)q_w16(0x0505), (unsigned)q_w16(0x050D),
						(unsigned)q_w16(0x0509), (unsigned)q_w16(0x0511),
						(unsigned)q_w16(0x052B), (unsigned)q_w16(0x052F),
						(unsigned)q_w16(0x0533), (unsigned)q_w16(0x0537),
						(unsigned)q_w16(0x0DDB));
					for (unsigned i=0;i<8;i++)
					{
						uint16 o=(uint16)(i*2);
						fprintf(stderr,"%s%u:%04X:%04X:%04X:%04X",
							i ? "," : "",
							(unsigned)q_w16((uint16)(0x03B9+o)),
							(unsigned)q_w16((uint16)(0x03C9+o)),
							(unsigned)q_w16((uint16)(0x0399+o)),
							(unsigned)q_w16((uint16)(0x03A9+o)),
							(unsigned)q_w16((uint16)(0x03D9+o)));
					}
					fprintf(stderr,"\n");
				}
			}
'''

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("source",type=Path); args=ap.parse_args()
 s=args.source.read_text(encoding="utf-8")
 if "UR-Recomp camera DMA queue causal probe" in s: return 0
 if MARKER not in s: raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
 args.source.write_text(s.replace(MARKER,SNIPPET+"\n"+MARKER,1),encoding="utf-8")
 return 0
if __name__=="__main__": raise SystemExit(main())

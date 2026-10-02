#!/usr/bin/env python3
"""Inject a narrow synchronized racer-composition trace into pinned Snes9x."""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();"""

SNIPPET = r'''			/* UR-Recomp synchronized racer cache-composition probe. */
			{
				uint16 rc_pcw = Registers.PCw;
				if ((Registers.PB & 0x7F) == 0x03 && (rc_pcw == 0xF129 || rc_pcw == 0xF292))
				{
					unsigned f = (unsigned)ICPU.Frame;
					auto rc_w16 = [](uint16 a) -> uint16 {
						return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
					};
					fprintf(stderr,
						"RACERCOMP frame=%u bank=%02X pc=%04X "
						"ids=%04X,%04X,%04X,%04X sel=%04X,%04X "
						"pm=%04X,%04X,%04X,%04X,%04X "
						"um=%04X,%04X,%04X,%04X,%04X "
						"off=%04X,%04X,%04X,%04X stage=",
						f, (unsigned)Registers.PB, (unsigned)rc_pcw,
						(unsigned)rc_w16(0x0FE9), (unsigned)rc_w16(0x0FEB),
						(unsigned)rc_w16(0x0D3F), (unsigned)rc_w16(0x0D41),
						(unsigned)rc_w16(0x0C83), (unsigned)rc_w16(0x0C85),
						(unsigned)rc_w16(0x0000), (unsigned)rc_w16(0x0002),
						(unsigned)rc_w16(0x0004), (unsigned)rc_w16(0x0006),
						(unsigned)rc_w16(0x0008),
						(unsigned)rc_w16(0x000A), (unsigned)rc_w16(0x000C),
						(unsigned)rc_w16(0x000E), (unsigned)rc_w16(0x0010),
						(unsigned)rc_w16(0x0012),
						(unsigned)rc_w16(0x002C), (unsigned)rc_w16(0x002E),
						(unsigned)rc_w16(0x0018), (unsigned)rc_w16(0x001A));
					if (rc_pcw == 0xF292)
					{
						for (unsigned i = 0; i < 82; i++)
						{
							uint16 q = (uint16)(i * 2);
							uint16 bankw = rc_w16((uint16)(0x15A1 + q));
							if ((bankw & 0x00FF) == 0x00FF)
								break;
							fprintf(stderr, "%s%02X:%04X:%04X",
								i ? "," : "",
								(unsigned)(bankw & 0x00FF),
								(unsigned)rc_w16((uint16)(0x1645 + q)),
								(unsigned)rc_w16((uint16)(0x16E9 + q)));
						}
					}
					fprintf(stderr, "\n");
				}
			}
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")
    if "UR-Recomp synchronized racer cache-composition probe" in text:
        return 0
    if MARKER not in text:
        raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
    args.source.write_text(text.replace(MARKER, SNIPPET + "\n" + MARKER, 1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

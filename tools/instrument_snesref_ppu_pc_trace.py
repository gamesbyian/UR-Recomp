#!/usr/bin/env python3
"""Inject a narrow CPU-direct PPU-write provenance trace into pinned Snes9x."""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """void S9xSetPPU (uint8 Byte, uint16 Address)
{
	// MAP_PPU: $2000-$3FFF
"""

SNIPPET = r'''void S9xSetPPU (uint8 Byte, uint16 Address)
{
	// UR-Recomp renderer-facing preparation/emission provenance probe.
	if (!CPU.InDMAorHDMA && Address >= 0x2116 && Address <= 0x2119)
	{
		auto prep_w16 = [](uint16 a) -> uint16 {
			return (uint16)(Memory.RAM[a] | (Memory.RAM[a + 1] << 8));
		};
		fprintf(stderr,
			"PPUPCTRACE frame=%u v=%u cycles=%d pc=%06X addr=%04X val=%02X "
			"ca=%u cb=%u camx=%u camy=%u edgex=%u edgey=%u camdx=%u\n",
			(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
			(unsigned)Registers.PBPC, (unsigned)Address, (unsigned)Byte,
			(unsigned)prep_w16(0x0DCD), (unsigned)prep_w16(0x0DCF),
			(unsigned)prep_w16(0x0419), (unsigned)prep_w16(0x041D),
			(unsigned)prep_w16(0x0505), (unsigned)prep_w16(0x050D),
			(unsigned)Memory.RAM[0x04F5]);
	}
	// MAP_PPU: $2000-$3FFF
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")
    if "UR-Recomp renderer-facing preparation/emission provenance probe" in text:
        return 0
    if MARKER not in text:
        raise SystemExit("ppu.cpp S9xSetPPU marker not found")
    text = text.replace(MARKER, SNIPPET, 1)
    args.source.write_text(text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

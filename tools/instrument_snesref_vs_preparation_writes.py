#!/usr/bin/env python3
"""Instrument Snes9x to log exact guest PCs that change VS preparation bytes."""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();"""

TARGETS = [
    0x0505, 0x0507, 0x0509, 0x050B,
    0x052B, 0x052D, 0x052F, 0x0531,
    0x03B9, 0x03BD, 0x03C1, 0x03C5,
    0x0DDB,
]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    args = ap.parse_args()
    s = args.source.read_text(encoding="utf-8")
    if "UR-Recomp exact VS preparation writer probe" in s:
        return 0
    if MARKER not in s:
        raise SystemExit("cpuexec.cpp opcode-dispatch marker not found")
    addrs = ", ".join(f"0x{x:04X}" for x in TARGETS)
    replacement = f"""			/* UR-Recomp exact VS preparation writer probe. */
			static const uint16 ur_vs_prep_addr[] = {{{addrs}}};
			static uint8 ur_vs_prep_prev[sizeof(ur_vs_prep_addr) / sizeof(ur_vs_prep_addr[0])];
			static bool ur_vs_prep_init = false;
			uint32 ur_vs_prep_pc = ((uint32)Registers.PB << 16) | Registers.PCw;
			if (!ur_vs_prep_init)
			{{
				for (unsigned ur_i = 0; ur_i < sizeof(ur_vs_prep_addr) / sizeof(ur_vs_prep_addr[0]); ++ur_i)
					ur_vs_prep_prev[ur_i] = Memory.RAM[ur_vs_prep_addr[ur_i]];
				ur_vs_prep_init = true;
			}}
			Registers.PCw++;
			(*Opcodes[Op].S9xOpcode)();
			for (unsigned ur_i = 0; ur_i < sizeof(ur_vs_prep_addr) / sizeof(ur_vs_prep_addr[0]); ++ur_i)
			{{
				uint8 ur_now = Memory.RAM[ur_vs_prep_addr[ur_i]];
				if (ur_now != ur_vs_prep_prev[ur_i])
				{{
					fprintf(stderr,
						"VSPREPWRITE frame=%u pc=%06X addr=%04X old=%02X new=%02X\\n",
						(unsigned)ICPU.Frame, (unsigned)ur_vs_prep_pc,
						(unsigned)ur_vs_prep_addr[ur_i],
						(unsigned)ur_vs_prep_prev[ur_i], (unsigned)ur_now);
					ur_vs_prep_prev[ur_i] = ur_now;
				}}
			}}"""
    args.source.write_text(s.replace(MARKER, replacement, 1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

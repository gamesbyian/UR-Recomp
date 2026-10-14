#!/usr/bin/env python3
"""Bounded original-Snes9x source probe for the Uniracers colour-HDMA WRAM writer.

Opt-in, opcode-by-opcode, compares only $7E:2084..2097 before/after each
original guest instruction. Optional semantic two-player arming is bounded\nto 256 original frames and requires live 0DDB=01 and 0313=01.\nThe probe reports actual executed PC candidates
without changing RAM, game, opcode, DMA or PPU behaviour. Must be compared
with native channel5 transfer observations before calling any PC the writer.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK = "UR_QA08_COLDATA_TABLE_WRITER"
OPCODE = "\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();"
CODE = r'''			/* UR_QA08_COLDATA_TABLE_WRITER: guarded original-emulator
			 * observation of the direct HDMA colour table in WRAM.
			 * Disabled unless BOTH original-emulator frame bounds are
			 * explicitly supplied, OR the separate strict original two-player\n\t\t\t * semantic arm gate is enabled. No write or flow-control effects. */
			{
				static int qa08_writer_init = 0;
				static unsigned long qa08_writer_first, qa08_writer_last;
				static unsigned qa08_writer_count;
				static unsigned qa08_brightness_count;
				static int qa08_writer_2p_armed = -1;
				static unsigned long qa08_writer_2p_first = ~0ul;
				if (qa08_writer_2p_armed < 0)
				{
					const char *setting = getenv("UR_QA08_ORIGINAL_WRITER_ARM_ON_2P");
					qa08_writer_2p_armed = (setting && setting[0] == '1' &&
					                         setting[1] == '\0') ? 1 : 0;
				}
				/* The independently observed second camera flag remains 1
				 * during active two-player play. Do not equate the libretro
				 * frame clock with native Baldosa guest frame 2208. */
				if (qa08_writer_2p_armed &&
				    qa08_writer_2p_first == ~0ul &&
				    Memory.RAM[0x0DDB] == 1 && Memory.RAM[0x0313] == 1)
				{
					qa08_writer_2p_first = (unsigned long)ICPU.Frame;
					fprintf(stderr,
					  "UR_QA08_COLDATA_TABLE_ARM frame=%u v=%u camera=01 race=01 mode=2p\n",
					  (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter);
				}
				if (!qa08_writer_init)
				{
					const char *first = getenv("UR_QA08_ORIGINAL_WRITER_FRAME_FIRST");
					const char *last = getenv("UR_QA08_ORIGINAL_WRITER_FRAME_LAST");
					char *e1 = NULL, *e2 = NULL;
					qa08_writer_init = 1;
					qa08_writer_first = 1;
					qa08_writer_last = 0; /* default disabled */
					if (first && *first && last && *last)
					{
						unsigned long a = strtoul(first, &e1, 10);
						unsigned long b = strtoul(last, &e2, 10);
						if (e1 != first && e2 != last &&
						    *e1 == '\0' && *e2 == '\0' &&
						    a <= b && b <= 500000ul && b-a <= 255ul)
						{
							qa08_writer_first = a;
							qa08_writer_last = b;
						}
					}
				}
				const unsigned long qa08_now = (unsigned long)ICPU.Frame;
				const bool qa08_writer_active =
					(qa08_now >= qa08_writer_first &&
					 qa08_now <= qa08_writer_last) ||
					(qa08_writer_2p_armed && qa08_writer_2p_first != ~0ul &&
					 qa08_now >= qa08_writer_2p_first &&
					 qa08_now - qa08_writer_2p_first <= 255ul);
				uint8 qa08_prior[20];
				uint8 qa08_brightness_prior[6];
				const uint32 qa08_executed_pc =
					((uint32)Registers.PB << 16) | (uint32)Registers.PCw;
				if (qa08_writer_active)
				{
					for (unsigned j = 0; j < 20; ++j)
						qa08_prior[j] = Memory.RAM[0x2084 + j];
					for (unsigned j = 0; j < 6; ++j)
						qa08_brightness_prior[j] = Memory.RAM[0x2064 + j];
				}
				Registers.PCw++;
				(*Opcodes[Op].S9xOpcode)();
				if (qa08_writer_active)
				{
					/* Source-grade executed 65816 bytes constructing CH7
					 * INIDISP table. No guest state is mutated, and a table
					 * byte change does not imply a final PPU register write. */
					for (unsigned j = 0; j < 6; ++j)
					{
						const uint8 after = Memory.RAM[0x2064 + j];
						if (qa08_brightness_prior[j] != after)
						{
							if (qa08_brightness_count == 4096u)
								fprintf(stderr,
									"UR_QA08_INIDISP_TABLE_WRITER_OVERFLOW limit=4096\n");
							else if (qa08_brightness_count < 4096u)
								fprintf(stderr,
									"UR_QA08_INIDISP_TABLE_WRITER frame=%u v=%u pc=%06X "
									"addr=7E:%04X before=%02X after=%02X\n",
									(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
									(unsigned)qa08_executed_pc,
									(unsigned)(0x2064 + j),
									(unsigned)qa08_brightness_prior[j],
									(unsigned)after);
							++qa08_brightness_count;
						}
					}
					for (unsigned j = 0; j < 20; ++j)
					{
						const uint8 after = Memory.RAM[0x2084 + j];
						if (qa08_prior[j] != after)
						{
							if (qa08_writer_count == 4096u)
								fprintf(stderr,
									"UR_QA08_COLDATA_TABLE_WRITER_OVERFLOW limit=4096\n");
							else if (qa08_writer_count < 4096u)
								fprintf(stderr,
									"UR_QA08_COLDATA_TABLE_WRITER frame=%u v=%u pc=%06X "
									"addr=7E:%04X before=%02X after=%02X\n",
									(unsigned)ICPU.Frame, (unsigned)CPU.V_Counter,
									(unsigned)qa08_executed_pc,
									(unsigned)(0x2084 + j),
									(unsigned)qa08_prior[j], (unsigned)after);
							++qa08_writer_count;
						}
					}
				}
			}'''

def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("original Snes9x WRAM writer probe already present")
    if (source.count(OPCODE) != 1 or
            "void S9xMainLoop (void)" not in source or
            "#include \"memmap.h\"" not in source):
        raise ValueError("pinned original Snes9x opcode-dispatch layout changed")
    # Resolve libc declarations on all Snes9x C++ build configurations.
    headers = '#include "memmap.h"'
    source = source.replace(headers, headers + '\n#include <stdlib.h>\n#include <stdio.h>', 1)
    return source.replace(OPCODE, CODE, 1)

def apply(path: Path, check_only: bool = False) -> Path:
    edited=patch_source(path.read_text(encoding="utf8"))
    if not check_only:
        path.write_text(edited,encoding="utf8")
    return path

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("--check-only",action="store_true")
    a=p.parse_args()
    try:
        dest=apply(a.source,a.check_only)
    except (OSError,ValueError) as exc:
        p.exit(2,f"QA08 original writer probe refused: {exc}\n")
    print(f"QA08 original WRAM writer probe staged={not a.check_only} source={dest}")

if __name__=="__main__":
    main()

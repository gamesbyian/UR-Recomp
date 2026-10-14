#!/usr/bin/env python3
"""Read-only live original Snes9x $2131/$2132 HDMA observation.

Only the disposable pinned snes9xgit/snes9x@1bcc369e Snes9x PPU is patched.
Emits after the actual PPU register semantics, not CPU journal entries.
The PPU call sees the DMA channel's still-current direct table pointer
before S9xDoHDMA increments it (the callsite is source-confirmed).
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_ORIGINAL_HDMA_PPU"
FUNCTION = "void S9xSetPPU (uint8 Byte, uint16 Address)\n{"
HDR = '#include "dma.h"'
CASE31 = "\n\t\t\t\tbreak;\n\n\t\t\tcase 0x2132: // COLDATA"
CASE32 = "\n\t\t\t\tbreak;\n\n\t\t\tcase 0x2133: // SETINI"

PROBE = r'''/* UR_QA08_ORIGINAL_HDMA_PPU: source-level execution witness only.
 * Emit only when intentionally armed for the original table-creation
 * neighbourhood, while S9xSetPPU is called from actual channel-5 HDMA.
 * No guest memory reads outside the known original $7E table, no writes. */
static void qa08_original_hdma_live_ppu(uint8 value, uint16 dest)
{
    static int qa08_init = 0, qa08_on = 0;
    static unsigned qa08_count = 0;
    if (!qa08_init) {
        const char *arm = getenv("UR_QA08_ORIGINAL_HDMA_PPU_WINDOW");
        qa08_on = (arm && strcmp(arm, "1781-1783") == 0);
        qa08_init = 1;
    }
    if (!qa08_on || ICPU.Frame < 1781 || ICPU.Frame > 1783 ||
        !CPU.InHDMA || !CPU.InDMAorHDMA ||
        CPU.CurrentDMAorHDMAChannel != 5 ||
        (dest != 0x2131 && dest != 0x2132))
        return;
    const SDMA *ch = &DMA[5];
    const unsigned offs = (unsigned)dest - (unsigned)(0x2100 + ch->BAddress);
    const unsigned src = ((unsigned)ch->Address + offs) & 0xffffu;
    const unsigned bank = ch->ABank;
    const unsigned observed = bank == 0x7e ? (unsigned)Memory.RAM[src] : 0xffu;
    const unsigned rgb = (unsigned)PPU.FixedColourRed |
                         ((unsigned)PPU.FixedColourGreen << 5) |
                         ((unsigned)PPU.FixedColourBlue << 10);
    if (qa08_count >= 128u) {
        if (qa08_count == 128u)
            fprintf(stderr,
                "UR_QA08_ORIGINAL_HDMA_PPU_OVERFLOW frame=%u max=128\n",
                (unsigned)ICPU.Frame);
        ++qa08_count;
        return;
    }
    ++qa08_count;
    fprintf(stderr,
        "UR_QA08_ORIGINAL_HDMA_PPU frame=%u v=%u cycles=%d "
        "channel=5 mode=%u indirect=%u bbus=%02X base=%02X "
        "source=%02X:%04X original_wram=%02X byte=%02X "
        "cgadsub=%02X cgwsel=%02X fixed15=%04X\n",
        (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
        (unsigned)ch->TransferMode,
        (unsigned)ch->HDMAIndirectAddressing,
        (unsigned)(dest & 0xff), (unsigned)ch->BAddress,
        bank, src, observed, (unsigned)value,
        dest == 0x2131 ? (unsigned)value :
                             (unsigned)Memory.FillRAM[0x2131],
        (unsigned)Memory.FillRAM[0x2130], rgb);
}

'''

def patch_source(src: str) -> str:
    if MARK in src:
        raise ValueError("original PPU HDMA source probe already applied")
    if (src.count(FUNCTION) != 1 or src.count(HDR) != 1 or
            src.count(CASE31) != 1 or src.count(CASE32) != 1 or
            'if (CPU.InDMAorHDMA)' not in src or
            'if (Byte & 0x80)' not in src or
            'PPU.FixedColourRed   = Byte & 0x1f;' not in src):
        raise ValueError("pinned original Snes9x PPU DMA/colour source changed")
    src = src.replace(HDR, HDR + '\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>', 1)
    src = src.replace(FUNCTION, PROBE + FUNCTION, 1)
    src = src.replace(CASE31, "\n\t\t\t\tqa08_original_hdma_live_ppu(Byte, 0x2131);"+CASE31, 1)
    src = src.replace(CASE32, "\n\t\t\t\tqa08_original_hdma_live_ppu(Byte, 0x2132);"+CASE32, 1)
    return src

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ppu_cpp", type=Path)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    try:
        patched = patch_source(args.ppu_cpp.read_text(encoding="utf8"))
        if not args.check_only:
            args.ppu_cpp.write_text(patched, encoding="utf8")
    except (OSError, ValueError) as exc:
        ap.exit(2, f"Original Snes9x PPU HDMA source probe refused: {exc}\n")
    print(f"QA08 original live HDMA PPU patch staged={not args.check_only}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Opt-in bounded DMA-channel entry trace for archived Snes9x 1.43.

Records descriptor fields at S9xDoDMA entry. Does not claim HDMA, a PPU
register latch, destination VMADD/OAMADD, successful transfer or final pixels.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ANCHOR = "    SDMA *d = &DMA[Channel];"
MARKER = "UR-Recomp bounded DMA entry provenance"
INSERT = r'''
    /* UR-Recomp bounded DMA entry provenance; entry-only, not DMA completion. */
    if (d->BAddress == 0x04 || d->BAddress == 0x18 ||
        d->BAddress == 0x19 || d->BAddress == 0x22)
    {
        fprintf(stderr, "URDMAPROV frame=%u v=%u cycles=%d pc=%06X "
                "channel=%u bank=%02X src=%04X bbus=%02X count=%04X "
                "mode=%u direction=%u fixed=%u decrement=%u\n",
                (unsigned)ICPU.Frame, (unsigned)CPU.V_Counter, CPU.Cycles,
                (unsigned)Registers.PBPC, (unsigned)Channel,
                (unsigned)d->ABank, (unsigned)d->AAddress,
                (unsigned)d->BAddress, (unsigned)d->TransferBytes,
                (unsigned)d->TransferMode, (unsigned)d->TransferDirection,
                (unsigned)d->AAddressFixed, (unsigned)d->AAddressDecrement);
    }
'''

def patch(source: str) -> str:
    if MARKER in source:
        return source
    if source.count(ANCHOR) != 1 or "void S9xDoDMA (uint8 Channel)" not in source:
        raise ValueError("unexpected archived Snes9x 1.43 DMA source; refusing patch")
    return source.replace(ANCHOR, ANCHOR + "\n" + INSERT, 1)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, help="private working copy of archived Snes9x 1.43 dma.cpp")
    a = p.parse_args()
    original = a.source.read_text(encoding="utf-8")
    result = patch(original)
    if result != original:
        a.source.write_text(result, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

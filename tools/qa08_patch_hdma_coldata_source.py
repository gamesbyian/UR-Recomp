#!/usr/bin/env python3
"""Opt-in pinned native HDMA $2132 COLDATA plus mode1 $2131 CGADSUB byte provenance.

Disposable Baldosa SNESRecomp DMA instrumentation only. Reads the real SNES
A-bus byte, channel, HDMA table pointer and post-write live fixed RGB15.
Does not replace source bytes, calculate pixels, alter renderer or guest state.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK="UR_QA08_HDMA_COLDATA"
ANCHOR=(
    "    debug_server_on_reg_write((uint16_t)(0x2100u + bAdr), val);\n"
    "    snes_writeBBus(dma->snes, bAdr, val);\n"
    "  }\n#ifdef SNESRECOMP_INTERP_PROFILE"
)
PATCH=r'''    debug_server_on_reg_write((uint16_t)(0x2100u + bAdr), val);
    snes_writeBBus(dma->snes, bAdr, val);
    /* UR_QA08_HDMA_COLDATA. Observe only real channel->PPU register
     * writes from this pinned native AOT, after the actual SNES BBUS
     * register write. No guest, PPU, DMA, or timing mutation. */
    {
      static long qa08_colour_frame = -2;
      static unsigned qa08_colour_writes = 0;
      static unsigned qa08_cgadsub_writes = 0;
      static unsigned qa08_inidisp_writes = 0;
      if (qa08_colour_frame == -2) {
        const char *setting = getenv("UR_QA08_HDMA_COLDATA_FRAME");
        char *end = NULL;
        qa08_colour_frame = -1;
        if (setting && *setting) {
          unsigned long candidate = strtoul(setting, &end, 10);
          if (end != setting && *end == '\0' && candidate <= 500000UL)
            qa08_colour_frame = (long)candidate;
        }
      }
      extern int snes_frame_counter;
      if (qa08_colour_frame >= 0 &&
          snes_frame_counter == qa08_colour_frame &&
          g_ppu_wlog_src == kPpuWlogHdma && bAdr == 0x32) {
        if (qa08_colour_writes == 2048u) {
          fprintf(stderr,
                  "UR_QA08_HDMA_COLDATA_OVERFLOW frame=%d limit=2048\n",
                  snes_frame_counter);
        } else if (qa08_colour_writes < 2048u) {
          uint32_t tagged_frame = 0;
          int16_t tagged_line = -1;
          ppu_wlog_position(&tagged_frame, &tagged_line);
          const DmaChannel *ch = &dma->channel[channel];
          fprintf(stderr,
                  "UR_QA08_HDMA_COLDATA frame=%d tagframe=%u line=%d "
                  "channel=%d bbus=%02X value=%02X src=%02X:%04X "
                  "mode=%u indirect=%u table=%04X bank=%02X fixed15=%04X\n",
                  snes_frame_counter, tagged_frame, tagged_line,
                  channel, bAdr, val, aBank, aAdr,
                  (unsigned)(ch->mode & 7), (unsigned)ch->indirect,
                  (unsigned)ch->tableAdr, (unsigned)ch->aBank,
                  (unsigned)(dma->snes->ppu->fixedColor & 0x7fff));
        }
        qa08_colour_writes++;
      }
      /* Companion of the mode-1 channel-5 $2132 write: the other
       * transfer goes to $2131 CGADSUB. Read after real BBUS dispatch.
       * Native observation ONLY; never modify the register or guest. */
      if (qa08_colour_frame >= 0 &&
          snes_frame_counter == qa08_colour_frame &&
          g_ppu_wlog_src == kPpuWlogHdma &&
          channel == 5 && bAdr == 0x31) {
        if (qa08_cgadsub_writes == 2048u) {
          fprintf(stderr,
                  "UR_QA08_HDMA_CGADSUB_OVERFLOW frame=%d limit=2048\n",
                  snes_frame_counter);
        } else if (qa08_cgadsub_writes < 2048u) {
          uint32_t tagged_frame = 0;
          int16_t tagged_line = -1;
          ppu_wlog_position(&tagged_frame, &tagged_line);
          const DmaChannel *ch = &dma->channel[channel];
          fprintf(stderr,
                  "UR_QA08_HDMA_CGADSUB frame=%d tagframe=%u line=%d "
                  "channel=%d bbus=%02X value=%02X src=%02X:%04X "
                  "mode=%u indirect=%u table=%04X bank=%02X cgadsub=%02X\n",
                  snes_frame_counter, tagged_frame, tagged_line,
                  channel, bAdr, val, aBank, aAdr,
                  (unsigned)(ch->mode & 7), (unsigned)ch->indirect,
                  (unsigned)ch->tableAdr, (unsigned)ch->aBank,
                  (unsigned)dma->snes->ppu->cgadsub);
        }
        qa08_cgadsub_writes++;
      }
      /* UR_QA08_HDMA_INIDISP: genuine $2100 PPU register write
       * after BBUS dispatch. Unlike the channel-5 colour pair,
       * its source HDMA channel is left open to empirical discovery. */
      if (qa08_colour_frame >= 0 &&
          snes_frame_counter == qa08_colour_frame &&
          g_ppu_wlog_src == kPpuWlogHdma && bAdr == 0x00) {
        if (qa08_inidisp_writes == 2048u) {
          fprintf(stderr,
                  "UR_QA08_HDMA_INIDISP_OVERFLOW frame=%d limit=2048\n",
                  snes_frame_counter);
        } else if (qa08_inidisp_writes < 2048u) {
          uint32_t tagged_frame = 0;
          int16_t tagged_line = -1;
          ppu_wlog_position(&tagged_frame, &tagged_line);
          const DmaChannel *ch = &dma->channel[channel];
          fprintf(stderr,
                  "UR_QA08_HDMA_INIDISP frame=%d tagframe=%u line=%d "
                  "channel=%d bbus=%02X value=%02X src=%02X:%04X "
                  "mode=%u indirect=%u table=%04X bank=%02X live_inidisp=%02X\n",
                  snes_frame_counter, tagged_frame, tagged_line,
                  channel, bAdr, val, aBank, aAdr,
                  (unsigned)(ch->mode & 7), (unsigned)ch->indirect,
                  (unsigned)ch->tableAdr, (unsigned)ch->aBank,
                  (unsigned)dma->snes->ppu->inidisp);
        }
        qa08_inidisp_writes++;
      }
    }
  }
#ifdef SNESRECOMP_INTERP_PROFILE'''

def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("QA08 HDMA colour source patch already applied")
    if (source.count(ANCHOR) != 1 or
            "static void dma_transferByte(" not in source or
            "void dma_doHdma(Dma* dma)" not in source or
            '#include "ppu.h"' not in source):
        raise ValueError("pinned SNESRecomp DMA transferByte/HDMA layout changed")
    return source.replace(ANCHOR,PATCH,1)

def apply(framework: Path, check_only: bool = False) -> Path:
    dest=framework/"runner/src/snes/dma.c"
    patched=patch_source(dest.read_text(encoding="utf8"))
    if not check_only:
        dest.write_text(patched,encoding="utf8")
    return dest

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--framework",type=Path,required=True)
    p.add_argument("--check-only",action="store_true")
    a=p.parse_args()
    try:
        dest=apply(a.framework,a.check_only)
    except (ValueError,OSError) as exc:
        p.exit(2,f"QA08 native HDMA COLDATA patch refused: {exc}\n")
    print(f"QA08 native HDMA byte provenance staged={not a.check_only} file={dest}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

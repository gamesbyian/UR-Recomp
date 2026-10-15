#!/usr/bin/env python3
"""DISPOSABLE read-only census of every REAL native HDMA PPU register write.

Source-qualified independent follow-up to the 460-source-pixel countdown
window contours after only ch7/ch5+7 priming. This instrument observes
actual A-bus BBUS writes in pinned Baldosa DMA, never guest/render state.
Apply AFTER the existing accepted read-only channel5/7 observer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_HDMA_ALL_CHANNELS_FRAME"
ANCHOR = (
    "    snes_writeBBus(dma->snes, bAdr, val);\n"
    "    /* UR_QA08_HDMA_COLDATA. Observe only real channel->PPU register\n"
)
INSERT = r'''    snes_writeBBus(dma->snes, bAdr, val);
    /* UR_QA08_HDMA_ALL_CHANNELS_FRAME: completely read-only source
     * census after the actual B-bus write. Opt-in ONE native guest
     * frame; no table address, channel state or register mutation.
     * Independent of the existing separately armed channel5/7 probe. */
    {
      static long qa08_all_frame = -2;
      static unsigned qa08_all_writes = 0;
      if (qa08_all_frame == -2) {
        const char *setting = getenv("UR_QA08_HDMA_ALL_CHANNELS_FRAME");
        char *end = NULL;
        qa08_all_frame = -1;
        if (setting && *setting) {
          unsigned long desired = strtoul(setting, &end, 10);
          if (end != setting && *end == '\0' && desired <= 500000UL)
            qa08_all_frame = (long)desired;
        }
      }
      extern int snes_frame_counter;
      if (qa08_all_frame >= 0 &&
          snes_frame_counter == qa08_all_frame &&
          g_ppu_wlog_src == kPpuWlogHdma) {
        if (qa08_all_writes == 16384u) {
          fprintf(stderr, "UR_QA08_HDMA_ALL_OVERFLOW frame=%d limit=16384\n",
                  snes_frame_counter);
        } else if (qa08_all_writes < 16384u) {
          uint32_t qa08_tagframe = 0;
          int16_t qa08_line = -1;
          ppu_wlog_position(&qa08_tagframe, &qa08_line);
          const DmaChannel *qa08_ch = &dma->channel[channel];
          fprintf(stderr,
                  "UR_QA08_HDMA_ALL frame=%d tagframe=%u line=%d "
                  "channel=%d bbus=%02X value=%02X src=%02X:%04X "
                  "mode=%u indirect=%u table=%04X bank=%02X "
                  "rep=%02X transfer=%u\n",
                  snes_frame_counter, qa08_tagframe, qa08_line,
                  channel, bAdr, val, aBank, aAdr,
                  (unsigned)(qa08_ch->mode & 7),
                  (unsigned)qa08_ch->indirect,
                  (unsigned)qa08_ch->tableAdr,
                  (unsigned)qa08_ch->aBank,
                  (unsigned)qa08_ch->repCount,
                  (unsigned)qa08_ch->doTransfer);
        }
        qa08_all_writes++;
      }
    }
    /* UR_QA08_HDMA_COLDATA. Observe only real channel->PPU register
'''


def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("all-channel source observer already staged")
    if (source.count(ANCHOR) != 1
        or source.count("UR_QA08_HDMA_COLDATA") < 1
        or source.count("snes_writeBBus(dma->snes, bAdr, val);") != 1
        or "void dma_doHdma(Dma* dma)" not in source):
        raise ValueError("pinned source-ordered HDMA read-only observer not found")
    return source.replace(ANCHOR, INSERT, 1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--framework", type=Path, required=True)
    p.add_argument("--apply-experiment", action="store_true")
    args = p.parse_args()
    path = args.framework / "runner/src/snes/dma.c"
    try:
        source = path.read_text(encoding="utf-8")
        changed = patch_source(source)
        if args.apply_experiment:
            path.write_text(changed, encoding="utf-8")
    except (ValueError, OSError) as exc:
        p.exit(2, f"QA08_ALL_CHANNEL_SOURCE_REJECTED {exc}\n")
    print("QA08_ALL_CHANNEL_HDMA_SOURCE_STAGED "
          f"applied={args.apply_experiment} path={path} "
          "real_native_write_events_not_yet_captured=true")


if __name__ == "__main__":
    main()

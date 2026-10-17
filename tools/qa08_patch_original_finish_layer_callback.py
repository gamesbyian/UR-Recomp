#!/usr/bin/env python3
"""Read-only original 2014 Snes9x libretro callback BG/OBJ depth witness.

Patch only a disposable exact-pinned libretro source checkout. At *exact*
original callback indexes 3791 and 3871 log already-rendered RGB565, main and
sub depth-buffer words, CGRAM words and PPU colour-math registers. Never
change inputs, source pixels, hardware state, frame phase or rendering. The
paired original 263-frame source image SHA256 admission belongs to the
separate CI script, and a diagnostic is not original/hardware acceptance.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK="UR_QA08_2014_ORIGINAL_FINISH_LAYER_READONLY"
INTRO="""bool8 S9xDeinitUpdate(int width, int height)
{
    static int burst_phase = 0;"""
IMPL=r'''bool8 S9xDeinitUpdate(int width, int height)
{
    /* UR_QA08_2014_ORIGINAL_FINISH_LAYER_READONLY: original callback ordering,
     * never a host do_dump(g_frame=N) phase guess. This function emits the
     * *actual* libretro video callback subsequently consumed by snesref.
     * Existing SNES9x framebuffer, depth-buffer and CGRAM are read only.
     * No renderer/source pixel edits, no requested extra retro_run. */
    static unsigned qa08_callback_ordinal = 0;
    const unsigned qa08_actual_callback = qa08_callback_ordinal++;
    const char *qa08_opt = getenv("UR_QA08_SNES9X_FINISH_LAYERS");
    if (qa08_opt && strcmp(qa08_opt,"original-2p-3791-3871")==0 &&
        (qa08_actual_callback == 3791u || qa08_actual_callback == 3871u)) {
        const unsigned x=121u,y=165u;
        if (width != 256 || height != 224 || GFX.PPL < 256 ||
            GFX.RealPPL < 256 || !GFX.ZBuffer || !GFX.SubZBuffer ||
            !GFX.Screen || !GFX.SubScreen) {
            fprintf(stderr,"QA08_ORIGINAL_FINISH_LAYER_REJECT callback=%u geometry=%dx%d\n",
                    qa08_actual_callback,width,height);
        } else {
            const unsigned screen_at=y*GFX.PPL+x;
            const unsigned z_at=y*GFX.RealPPL+x;
            fprintf(stderr,
              "QA08_ORIGINAL_FINISH_LAYER callback=%u cpu_frame=%u "
              "total_emulated=%u x=%u y=%u RGB565=%04x "
              "main_depth=%u sub_depth=%u sub_RGB565=%04x "
              "bgmode=%u brightness=%u blank=%u "
              "TM=%02x TS=%02x CGWSEL=%02x CGADSUB=%02x "
              "CGRAM_1B=%04x CGRAM_C6=%04x "
              "width=%d height=%d\n",
              qa08_actual_callback,(unsigned)ICPU.Frame,
              (unsigned)IPPU.TotalEmulatedFrames,x,y,
              (unsigned)GFX.Screen[screen_at],
              (unsigned)GFX.ZBuffer[z_at],
              (unsigned)GFX.SubZBuffer[z_at],
              (unsigned)GFX.SubScreen[z_at],
              (unsigned)PPU.BGMode,(unsigned)PPU.Brightness,
              (unsigned)PPU.ForcedBlanking,
              (unsigned)Memory.FillRAM[0x212c],(unsigned)Memory.FillRAM[0x212d],
              (unsigned)Memory.FillRAM[0x2130],(unsigned)Memory.FillRAM[0x2131],
              (unsigned)PPU.CGDATA[0x1b],(unsigned)PPU.CGDATA[0xc6],
              width,height);
        }
    }
    static int burst_phase = 0;'''


def patch_source(source:str)->str:
    if MARK in source:
        if source.count(MARK)!=1 or source.count(IMPL)!=1:
            raise ValueError("partial or forged pinned Snes9x source observation")
        return source
    if source.count(INTRO)!=1 or source.count("#include <stdio.h>")!=1 or (
        source.count("video_cb(GFX.Screen +")==0
    ):
        raise ValueError("unrecognized pinned original libretro video source")
    return source.replace("#include <stdio.h>","#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>",1).replace(INTRO,IMPL,1)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("--apply",action="store_true")
    a=parser.parse_args()
    src=a.source.read_text(encoding="utf8")
    patched=patch_source(src)
    if a.apply and patched!=src:
        a.source.write_text(patched,encoding="utf8")
    print("QA08_ORIGINAL_FINISH_SOURCE_LAYER_STAGED",
          "changed="+str(int(patched!=src)), "apply="+str(int(a.apply)),
          "no_pixel_or_CPU_edits=1")


if __name__=="__main__":
    main()

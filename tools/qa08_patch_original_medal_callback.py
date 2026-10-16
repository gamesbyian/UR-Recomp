#!/usr/bin/env python3
"""One-shot original 2014 Snes9x medal pixel + OAM attribution (read-only).

Observe five independently chosen mismatching native/source coordinates at
exact original video callbacks 4031 and 4175; also observe seven OAM slots.
This modifies only diagnostic stdout in the disposable PINNED libretro
source, never game input, guest memory, raster pixels or tile interpretation.
263/263 immutable original callback pictures are verified separately.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK="UR_QA08_ORIGINAL_MEDAL_2P_CALLBACK_READONLY"
ANCHOR="""bool8 S9xDeinitUpdate(int width, int height)
{
    static int burst_phase = 0;"""
OBS=r'''bool8 S9xDeinitUpdate(int width, int height)
{
    /* UR_QA08_ORIGINAL_MEDAL_2P_CALLBACK_READONLY: the existing actual
     * original libretro video callback. Zero new original emulated frames,
     * zero modified framebuffer/OAM/CGRAM registers or guest operation. */
    static unsigned qa08_medal_callback_number = 0;
    const unsigned qa08_cb = qa08_medal_callback_number++;
    const char *qa08_selector = getenv("UR_QA08_ORIGINAL_MEDAL_PIXELS");
    if (qa08_selector &&
        strcmp(qa08_selector, "2p-4031-4175")==0 &&
        (qa08_cb==4031u || qa08_cb==4175u)) {
        const unsigned qa08_xs[5]={207,205,205,225,225};
        const unsigned qa08_ys[5]={91,115,139,96,120};
        const unsigned qa08_slots[7]={96,97,98,99,112,113,114};
        if (width!=256 || height!=224 || GFX.PPL<256 ||
            GFX.RealPPL<256 || !GFX.Screen || !GFX.SubScreen ||
            !GFX.ZBuffer || !GFX.SubZBuffer) {
            fprintf(stderr,"QA08_ORIGINAL_MEDAL_REJECT callback=%u geometry=%dx%d\n",
                    qa08_cb,width,height);
        } else {
            for (unsigned qi=0;qi<5;qi++) {
                const unsigned x=qa08_xs[qi], y=qa08_ys[qi];
                const unsigned si=y*GFX.PPL+x;
                const unsigned zi=y*GFX.RealPPL+x;
                fprintf(stderr,
                    "QA08_ORIGINAL_MEDAL_PIXEL callback=%u cpu_frame=%u "
                    "total_emulated=%u x=%u y=%u RGB565=%04x "
                    "main_depth=%u sub_depth=%u sub_RGB565=%04x "
                    "bgmode=%u brightness=%u forced_blank=%u "
                    "TM=%02x TS=%02x CGWSEL=%02x CGADSUB=%02x "
                    "CGRAM_1B=%04x CGRAM_C6=%04x\n",
                    qa08_cb,(unsigned)ICPU.Frame,
                    (unsigned)IPPU.TotalEmulatedFrames,x,y,
                    (unsigned)GFX.Screen[si],
                    (unsigned)GFX.ZBuffer[zi],
                    (unsigned)GFX.SubZBuffer[zi],
                    (unsigned)GFX.SubScreen[zi],
                    (unsigned)PPU.BGMode,(unsigned)PPU.Brightness,
                    (unsigned)PPU.ForcedBlanking,
                    (unsigned)Memory.FillRAM[0x212c],
                    (unsigned)Memory.FillRAM[0x212d],
                    (unsigned)Memory.FillRAM[0x2130],
                    (unsigned)Memory.FillRAM[0x2131],
                    (unsigned)PPU.CGDATA[0x1b],
                    (unsigned)PPU.CGDATA[0xc6]);
            }
            for (unsigned qi=0;qi<7;qi++) {
                const unsigned slot=qa08_slots[qi];
                fprintf(stderr,
                    "QA08_ORIGINAL_MEDAL_OAM callback=%u slot=%u "
                    "tile=%03x palette=%u priority=%u x=%d y=%d\n",
                    qa08_cb,slot,(unsigned)PPU.OBJ[slot].Name,
                    (unsigned)PPU.OBJ[slot].Palette,
                    (unsigned)PPU.OBJ[slot].Priority,
                    (int)PPU.OBJ[slot].HPos,(int)PPU.OBJ[slot].VPos);
            }
        }
    }
    static int burst_phase = 0;'''

def patch_source(source:str)->str:
    if MARK in source:
        if source.count(MARK)!=1 or source.count(OBS)!=1:
            raise ValueError("tampered or partially applied original medal observer")
        return source
    if (source.count(ANCHOR)!=1
        or source.count("#include <stdio.h>")!=1
        or source.count("video_cb(GFX.Screen +")<1):
        raise ValueError("not the pinned 2014 libretro callback source")
    return source.replace("#include <stdio.h>",
                          "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>",1).replace(
        ANCHOR,OBS,1)

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    source=a.source.read_text(encoding="utf8")
    new=patch_source(source)
    if a.apply and source!=new:
        a.source.write_text(new,encoding="utf8")
    print("QA08_ORIGINAL_MEDAL_CALLBACK_READY",a.source,"applied="+str(int(a.apply)),
          "pixels_or_guest_changed=0")

if __name__=="__main__":
    main()

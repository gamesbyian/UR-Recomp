#!/usr/bin/env python3
"""QA-08 original Snes9x results: read seven sprite sources' 4bpp opacity.

This patches only the disposable exact-pinned 2014 libretro video callback,
reading live OAM and VRAM *after* the rendering and logging 16x16 indexed
source tile hashes/opacity counts, never altering sprite data or output. The
263 historical original 256x224 source images are independently checked.
No ROM, full VRAM image, decoded sprites or new graphics asset is exported.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK="UR_QA08_READONLY_MEDAL_4BPP_TILE_FINGERPRINT"
ANCHOR="""bool8 S9xDeinitUpdate(int width, int height)
{
    static int burst_phase = 0;"""
HOOK=r'''bool8 S9xDeinitUpdate(int width, int height)
{
    /* UR_QA08_READONLY_MEDAL_4BPP_TILE_FINGERPRINT: read-only real source.
     * Derivation follows pinned gfx.cpp DrawOBJS BaseTile and tileimpl.h
     * GetCachedTile (OBJ name/page => 4bpp VRAM base + 32 bytes/tile).
     * No tile, CGRAM, OAM, guest or framebuffer modification. */
    static unsigned qa08_original_callback_number = 0;
    const unsigned qa08_cb = qa08_original_callback_number++;
    const char *qa08_opt = getenv("UR_QA08_ORIGINAL_MEDAL_TILEBITS");
    if (qa08_opt &&
        strcmp(qa08_opt,"original-2p-4031-4175")==0 &&
        (qa08_cb==4031u || qa08_cb==4175u)) {
        const unsigned slots[7]={96,97,98,99,112,113,114};
        const int xs[5]={207,205,205,225,225};
        const int ys[5]={91,115,139,96,120};
        if (width!=256 || height!=224 || PPU.OBJSizeSelect!=3 ||
            !Memory.VRAM || !GFX.Screen) {
            fprintf(stderr,"QA08_ORIGINAL_4BPP_REJECT callback=%u geometry=%dx%d size=%u\n",
                    qa08_cb,width,height,(unsigned)PPU.OBJSizeSelect);
        } else {
            unsigned tilepixels[7][16][16];
            unsigned short palette_words[7][16];
            for (unsigned si=0;si<7;si++) {
                const unsigned slot=slots[si];
                const struct SOBJ *obj=&PPU.OBJ[slot];
                if (obj->Size) {
                    fprintf(stderr,"QA08_ORIGINAL_4BPP_REJECT callback=%u slot=%u is_large=1\n",
                            qa08_cb,slot);
                    break;
                }
                unsigned counts[16]={0};
                unsigned mask_rows[16]={0};
                unsigned long long digest=14695981039346656037ULL;
                for (unsigned y=0;y<16;y++) {
                    for (unsigned x=0;x<16;x++) {
                        const unsigned vx=obj->HFlip?(15-x):x;
                        const unsigned vy=obj->VFlip?(15-y):y;
                        const unsigned name=(unsigned)obj->Name&511u;
                        const unsigned tile=(name&0x100u) |
                          (((name&0xf0u)+((vy>>3)<<4))&0xf0u) |
                          ((name+(vx>>3))&0x0fu);
                        const unsigned at=(PPU.OBJNameBase +
                            tile*32u + ((tile&0x100u)?PPU.OBJNameSelect:0u))&0xffffu;
                        const unsigned row=vy&7u, bit=7u-(vx&7u);
                        const unsigned value=
                            ((Memory.VRAM[(at+row*2u)&0xffffu]>>bit)&1u) |
                            (((Memory.VRAM[(at+row*2u+1u)&0xffffu]>>bit)&1u)<<1) |
                            (((Memory.VRAM[(at+16u+row*2u)&0xffffu]>>bit)&1u)<<2) |
                            (((Memory.VRAM[(at+17u+row*2u)&0xffffu]>>bit)&1u)<<3);
                        tilepixels[si][y][x]=value;
                        counts[value]++;
                        if (value) mask_rows[y]|=(1u<<x);
                        digest^=value;
                        digest*=1099511628211ULL;
                    }
                }
                for (unsigned v=0;v<16;v++) {
                    const unsigned idx=128u+(unsigned)obj->Palette*16u+v;
                    palette_words[si][v]=(unsigned short)PPU.CGDATA[idx];
                }
                fprintf(stderr,
                    "QA08_ORIGINAL_TILE_SOURCE cb=%u slot=%u x=%d y=%d "
                    "name=%03x pal=%u priority=%u size=16 "
                    "hflip=%u vflip=%u base=%04x select=%04x "
                    "nonzero=%u indexed16_FNV64=%016llx\n",
                    qa08_cb,slot,(int)obj->HPos,(int)obj->VPos,
                    (unsigned)obj->Name,(unsigned)obj->Palette,
                    (unsigned)obj->Priority,(unsigned)obj->HFlip,
                    (unsigned)obj->VFlip,(unsigned)PPU.OBJNameBase,
                    (unsigned)PPU.OBJNameSelect,256u-counts[0],digest);
                for (unsigned y=0;y<16;y++) {
                    fprintf(stderr,
                        "QA08_ORIGINAL_TILE_ROW cb=%u slot=%u row=%u "
                        "opaque_mask=%04x\n",qa08_cb,slot,y,mask_rows[y]);
                }
                fprintf(stderr,"QA08_ORIGINAL_TILE_COUNTS cb=%u slot=%u",
                        qa08_cb,slot);
                for (unsigned v=0;v<16;v++) {
                    fprintf(stderr," c%u=%u",v,counts[v]);
                }
                fprintf(stderr,"\n");
            }
            for (unsigned i=0;i<5;i++) {
                fprintf(stderr,"QA08_ORIGINAL_TILE_SAMPLE cb=%u x=%d y=%d",
                        qa08_cb,xs[i],ys[i]);
                for (unsigned si=0;si<7;si++) {
                    const struct SOBJ *obj=&PPU.OBJ[slots[si]];
                    const int x=xs[i]-(int)obj->HPos;
                    const int y=(ys[i]-(int)obj->VPos+256)&255;
                    if (x<0 || x>=16 || y>=16) {
                        fprintf(stderr," s%u=outside",slots[si]);
                    } else {
                        const unsigned v=tilepixels[si][y][x];
                        fprintf(stderr," s%u=%u.%04x",slots[si],v,
                                (unsigned)palette_words[si][v]);
                    }
                }
                fprintf(stderr,"\n");
            }
        }
    }
    static int burst_phase = 0;'''


def patched(original:str)->str:
    if MARK in original:
        if original.count(MARK)!=1 or original.count(HOOK)!=1:
            raise ValueError("unrecognized or incomplete 2014 medal tile patch")
        return original
    if (original.count(ANCHOR)!=1 or
        original.count("#include <stdio.h>")!=1 or
        original.count("video_cb(GFX.Screen +")<1):
        raise ValueError("not exact original pinned libretro video callback")
    return original.replace("#include <stdio.h>",
                            "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>",1
                            ).replace(ANCHOR,HOOK,1)


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source",type=Path)
    ap.add_argument("--apply",action="store_true")
    a=ap.parse_args()
    s=a.source.read_text()
    new=patched(s)
    if a.apply and s!=new:
        a.source.write_text(new)
    print("QA08_ORIGINAL_4BPP_READONLY_READY applied="+str(int(a.apply))+
          " pixel_output_changed=0 full_ROM_VRAM_export=0")

if __name__=="__main__":
    main()

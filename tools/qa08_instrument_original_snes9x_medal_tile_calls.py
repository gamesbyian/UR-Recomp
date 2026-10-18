#!/usr/bin/env python3
"""Read-only ORIGINAL pinned Snes9x actual DrawOBJS tile-call source witness.

Never alter the original ROM/controller/CPU/PPU event clocks, tiled output,
colour, OAM order or source presentation. The selected 2014 source framebuffer
at an end-of-field callback is not equivalent to a native scanline without
independent registration. Instrument only authentic tile painter calls
inside original gfx.cpp DrawOBJS; no second sprite renderer is introduced.
"""
from __future__ import annotations
import argparse
from pathlib import Path

PIN="1bcc369e89f08243e0a462882fb1f3e42e51de3a"
MARK="UR_QA08_ORIGINAL_SNES9X_ACTIVE_MEDAL_TILE_CALL"
HEADER='#include "display.h"'
METHOD="static void DrawOBJS (int D)"
DRAW='\t\t\t\t\t\tif (DrawMode)\n\t\t\t\t\t\t\tDrawTile(BaseTile | TileX, O, TileLine, 1);'
CLIPPED='\t\t\t\t\t\tif (DrawMode)\n\t\t\t\t\t\t\tDrawClippedTile(BaseTile | TileX, O, x - X, w, TileLine, 1);'
HELPER=r'''
/* UR_QA08_ORIGINAL_SNES9X_ACTIVE_MEDAL_TILE_CALL.
 * Original Snes9x sprite painter input/output observation, read-only.
 * Actual tile call executes ONCE, without modifying any emulated or PPU
 * state. Each logged record is a tile-CANDIDATE, not an asserted winner;
 * a same-depth sprite may repaint and later BG may occlude it.
 * Original frame labels do not establish native guest equivalence. */
struct UrQa08OrigObjPre {
    bool armed[5];
    uint8 z[5];
    uint16 rgb[5];
};
static const int urqa08_xs[5] = {207,205,205,225,225};
static const int urqa08_ys[5] = {91,115,139,96,120};
static UrQa08OrigObjPre urqa08_original_before(int depth, unsigned y,
                                                 int x0, int x1) {
    UrQa08OrigObjPre q={};
    const unsigned f=(unsigned)ICPU.Frame;
    if (depth<32 || !((f>=4028 && f<=4036) ||
                       (f>=4172 && f<=4180)))
        return q;
    for (int i=0;i<5;i++) {
        const int x=urqa08_xs[i];
        if ((int)y!=urqa08_ys[i] || x<x0 || x>=x1) continue;
        q.armed[i]=true;
        q.z[i]=GFX.DB[y*GFX.PPL+x];
        q.rgb[i]=GFX.S[y*GFX.PPL+x];
    }
    return q;
}
static void urqa08_original_after(const UrQa08OrigObjPre& q, unsigned y,
                                  int oam_slot, uint32 tile, int tile_line,
                                  int from_x, int to_x, int drawmode) {
    for (int i=0;i<5;i++) {
        if (!q.armed[i]) continue;
        int x=urqa08_xs[i];
        const uint8 after_z=GFX.DB[y*GFX.PPL+x];
        const uint16 after_rgb=GFX.S[y*GFX.PPL+x];
        fprintf(stderr,
            "UR_QA08_ORIGINAL_ACTIVE_MEDAL_TILE frame=%u y=%u x=%d "
            "slot=%d objname=%03x palette=%u priority=%u "
            "src_tile=%04x tileline=%d tile_span=%d,%d drawmode=%d "
            "zbefore=%02x zafter=%02x rgbbefore=%04x rgbafter=%04x "
            "changed_z=%u changed_rgb=%u original_guest_phase_proven=0\n",
            (unsigned)ICPU.Frame,y,x,oam_slot,
            (unsigned)PPU.OBJ[oam_slot].Name,
            (unsigned)PPU.OBJ[oam_slot].Palette,
            (unsigned)PPU.OBJ[oam_slot].Priority,
            (unsigned)tile,tile_line,from_x,to_x,drawmode,
            (unsigned)q.z[i],(unsigned)after_z,
            (unsigned)q.rgb[i],(unsigned)after_rgb,
            (unsigned)(q.z[i]!=after_z),(unsigned)(q.rgb[i]!=after_rgb));
    }
}
'''
MAIN_DRAW='''						if (DrawMode)
                        {
                            const uint32 source_tile=BaseTile | TileX;
                            const UrQa08OrigObjPre original_pre =
                                urqa08_original_before(D,Y,X,X+8);
                            DrawTile(source_tile,O,TileLine,1);
                            urqa08_original_after(original_pre,Y,S,source_tile,
                                                  TileLine,X,X+8,DrawMode);
                        }'''
CLIP_DRAW='''						if (DrawMode)
                        {
                            const uint32 source_tile=BaseTile | TileX;
                            const UrQa08OrigObjPre original_pre =
                                urqa08_original_before(D,Y,x,x+w);
                            DrawClippedTile(source_tile,O,x-X,w,TileLine,1);
                            urqa08_original_after(original_pre,Y,S,source_tile,
                                                  TileLine,x,x+w,DrawMode);
                        }'''

def patch_source(source:str)->str:
    if MARK in source:
        raise ValueError("original gfx.cpp already has diagnostic instrumentation")
    if (source.count(HEADER)!=1 or source.count(METHOD)!=1 or
        source.count(DRAW)!=1 or source.count(CLIPPED)!=1 or
        "for (uint32 Y = GFX.StartY" not in source or
        "GFX.DB = GFX.ZBuffer;" not in source or
        'DrawOBJS(D + 4);' not in source):
        raise ValueError("original Snes9x gfx.cpp tile-painter source diverged")
    source=source.replace(HEADER,HEADER+"\n#include <stdio.h>\n",1)
    source=source.replace(METHOD,HELPER+"\n"+METHOD,1)
    source=source.replace(DRAW,MAIN_DRAW,1)
    source=source.replace(CLIPPED,CLIP_DRAW,1)
    if (source.count(MARK)!=1 or
        source.count("DrawTile(source_tile,O,TileLine,1);")!=1 or
        source.count("DrawClippedTile(source_tile,O,x-X,w,TileLine,1);")!=1):
        raise ValueError("partial source injection or an extra tile painter")
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    try:
        raw=a.source.read_text(encoding="utf8")
        patched=patch_source(raw)
        if a.apply:a.source.write_text(patched,encoding="utf8")
    except (OSError,ValueError) as e:
        p.exit(2,"QA08_ORIGINAL_TILE_SOURCE_REFUSED: "+str(e)+"\n")
    print("QA08_ORIGINAL_SNES9X_TILE_SOURCE",
          a.source,"applied="+str(int(a.apply)),
          "original_guest_untouched=1 source_owner_unproven=1")
if __name__=="__main__":
    main()

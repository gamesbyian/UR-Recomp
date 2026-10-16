#!/usr/bin/env python3
"""QA-08: read only real Windows PPU OBJ tile planes at four medal pixels.

Patch exact-pinned disposable Baldosa legacy renderer only, AFTER existing
verified per-pixel/OAM provenance observer. Capture raw guest and optional
host render-override VRAM words independently of OBJ-buffer output. No
read writes, no sprite re-evaluation, no timing/palette change.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools import baldosa_qa08_native_effective_pixel_owner_patch as prior
except ImportError:
    import baldosa_qa08_native_effective_pixel_owner_patch as prior

MARK="UR_QA08_NATIVE_MEDAL_LIVE_VRAM_INDEX"
RELATIVE=prior.RELATIVE
ANCHOR=prior.END+prior.TRACE
ADDED=r'''  /* UR_QA08_NATIVE_MEDAL_LIVE_VRAM_INDEX: same effective scanline pixel.
   * Derives raw OBJ 4bpp tile from OAM and genuine guest / render VRAM.
   * No pixel producer, VRAM/OAM/write timing or emulator state modifications. */
  if ((snes_frame_counter == 4032 || snes_frame_counter == 4176) &&
      x == 225 && (y == 97 || y == 121) &&
      getenv("UR_QA08_WINDOWS_MEDAL_VRAM_TRACE")) {
    const unsigned slots[2] = {(y == 97) ? 97u : 96u,
                               (y == 97) ? 99u : 98u};
    for (unsigned qi = 0; qi < 2; ++qi) {
    const unsigned slot = slots[qi];
    const unsigned oam0 = (unsigned)ppu->oam[slot * 2u];
    const unsigned oam1 = (unsigned)ppu->oam[slot * 2u + 1u];
    const unsigned sx = oam0 & 255u, sy = (oam0 >> 8u) & 255u;
    const int xoff = x - (int)sx;
    const int yoff = ((y - 1 - (int)sy) + 256) & 255;
    const unsigned large = ((unsigned)ppu->highOam[slot >> 2u] >>
                           ((slot & 3u) * 2u + 1u)) & 1u;
    if (xoff >= 0 && xoff < 16 && yoff >= 0 && yoff < 16 &&
        PPU_objSize(ppu) == 3 && large == 0u && !PPU_objInterlace(ppu)) {
      const unsigned usedcol = (oam1 & 0x4000u) ? (15u - (unsigned)xoff) : (unsigned)xoff;
      const unsigned usedrow = (oam1 & 0x8000u) ? (15u - (unsigned)yoff) : (unsigned)yoff;
      const unsigned tile = (((((oam1 & 255u) >> 4u) + (usedrow >> 3u)) << 4u) |
                             (((oam1 & 15u) + (usedcol >> 3u)) & 15u)) & 511u;
      const unsigned bank = (oam1 & 0x100u) ? PPU_objTileAdr2(ppu) : PPU_objTileAdr1(ppu);
      const unsigned wa = (bank + tile * 16u + (usedrow & 7u)) & 0x7fffu;
      const unsigned bit = 7u - (usedcol & 7u);
      const unsigned guest0 = (unsigned)ppu->vram[wa];
      const unsigned guest8 = (unsigned)ppu->vram[(wa+8u)&0x7fffu];
      const uint16_t *rv = PpuRenderVram(ppu);
      const unsigned render0 = (unsigned)rv[wa];
      const unsigned render8 = (unsigned)rv[(wa+8u)&0x7fffu];
      const unsigned guestplane = guest0 | (guest8 << 16u);
      const unsigned renderplane = render0 | (render8 << 16u);
      const unsigned guest_index = ((guestplane >> bit) & 1u) |
                   ((guestplane >> (bit+7u)) & 2u) |
                   ((guestplane >> (bit+14u)) & 4u) |
                   ((guestplane >> (bit+21u)) & 8u);
      const unsigned render_index = ((renderplane >> bit) & 1u) |
                   ((renderplane >> (bit+7u)) & 2u) |
                   ((renderplane >> (bit+14u)) & 4u) |
                   ((renderplane >> (bit+21u)) & 8u);
      const unsigned actual = (unsigned)ppu->objBuffer.data[x+kPpuExtraLeftRight];
      fprintf(stderr,"UR_QA08_WIN_MEDAL_VRAM frame=%d x=%d raster_y=%d "
              "ppu_line=%d slot=%u xoff=%d yoff=%d usedcol=%u usedrow=%u "
              "name=%03x obsel=%02x obsel_bank=%04x tile=%03x wordaddr=%04x "
              "guest_w0=%04x guest_w8=%04x render_w0=%04x render_w8=%04x "
              "guest_idx=%u render_idx=%u actual_obj=%04x actual_cgram=%02x "
              "overlay=%u vram_writes=%u\n",
              snes_frame_counter,x,y-1,y,slot,xoff,yoff,usedcol,usedrow,
              oam1 & 511u,(unsigned)ppu->obsel,bank,tile,wa,
              guest0,guest8,render0,render8,guest_index,render_index,
              actual,actual & 255u,ppu->renderVram ? 1u : 0u,
              (unsigned)ppu->vramWriteCount);
    } else {
      fprintf(stderr,"UR_QA08_WIN_MEDAL_VRAM_REJECT frame=%d slot=%u "
              "xoff=%d yoff=%d size=%u large=%u interlace=%u\n",
              snes_frame_counter,slot,xoff,yoff,
              (unsigned)PPU_objSize(ppu),large,(unsigned)PPU_objInterlace(ppu));
    }
    }
  }
'''


def patch_source(source:str)->str:
    if MARK in source:
        if source.count(MARK)!=1 or source.count(ANCHOR+ADDED)!=1:
            raise ValueError("corrupted/doubled native results VRAM observer")
        return source
    if source.count(ANCHOR)!=1 or prior.MARK not in source:
        raise ValueError("missing unique pinned prior 11-point PPU/OAM pixel observer")
    if "PpuRenderVram" not in source and not ('#include "ppu.h"' in source or '#include "snes.h"' in source):
        raise ValueError("PPU source does not expose actual VRAM renderer")
    return source.replace(ANCHOR,ANCHOR+ADDED,1)


def apply_game(game:Path, *, write:bool=False)->Path:
    game=game.resolve()
    if prior.previous.pinned_revision(game)!=prior.previous.GAME_REV:
        raise ValueError("foreign Uniracers game pin")
    if prior.previous.pinned_revision(game/"snesrecomp")!=prior.previous.CORE_REV:
        raise ValueError("foreign SNESRecomp PPU pin")
    path=game/RELATIVE
    old=path.read_text(encoding="utf-8")
    new=patch_source(old)
    if write and old!=new:
        path.write_text(new,encoding="utf-8")
    return path


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",required=True,type=Path)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try:
        path=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        ap.exit(2,"QA08_WIN_MEDAL_VRAM_REFUSED: "+str(exc)+"\n")
    print("QA08_WIN_MEDAL_VRAM read_only=1 staged="+str(int(a.apply_candidate))+
          " target="+str(path)+" source_PPU_pixels_guest_untouched=1")


if __name__=="__main__":
    main()

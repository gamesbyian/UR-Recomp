#!/usr/bin/env python3
"""Read-only title-scoped Windows SNES $2102/$2103/$2104 port witness.

All writes are observed BEFORE the original PPU port handler. Retains actual
source enum (0 CPU, 1 DMA, 2 HDMA, 3 host raster replay), frame, beam,
OAM low/high address and first/second byte latch. No extra writes, replay,
guest timing, global SNESRecomp, PPU state or raster changes are permitted.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools import baldosa_qa08_native_inidisp_port_trace_patch as old
except ImportError:
    import baldosa_qa08_native_inidisp_port_trace_patch as old

MARK="UR_QA08_NATIVE_OAM_PORT_BEFORE_WRITE"
ANCHOR=old.ANCHOR
TRACE=r"""  /* UR_QA08_NATIVE_OAM_PORT_BEFORE_WRITE: exact native incoming data, not
   * final rendered OAM and not inferred from the PPU's ignored $2104 wlog.
   * The original guest CPU, DMA, HDMA, and replay source labels are kept. */
  if ((adr == 0x02 || adr == 0x03 || adr == 0x04) &&
      getenv("UR_QA08_WINDOWS_OAM_PORT_TRACE") &&
      ((snes_frame_counter >= 4029 && snes_frame_counter <= 4034) ||
       (snes_frame_counter >= 4173 && snes_frame_counter <= 4178)) &&
      g_snes && ppu == g_snes->ppu) {
    fprintf(stderr,
      "UR_QA08_WIN_OAM_PORT frame=%d v=%u h=%u port=%02x val=%02x "
      "src=%u adr=%02x high=%u second=%u latch=%02x "
      "oldlow=%02x oldhigh=%02x\n",
      snes_frame_counter, (unsigned)g_snes->vPos, (unsigned)g_snes->hPos,
      (unsigned)adr, (unsigned)val, (unsigned)g_ppu_wlog_src,
      (unsigned)ppu->oamAdr, (unsigned)(!!ppu->oamInHigh),
      (unsigned)(!!ppu->oamSecondWrite), (unsigned)ppu->oamBuffer,
      (unsigned)ppu->oamaddl, (unsigned)ppu->oamaddh);
  }
"""

def patch_source(src:str)->str:
    if MARK in src:
        if src.count(MARK)!=1 or src.count(TRACE)!=1:
            raise ValueError("partially staged/untrusted OAM source witness")
        return src
    if (src.count(ANCHOR)!=1 or
        src.count(old.TRACE)!=1 or old.MARK not in src or
        "case OAMADDL & 0xff:" not in src or
        "case OAMADDH & 0xff:" not in src or
        "case 0x04: {" not in src or
        "#include <stdio.h>" not in src or
        "#include <stdlib.h>" not in src):
        raise ValueError("unrecognized exact-pinned original PPU port source")
    return src.replace(ANCHOR,ANCHOR+TRACE,1)

def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if old.old.pinned_revision(game)!=old.old.GAME_REV:
        raise ValueError("foreign game source pin")
    if old.old.pinned_revision(game/"snesrecomp")!=old.old.CORE_REV:
        raise ValueError("foreign native SNES PPU pin")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("missing original native generated guest")
    f=game/old.old.RELATIVE
    source=f.read_text(encoding="utf-8")
    updated=patch_source(source)
    if write and updated!=source:
        f.write_text(updated,encoding="utf-8")
    return f

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",type=Path,required=True)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try:
        f=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        ap.exit(2,f"QA08_NATIVE_OAM_PORT_REJECTED: {exc}\n")
    print("QA08_NATIVE_OAM_PORT_OBSERVER",f,
          "staged="+str(int(a.apply_candidate)),
          "title_only=1 no_guest_or_PPU_change=1")

if __name__=="__main__":
    main()

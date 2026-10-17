#!/usr/bin/env python3
"""Read-only current guest $2102/$2103/$2104 data-port DMA source witness."""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV
    )
    from tools.qa08_current_result_cgram_port_patch import (
        ANCHOR, TRACE as CGRAM_TRACE, MARK as CGRAM_MARK
    )
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV
    )
    from qa08_current_result_cgram_port_patch import (
        ANCHOR, TRACE as CGRAM_TRACE, MARK as CGRAM_MARK
    )
RELATIVE=Path("snesrecomp/runner/src/snes/ppu.c")
MARK="UR_QA08_CURRENT_NATIVE_OAM_INPUT"
TRACE=r"""  /* UR_QA08_CURRENT_NATIVE_OAM_INPUT: prior to production PPU port write.
   * Observe, never replace, true CPU/DMA/HDMA/replay source and OAM latch. */
  if ((adr == 0x02 || adr == 0x03 || adr == 0x04) &&
      getenv("UR_QA08_WINDOWS_OAM_PORT_TRACE") &&
      ((snes_frame_counter >= 4029 && snes_frame_counter <= 4034) ||
       (snes_frame_counter >= 4173 && snes_frame_counter <= 4178)) &&
      g_snes && ppu == g_snes->ppu) {
    fprintf(stderr,
      "UR_QA08_WIN_OAM_PORT frame=%d v=%u h=%u port=%02x val=%02x "
      "src=%u adr=%02x high=%u second=%u latch=%02x "
      "oldlow=%02x oldhigh=%02x\n",
      snes_frame_counter,(unsigned)g_snes->vPos,(unsigned)g_snes->hPos,
      (unsigned)adr,(unsigned)val,(unsigned)g_ppu_wlog_src,
      (unsigned)ppu->oamAdr,(unsigned)(!!ppu->oamInHigh),
      (unsigned)(!!ppu->oamSecondWrite),(unsigned)ppu->oamBuffer,
      (unsigned)ppu->oamaddl,(unsigned)ppu->oamaddh);
  }
"""
def patch_source(src:str)->str:
    if MARK in src:
        if src.count(MARK)!=1 or src.count(ANCHOR+TRACE)!=1 or src.count(CGRAM_TRACE)!=1:
            raise ValueError("current native OAM witness partial/drifted")
        return src
    if (src.count(ANCHOR)!=1 or src.count(CGRAM_TRACE)!=1 or
        CGRAM_MARK not in src or "case OAMADDL & 0xff:" not in src or
        "case OAMADDH & 0xff:" not in src or "case 0x04: {" not in src or
        "#include <stdio.h>" not in src or "#include <stdlib.h>" not in src):
        raise ValueError("unqualified current native PPU port hook")
    if "UR_QA08_WIN_OAM_PORT " in src:
        raise ValueError("competing OAM input observer already applied")
    return src.replace(ANCHOR,ANCHOR+TRACE,1)
def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("foreign original guest/framework pin")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("native guest not generated")
    p=game/RELATIVE
    previous=p.read_text(encoding="utf-8")
    current=patch_source(previous)
    if write and previous!=current: p.write_text(current,encoding="utf-8")
    return p
def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",type=Path,required=True)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try: p=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc: ap.exit(2,f"QA08_CURRENT_OAM_DMA_READONLY_REJECT: {exc}\n")
    print("QA08_CURRENT_OAM_DMA_INPUT",p,"read_only="+str(int(a.apply_candidate)))
if __name__=="__main__":main()

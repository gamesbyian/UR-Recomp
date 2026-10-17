#!/usr/bin/env python3
"""QA-08 Uniracers title-scoped original PPU V0 HDMA replay order correction.

At native original Windows 2P guest 3683 PPU line1 is INIDISP 0F, while
the independently executed 2014 Snes9x journal writes 07 at V0, zero at
V111, and 07 at V113, all from channel7 HDMA. The full original/native
CGRAM hash is identical e79794a9. The pinned beam_frame_driver first
primes HDMA, then ppu_rasterApplyLine(0) overwrites the prime with the
earlier CPU vblank INIDISP 0F. Fix the scanout order: replay vblank/line0
register and HDMAEN history before HDMA initialization and V0 transfer.

No guest instruction, clock, gameplay, audio, persistence or Modern changes.
Do not modify upstream shared SNESRecomp: stage only in the exact source-
pinned disposable Windows Uniracers checkout; original 256x224 and
widescreen materializer remain untouched. Candidate until strict original/
native moving 1P and 2P 263-frame CI and player journey receipts pass.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV)
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV)

REL=Path("snesrecomp/runner/src/beam_frame_driver.c")
MARK="UR_QA08_UNIRACERS_V0_RASTER_BEFORE_HDMA"
BEFORE='''  snes_set_hdma_beam_enabled(g_snes, false);
  ppu_rasterRenderBegin(g_ppu);
  dma_initHdma(g_snes->dma);
  /* Hardware's V=0 init also performs each channel's first transfer before
   * any visible pixel. */
  dma_primeHdmaFirstLine(g_snes->dma);
  for (line = 1; line <= 224; line++) {
    uint8_t hdmaen;
    /* A split is written in H-blank after its line is drawn, so the previous
     * line's entries take effect on this one. */
    ppu_rasterApplyLine(g_ppu, line - 1);
    if (ppu_rasterTakeHdmaen(&hdmaen))
      dma_startDma(g_snes->dma, hdmaen, true);
    ppu_runLine(g_ppu, line);'''
AFTER='''  snes_set_hdma_beam_enabled(g_snes, false);
  ppu_rasterRenderBegin(g_ppu);
  /* UR_QA08_UNIRACERS_V0_RASTER_BEFORE_HDMA: CPU writes in previous
   * vblank and V0 must precede V0 HDMA (Snes9x: $2100=0F at V243,
   * overwritten by channel7 $2100=07 at V0 during the finish fade).
   * Prior code replayed the old 0F *after* priming 07, leaving the
   * upper split-screen at incorrect full brightness. Also apply any
   * late $420C enable before initialising HDMA channel descriptors. */
  uint8_t hdmaen;
  ppu_rasterApplyLine(g_ppu, 0);
  if (ppu_rasterTakeHdmaen(&hdmaen))
    dma_startDma(g_snes->dma, hdmaen, true);
  dma_initHdma(g_snes->dma);
  dma_primeHdmaFirstLine(g_snes->dma);
  for (line = 1; line <= 224; line++) {
    /* Subsequent H-blank register writes belong to the following line.
     * V0 was already replayed BEFORE its channel-7 HDMA prime. */
    if (line > 1) {
      ppu_rasterApplyLine(g_ppu, line - 1);
      if (ppu_rasterTakeHdmaen(&hdmaen))
        dma_startDma(g_snes->dma, hdmaen, true);
    }
    ppu_runLine(g_ppu, line);'''
FUNCTION="void snes_beam_frame_driver_draw_ppu_frame(void) {"
NEXT="\nvoid snes_beam_frame_driver_reset(void) {"


def patch_source(raw:str)->str:
    if raw.count(FUNCTION)!=1 or raw.count(NEXT)!=1:
        raise ValueError("unsupported source-pinned beam renderer")
    head,other=raw.split(FUNCTION,1)
    body,tail=other.split(NEXT,1)
    if MARK in raw:
        if raw.count(MARK)!=1 or body.count(AFTER)!=1:
            raise ValueError("partial or competing V0-before-HDMA correction")
        return raw
    if body.count(BEFORE)!=1 or "ppu_rasterRenderEnd(g_ppu);" not in body:
        raise ValueError("beam compositor/HDMA exact call sequence changed")
    return head+FUNCTION+body.replace(BEFORE,AFTER,1)+NEXT+tail


def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV:
        raise ValueError("title source revision changed")
    if pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("cross-title framework revision changed")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("original Uniracers guest source unavailable")
    file=game/REL
    source=file.read_text(encoding="utf-8")
    changed=patch_source(source)
    if write and source!=changed:
        file.write_text(changed,encoding="utf-8")
    return file


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--apply-candidate",action="store_true")
    args=p.parse_args()
    try:
        file=apply_game(args.game,write=args.apply_candidate)
    except (OSError,ValueError) as exc:
        p.exit(2,f"UR_QA08_V0_HDMA_ORDER_REJECTED: {exc}\n")
    print("UR_QA08_V0_HDMA_ORDER",file,
          "candidate_applied="+str(int(args.apply_candidate)),
          "original_256x224=1 guest_clocks_unchanged=1 release_gate=0")


if __name__=="__main__":
    main()

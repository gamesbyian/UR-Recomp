#!/usr/bin/env python3
"""Opt-in original-mode Windows $2100 writer timing, without any state edits.

Stage only after the existing CGRAM source observer in a disposable exact-pin
Uniracers Windows native build. Observe actual writes to the PPU $2100
INIDISP data port at frames 4008..4024 (blackout ramp). Label CPU, HDMA,
DMA and raster replay by their original source enum. Do not re-time guest
instructions, insert forced blank, alter PPU render, or modify Modern.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools import baldosa_qa08_native_cgram_port_chronology_patch as old
except ImportError:
    import baldosa_qa08_native_cgram_port_chronology_patch as old

MARK="UR_QA08_NATIVE_INIDISP_PORT_TIMELINE"
ANCHOR=old.ANCHOR
TRACE=r"""  /* UR_QA08_NATIVE_INIDISP_PORT_TIMELINE: exact title, opt-in CPU/PPU
   * write witness during the source-blackout 2P result brightness ramp.
   * This logs the incoming write before any production port state changes;
   * replay-source enum is preserved and must NOT be called guest CPU. */
  if (adr == 0x00 &&
      getenv("UR_QA08_WINDOWS_INIDISP_PORT_TRACE") &&
      snes_frame_counter >= 4008 && snes_frame_counter <= 4024 &&
      g_snes && ppu == g_snes->ppu) {
    fprintf(stderr,
      "UR_QA08_WIN_INIDISP_WRITE frame=%d v=%u h=%u "
      "val=%02x old=%02x src=%u\n",
      snes_frame_counter,(unsigned)g_snes->vPos,
      (unsigned)g_snes->hPos,(unsigned)val,
      (unsigned)ppu->inidisp,(unsigned)g_ppu_wlog_src);
  }
"""

def patch_source(source:str)->str:
    if MARK in source:
        if (source.count(MARK)!=1 or source.count(TRACE)!=1 or
            source.count(old.TRACE)!=1):
            raise ValueError("native $2100 write observer partial/tampered")
        return source
    if (source.count(ANCHOR)!=1 or source.count(old.TRACE)!=1 or
        old.MARK not in source or "case INIDISP & 0xff:" not in source):
        raise ValueError("native PPU port handler missing pinned CGRAM observer")
    return source.replace(ANCHOR,ANCHOR+TRACE,1)

def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if old.pinned_revision(game)!=old.GAME_REV:
        raise ValueError("unrecognized Uniracers guest revision")
    if old.pinned_revision(game/"snesrecomp")!=old.CORE_REV:
        raise ValueError("unrecognized native PPU framework revision")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("native Uniracers AOT guest missing")
    path=game/old.RELATIVE
    old_content=path.read_text(encoding="utf-8")
    candidate=patch_source(old_content)
    if write and candidate!=old_content:
        path.write_text(candidate,encoding="utf-8")
    return path

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--apply-candidate",action="store_true")
    a=p.parse_args()
    try:
        path=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        p.exit(2,f"QA08_NATIVE_INIDISP_WRITER_REJECTED: {exc}\n")
    print(f"QA08_NATIVE_INIDISP_READONLY source={path} staged={int(a.apply_candidate)} release=0")

if __name__=="__main__":
    main()

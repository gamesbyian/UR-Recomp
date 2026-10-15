#!/usr/bin/env python3
"""Read-only source-qualified Win32 Uniracers HDMA channel7 first-line probe.

The actual Windows guest=3683 upper screen is brightness 15, while original
Snes9x's V0 $2100 write is 07. Inspect descriptor and WRAM 2064-206B on the
real native HDMA prime. No modifications to registers, RAM, CPU/APU, game,
Modern UI, or output pixels. This is not a correction or release acceptance.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV,MARK as CANDIDATE_MARK)
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV,MARK as CANDIDATE_MARK)

REL=Path("snesrecomp/runner/src/snes/dma.c")
MARK="UR_QA08_NATIVE_CHANNEL7_FIRSTLINE_WITNESS"
START="void dma_primeHdmaFirstLine(Dma* dma) {\n  for (int i = 0; i < 8; i++) {\n    DmaChannel* ch = &dma->channel[i];\n"
END="\nvoid dma_doHdma(Dma* dma) {"
BEFORE="    if (!ch->hdmaActive || ch->terminated || !ch->doTransfer) continue;"
AFTER="    ch->repCount--;\n    ch->doTransfer = (ch->repCount & 0x80) != 0;"
PRE=r'''    /* UR_QA08_NATIVE_CHANNEL7_FIRSTLINE_WITNESS: inspect real WRAM only. */
    if (i == 7 && getenv("UR_QA08_WINDOWS_HDMA_FIRSTLINE_TRACE") &&
        snes_frame_counter >= 3620 && snes_frame_counter <= 3690) {
      const uint8_t *mem = dma->snes->ram;
      fprintf(stderr,
          "UR_QA08_WIN_HDMA7 frame=%d phase=pre enable=%u terminated=%u "
          "transfer=%u aBank=%02x aAdr=%04x tableAdr=%04x rep=%02x "
          "bAdr=%02x bytes=%02x%02x%02x%02x%02x%02x%02x%02x inidisp=%02x\n",
          snes_frame_counter, (unsigned)ch->hdmaActive,
          (unsigned)ch->terminated,(unsigned)ch->doTransfer,
          (unsigned)ch->aBank,(unsigned)ch->aAdr,
          (unsigned)ch->tableAdr,(unsigned)ch->repCount,
          (unsigned)ch->bAdr,
          (unsigned)mem[0x2064],(unsigned)mem[0x2065],
          (unsigned)mem[0x2066],(unsigned)mem[0x2067],
          (unsigned)mem[0x2068],(unsigned)mem[0x2069],
          (unsigned)mem[0x206a],(unsigned)mem[0x206b],
          (unsigned)dma->snes->ppu->inidisp);
    }
'''
POST=r'''    if (i == 7 && getenv("UR_QA08_WINDOWS_HDMA_FIRSTLINE_TRACE") &&
        snes_frame_counter >= 3620 && snes_frame_counter <= 3690)
      fprintf(stderr,
          "UR_QA08_WIN_HDMA7 frame=%d phase=post enable=%u terminated=%u "
          "transfer=%u tableAdr=%04x rep=%02x inidisp=%02x\n",
          snes_frame_counter, (unsigned)ch->hdmaActive,
          (unsigned)ch->terminated,(unsigned)ch->doTransfer,
          (unsigned)ch->tableAdr,(unsigned)ch->repCount,
          (unsigned)dma->snes->ppu->inidisp);
'''


def patch_source(raw:str)->str:
    if CANDIDATE_MARK not in raw or raw.count(START)!=1 or raw.count(END)!=1:
        raise ValueError("not the accepted Uniracers firstline source candidate")
    head,rest=raw.split(START,1)
    body,tail=rest.split(END,1)
    if MARK in raw:
        if raw.count(MARK)!=1 or body.count(PRE)!=1 or body.count(POST)!=1:
            raise ValueError("incomplete or altered existing witness")
        return raw
    if body.count(BEFORE)!=1 or body.count(AFTER)!=1:
        raise ValueError("source firstline semantics or descriptor changed")
    body=body.replace(BEFORE,PRE+BEFORE,1).replace(AFTER,POST+AFTER,1)
    return head+START+body+END+tail


def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("game/framework source pin drift")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("missing original generated game")
    file=game/REL
    before=file.read_text(encoding="utf-8")
    after=patch_source(before)
    if write and before!=after:
        file.write_text(after,encoding="utf-8")
    return file


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",type=Path,required=True)
    ap.add_argument("--apply-candidate",action="store_true")
    args=ap.parse_args()
    try:
        file=apply_game(args.game,write=args.apply_candidate)
    except (ValueError,OSError) as exc:
        ap.exit(2,f"UR_QA08_NATIVE_HDMA7_PROBE_REJECTED {exc}\n")
    print("UR_QA08_NATIVE_HDMA7_WITNESS",file,
          "applied="+str(int(args.apply_candidate)),
          "guest_state_untouched=1 release=0")


if __name__=="__main__":
    main()

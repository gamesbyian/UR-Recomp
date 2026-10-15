#!/usr/bin/env python3
"""QA08 experimental full-field CGRAM source snapshot for Windows Uniracers.

The pinned PPU raster journal captures *registers*, but explicitly skips the
$2121/$2122 CGRAM data-port. Reconstructing an earlier, completed field with
end-of-current-guest-frame live CGRAM can show a newer checkerboard palette
one field too soon (source 2P 5184: original FNV e8cdbe60 vs Win 898ece20).

Only for an exact pinned disposable Uniracers title build. Capture the
completed field's complete CGRAM at V225 *before* subsequent CPU vblank
uploads, present that field using that CGRAM, and restore LIVE guest CGRAM
and CGRAM address/write-latch state after the render. No edits to guest code,
CPU/APU/HDMA timing, user saves, Modern, source geometry or widescreen.

This is an isolated EXPERIMENT, NOT a proven shipping fix. It is only
admissible if actual original Snes9x vs Windows 261-frame 1P and 263-frame
2P source comparisons exhibit improvement with zero regressions, identical
guest CRC, including moving race, fades, split/window and result transitions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV)
    from tools.baldosa_uniracers_brightness_pixel_lut_patch import MARK as BRT_MARK
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV)
    from baldosa_uniracers_brightness_pixel_lut_patch import MARK as BRT_MARK

REL=Path("snesrecomp/runner/src/snes/ppu.c")
MARK="UR_QA08_EXPERIMENT_COMPLETED_FIELD_CGRAM_LATCH"
PATCHES=(
("""  uint8_t hdmaen;
  int count;
  uint32_t dropped;
  PpuRasterEntry e[PPU_RASTER_MAX];
} PpuRasterField;""",
"""  uint8_t hdmaen;
  /* UR_QA08_EXPERIMENT_COMPLETED_FIELD_CGRAM_LATCH: exact palette as of
   * V225 field completion, not the next field's CPU vblank uploads. */
  uint16_t cgram_complete[256];
  int count;
  uint32_t dropped;
  PpuRasterEntry e[PPU_RASTER_MAX];
} PpuRasterField;"""),
("""static struct {
  uint8_t oamAdr, oamInHigh, oamSecondWrite, oamBuffer;
} s_raster_port;""",
"""static struct {
  uint8_t oamAdr, oamInHigh, oamSecondWrite, oamBuffer;
} s_raster_port;
static uint16_t s_raster_live_guest_cgram[256];
static uint8_t s_raster_live_guest_cgramPointer;
static bool s_raster_live_guest_cgramSecondWrite;
static uint8_t s_raster_live_guest_cgramBuffer;"""),
("""  f->hdmaen = g_snesrecomp_last_hdmaen;
  f->count = 0;""",
"""  f->hdmaen = g_snesrecomp_last_hdmaen;
  memcpy(f->cgram_complete, ppu->cgram, sizeof(ppu->cgram));
  f->count = 0;"""),
("""  s_raster_rendering = 0;
  s_raster_cur ^= 1;
  s_raster_have_completed = 1;
  raster_snapshot(&s_field[s_raster_cur], ppu);""",
"""  s_raster_rendering = 0;
  /* This field has just reached V225; preserve its final CGRAM BEFORE any
   * next-field Vblank CPU palette upload can affect the scanned image. */
  memcpy(s_field[s_raster_cur].cgram_complete, ppu->cgram,
         sizeof(ppu->cgram));
  s_raster_cur ^= 1;
  s_raster_have_completed = 1;
  raster_snapshot(&s_field[s_raster_cur], ppu);"""),
("""  s_raster_port.oamBuffer = ppu->oamBuffer;
  memcpy(&ppu->inidisp, f->regs, PPU_SAVESTATE_REGS_SIZE);""",
"""  s_raster_port.oamBuffer = ppu->oamBuffer;
  /* Present prior completed field without writing to the LIVE guest's
   * palette or CGRAM address/write-twice latch. Save and restore all of it. */
  memcpy(s_raster_live_guest_cgram, ppu->cgram, sizeof(ppu->cgram));
  s_raster_live_guest_cgramPointer = ppu->cgramPointer;
  s_raster_live_guest_cgramSecondWrite = ppu->cgramSecondWrite;
  s_raster_live_guest_cgramBuffer = ppu->cgramBuffer;
  memcpy(ppu->cgram, f->cgram_complete, sizeof(ppu->cgram));
  memcpy(&ppu->inidisp, f->regs, PPU_SAVESTATE_REGS_SIZE);"""),
("""  ppu->oamBuffer = s_raster_port.oamBuffer;
}

/* Snapshot of the journal""",
"""  ppu->oamBuffer = s_raster_port.oamBuffer;
  memcpy(ppu->cgram, s_raster_live_guest_cgram, sizeof(ppu->cgram));
  ppu->cgramPointer = s_raster_live_guest_cgramPointer;
  ppu->cgramSecondWrite = s_raster_live_guest_cgramSecondWrite;
  ppu->cgramBuffer = s_raster_live_guest_cgramBuffer;
}

/* Snapshot of the journal"""),
)


def patch_source(source:str)->str:
    if BRT_MARK not in source:
        raise ValueError("expected source-brightness corrected Uniracers PPU first")
    # Validate entire source window BEFORE changing any of it.
    if MARK in source:
        if source.count(MARK)!=1 or any(
            source.count(updated)!=1 for _,updated in PATCHES):
            raise ValueError("partial or competing CGRAM field snapshot experiment")
        recovered=source
        for original,changed in reversed(PATCHES):
            recovered=recovered.replace(changed,original,1)
        if patch_source(recovered)!=source:
            raise ValueError("existing CGRAM field snapshot differs")
        return source
    if any(source.count(original)!=1 for original,_ in PATCHES):
        raise ValueError("pinned original raster CGRAM state or ownership drift")
    changed=source
    for original,updated in PATCHES:
        changed=changed.replace(original,updated,1)
    return changed


def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV:
        raise ValueError("unrecognized source game")
    if pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("unrecognized SNESRecomp framework revision")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("source-generated guest absent")
    path=game/REL
    before=path.read_text(encoding="utf-8")
    after=patch_source(before)
    if write and before!=after:
        path.write_text(after,encoding="utf-8")
    return path


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--apply-experiment",action="store_true")
    a=p.parse_args()
    try:
        path=apply_game(a.game,write=a.apply_experiment)
    except (ValueError,OSError) as err:
        p.exit(2,f"UR_QA08_CGRAM_FIELD_LATCH_EXPERIMENT_REJECTED {err}\n")
    print("UR_QA08_CGRAM_COMPLETED_FIELD_EXPERIMENT",path,
          "applied="+str(int(a.apply_experiment)),
          "guest_cgram_restored=1 exact_original_parity=NOT_YET_PROVEN")


if __name__=="__main__":
    main()

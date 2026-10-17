#!/usr/bin/env python3
"""Read-only title-scoped real Windows RF017 $2100 + output scanline witness.

Observes source PPU input-port writes, CPU/DMA/HDMA/replay provenance,
and effective raster INIDISP without inventing any guest clock correction.
Staged only on pinned disposable Baldosa Windows game+core before PE build.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV
    )
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV
    )

PORT_PATH=Path("snesrecomp/runner/src/snes/ppu.c")
RASTER_PATH=Path("snesrecomp/runner/src/snes/ppu_legacy.c")
PORT_ANCHOR="void ppu_write(Ppu* ppu, uint8_t adr, uint8_t val) {\n  ppu_wlog_note(adr, val);\n"
RASTER_ANCHOR="void ppu_draw_whole_line_legacy(Ppu *ppu, int line) {\n  // actual line\n"
PIXEL_ANCHOR="  pixelBuffer[3] = 0;\n"
RASTER_HEADER="#include <stdbool.h>\n"
PORT_MARK="UR_QA08_CURRENT_BLACKOUT_WRITE_PORT"
RASTER_MARK="UR_QA08_CURRENT_BLACKOUT_RASTER"
PIXEL_MARK="UR_QA08_CURRENT_PIXEL_PROBE_MARKER"
PORT_TRACE=r"""  /* UR_QA08_CURRENT_BLACKOUT_WRITE_PORT: original $2100 write INPUT,
   * not a speculative host frame re-registration or a fabricated value. */
  if (adr == 0x00 && getenv("UR_QA08_CURRENT_BLACKOUT_TRACE") &&
      snes_frame_counter >= 4008 && snes_frame_counter <= 4024 &&
      g_snes && ppu == g_snes->ppu) {
    fprintf(stderr,
      "UR_QA08_CURRENT_BLACKOUT_PORT frame=%d v=%u h=%u "
      "val=%02x old=%02x src=%u\n",
      snes_frame_counter,(unsigned)g_snes->vPos,(unsigned)g_snes->hPos,
      (unsigned)val,(unsigned)ppu->inidisp,(unsigned)g_ppu_wlog_src);
  }
"""
RASTER_TRACE=r"""  /* UR_QA08_CURRENT_BLACKOUT_RASTER: actual legacy-line entry,
   * retained as source state; never an alternate renderer. */
  if ((line == 1 || line == 112 || line == 114) &&
      (snes_frame_counter == 4015 || snes_frame_counter == 4016 ||
       snes_frame_counter == 4017 || snes_frame_counter == 4022) &&
      getenv("UR_QA08_CURRENT_BLACKOUT_TRACE")) {
    fprintf(stderr,
      "UR_QA08_CURRENT_BLACKOUT_LINE frame=%d line=%d inidisp=%02x "
      "brightness=%u forced_blank=%u cgadsub=%02x\n",
      snes_frame_counter,line,(unsigned)ppu->inidisp,
      (unsigned)PPU_brightness(ppu),(unsigned)(!!PPU_forcedBlank(ppu)),
      (unsigned)ppu->cgadsub);
  }
"""
PIXEL_TRACE=r"""  /* UR_QA08_CURRENT_PIXEL_PROBE_MARKER: source pixel after original PPU
   * resolver. Input y is one-based raster line; report output y-1. */
  if (snes_frame_counter == 4016 &&
      ((x == 32 && y == 33) || (x == 128 && y == 113) ||
       (x == 220 && y == 201)) &&
      getenv("UR_QA08_CURRENT_BLACKOUT_TRACE")) {
    fprintf(stderr,
      "UR_QA08_CURRENT_BLACKOUT_PIXEL frame=%d x=%d y=%d "
      "inidisp=%02x r=%u g=%u b=%u\n",
      snes_frame_counter,x,y-1,(unsigned)ppu->inidisp,
      (unsigned)pixelBuffer[2],(unsigned)pixelBuffer[1],
      (unsigned)pixelBuffer[0]);
  }
"""
def patch_port(src:str)->str:
    if PORT_MARK in src:
        if src.count(PORT_ANCHOR+PORT_TRACE)!=1 or src.count(PORT_MARK)!=1:
            raise ValueError("partial/tampered current RF017 PPU write observer")
        return src
    # A stripped sentinel must never bypass the no-double-patch contract.
    # An existing port-output line is sufficient proof of partial staging.
    if "UR_QA08_CURRENT_BLACKOUT_PORT " in src:
        raise ValueError("instrumented port write has missing/tampered marker")
    if src.count(PORT_ANCHOR)!=1 or "#include <stdio.h>" not in src or "#include <stdlib.h>" not in src:
        raise ValueError("pinned original port write/headers changed")
    return src.replace(PORT_ANCHOR,PORT_ANCHOR+PORT_TRACE,1)

def patch_raster(src:str)->str:
    if RASTER_MARK in src or PIXEL_MARK in src:
        if (src.count(RASTER_ANCHOR+RASTER_TRACE)!=1 or
            src.count(PIXEL_ANCHOR+PIXEL_TRACE)!=1 or
            src.count(RASTER_MARK)!=1 or src.count(PIXEL_MARK)!=1):
            raise ValueError("partial/tampered current PPU register/pixel observer")
        return src
    if (src.count(RASTER_ANCHOR)!=1 or src.count(PIXEL_ANCHOR)!=1 or
        src.count(RASTER_HEADER)!=1 or
        "#include <stdio.h>" in src or "#include <stdlib.h>" in src):
        raise ValueError("pinned current original raster source anchors changed")
    return (src.replace(RASTER_HEADER,RASTER_HEADER+"#include <stdio.h>\n#include <stdlib.h>\n",1)
          .replace(RASTER_ANCHOR,RASTER_ANCHOR+RASTER_TRACE,1)
          .replace(PIXEL_ANCHOR,PIXEL_ANCHOR+PIXEL_TRACE,1))

def apply_game(game:Path, *, write:bool=False)->list[Path]:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("game/core source revisions are not the approved pins")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("actual source regenerated RF017 guest missing")
    planned=[]
    for name,transform in ((PORT_PATH,patch_port),(RASTER_PATH,patch_raster)):
        path=game/name
        before=path.read_text(encoding="utf-8")
        after=transform(before)
        planned.append((path,before,after))
    if write:
        for path,before,after in planned:
            if before!=after:path.write_text(after,encoding="utf-8")
    return [x[0] for x in planned]

def main()->None:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--game",required=True,type=Path)
    a.add_argument("--apply-candidate",action="store_true")
    args=a.parse_args()
    try: paths=apply_game(args.game,write=args.apply_candidate)
    except (OSError,ValueError) as exc:
        a.exit(2,f"QA08_BLACKOUT_READONLY_REJECT: {exc}\n")
    print("QA08_BLACKOUT_READONLY",*[str(p) for p in paths],
          "applied="+str(int(args.apply_candidate)),"guest_PPU_presentation_modified=0")
if __name__=="__main__":main()

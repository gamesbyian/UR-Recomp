#!/usr/bin/env python3
"""Read-only current RF-017/firstline/V0 effective native PPU owners.

Diagnostics only; never merge into the release renderer. Source input is
game/core pinned and captures existing resolver outputs without re-evaluation.
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

RELATIVE=Path("snesrecomp/runner/src/snes/ppu_legacy.c")
MARK="UR_QA08_NATIVE_EFFECTIVE_PIXEL_OWNER"
INTRO="static void ppu_render_pixel(Ppu *ppu, int x, int y) {\n"
MAIN="    int mainLayer = ppu_resolve_pixel(ppu, x, y, false, &r, &g, &b);\n"
WINDOW="    bool colorWindowState = ppu_window_contains(ppu, 5, x);\n"
MATH_END=("      (PPU_preventMathMode(ppu) == 1 && !colorWindowState)\n"
          "      );\n")
SUB="      secondLayer = ppu_resolve_pixel(ppu, x, y, true, &r2, &g2, &b2);\n"
END="  pixelBuffer[3] = 0;\n"
DECL=r"""  /* UR_QA08_NATIVE_EFFECTIVE_PIXEL_OWNER: existing pixel, no new resolver. */
  int qa08_main_layer = -1, qa08_sub_layer = -1, qa08_math = -1;
  int qa08_window = -1, qa08_main_r = -1, qa08_main_g = -1;
  int qa08_main_b = -1, qa08_sub_r = -1, qa08_sub_g = -1;
  int qa08_sub_b = -1;
"""
CAPTURE_MAIN=r"""    qa08_main_layer = mainLayer;
    qa08_main_r = r; qa08_main_g = g; qa08_main_b = b;
"""
CAPTURE_WINDOW="    qa08_window = (int)colorWindowState;\n"
CAPTURE_MATH="    qa08_math = (int)mathEnabled;\n"
CAPTURE_SUB=r"""      qa08_sub_layer = secondLayer;
      qa08_sub_r = r2; qa08_sub_g = g2; qa08_sub_b = b2;
"""
TRACE=r"""  /* Original logical x and output y. This reads the already composed pixel
   * and the effective scanline OBJ buffer; it never re-renders any layer.
   * 2P source-qualified witness is opt-in to one existing full result route.
   * Every selected point is independently wrong in archived original/native
   * Snes9x/Windows full 256x224 RGB5 source frames. */
  if ((snes_frame_counter == 4032 || snes_frame_counter == 4048 ||
        snes_frame_counter == 4064 || snes_frame_counter == 4080 ||
        snes_frame_counter == 4176) &&
      ((x == 207 && y == 92) || (x == 205 && (y == 116 || y == 140)) ||
       (x == 225 && (y == 97 || y == 121))) &&
      getenv("UR_QA08_WINDOWS_PIXEL_OWNER_TRACE")) {
    const unsigned obj = (unsigned)ppu->objBuffer.data[x + kPpuExtraLeftRight];
    const unsigned objpal = obj & 255u;
    const unsigned objcolour = (unsigned)PpuPixelColor(
        ppu, (uint16_t)obj, (size_t)(x + kPpuExtraLeftRight));
    fprintf(stderr,
      "UR_QA08_WIN_PIXEL_OWNER frame=%d x=%d raster_y=%d ppu_line=%d "
      "main=%d sub=%d math=%d window=%d premain=%d,%d,%d "
      "presub=%d,%d,%d postmath=%d,%d,%d final=%u,%u,%u "
      "obj=%04x obj_cgram_index=%02x obj_word=%04x "
      "inidisp=%02x cgadsub=%02x cgwsel=%02x fixed=%04x "
      "tm=%02x ts=%02x obsel=%02x\n",
      snes_frame_counter,x,y-1,y,qa08_main_layer,qa08_sub_layer,
      qa08_math,qa08_window,qa08_main_r,qa08_main_g,qa08_main_b,
      qa08_sub_r,qa08_sub_g,qa08_sub_b,r,g,b,
      (unsigned)pixelBuffer[2],(unsigned)pixelBuffer[1],
      (unsigned)pixelBuffer[0],obj,objpal,objcolour,
      (unsigned)ppu->inidisp,(unsigned)ppu->cgadsub,(unsigned)ppu->cgwsel,
      (unsigned)ppu->fixedColor,(unsigned)ppu->screenEnabled[0],
      (unsigned)ppu->screenEnabled[1],(unsigned)ppu->obsel);
    {
      static const unsigned candidates[] = {96,97,98,99,112,113,114};
      for (unsigned j = 0; j < 7; ++j) {
        const unsigned slot = candidates[j];
        const unsigned xy = (unsigned)ppu->oam[slot * 2];
        const unsigned tileattr = (unsigned)ppu->oam[slot * 2 + 1];
        const unsigned high = ((unsigned)ppu->highOam[slot >> 2] >>
                              ((slot & 3) * 2)) & 3u;
        fprintf(stderr,
          "UR_QA08_WIN_OAM_LINE frame=%d x=%d ppu_line=%d "
          "slot=%u xy=%04x attrs=%04x high=%u\n",
          snes_frame_counter,x,y,slot,xy,tileattr,high);
      }
    }
  }

"""


def patch_source(src: str) -> str:
    parts=((INTRO,INTRO+DECL),(MAIN,MAIN+CAPTURE_MAIN),
           (WINDOW,WINDOW+CAPTURE_WINDOW),(MATH_END,MATH_END+CAPTURE_MATH),
           (SUB,SUB+CAPTURE_SUB),(END,END+TRACE))
    header='#include <stdbool.h>\n'
    if MARK in src:
        if any(src.count(b)!=1 for _,b in parts):
            raise ValueError("partial or modified read-only pixel observer")
        if src.count("#include <stdio.h>") != 1 or src.count("#include <stdlib.h>") != 1:
            raise ValueError("observer headers missing")
        return src
    if any(src.count(a)!=1 for a,_ in parts) or src.count(header)!=1:
        raise ValueError("pinned native pixel renderer anchor differs")
    if "#include <stdio.h>" in src or "#include <stdlib.h>" in src:
        raise ValueError("unexpected pre-existing PPU instrumentation")
    src=src.replace(header,header+"#include <stdio.h>\n#include <stdlib.h>\n",1)
    for a,b in parts:
        src=src.replace(a,b,1)
    return src

def apply_game(game: Path, *, write: bool = False) -> Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("game/core source revision changed")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("generated USA game absent")
    path=game/RELATIVE
    before=path.read_text(encoding="utf-8")
    after=patch_source(before)
    if write and after!=before: path.write_text(after,encoding="utf-8")
    return path

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",type=Path,required=True)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try: path=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        ap.exit(2,f"QA08_CURRENT_PIXEL_READONLY_REJECT: {exc}\n")
    print("QA08_CURRENT_PIXEL_READONLY",path,"staged="+str(int(a.apply_candidate)))

if __name__=="__main__": main()

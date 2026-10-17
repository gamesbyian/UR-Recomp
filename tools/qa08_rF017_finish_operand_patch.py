#!/usr/bin/env python3
"""Read-only source-bound RF017 Original 2P actual native finish operand owner.

No color transformation, sprite/OAM edit, clock shift or result composite fix.
Title/game/core SHA fail closed; exact decoded PPU source anchors required.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV
    )
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision,GAME_REV,CORE_REV
    )
RELATIVE=Path("snesrecomp/runner/src/snes/ppu_legacy.c")
HEADER="#include <stdbool.h>\n"
ENTRY="static void ppu_render_pixel(Ppu *ppu, int x, int y) {\n"
MAIN="    int mainLayer = ppu_resolve_pixel(ppu, x, y, false, &r, &g, &b);\n"
WINDOW="    bool colorWindowState = ppu_window_contains(ppu, 5, x);\n"
MATH_END=("      (PPU_preventMathMode(ppu) == 1 && !colorWindowState)\n"
          "      );\n")
SUB="      secondLayer = ppu_resolve_pixel(ppu, x, y, true, &r2, &g2, &b2);\n"
BEFORE_END="  pixelBuffer[3] = 0;\n"
MARK="UR_QA08_RF017_FINISH_OPERAND_READONLY"
DECL=r"""  /* UR_QA08_RF017_FINISH_OPERAND_READONLY: read only already resolved state. */
  int qa08_main=-1,qa08_sub=-1,qa08_math=-1,qa08_window=-1;
  int qa08_mr=-1,qa08_mg=-1,qa08_mb=-1;
  int qa08_sr=-1,qa08_sg=-1,qa08_sb=-1;
"""
GETMAIN="    qa08_main=mainLayer;qa08_mr=r;qa08_mg=g;qa08_mb=b;\n"
GETWINDOW="    qa08_window=(int)colorWindowState;\n"
GETMATH="    qa08_math=(int)mathEnabled;\n"
GETSUB="      qa08_sub=secondLayer;qa08_sr=r2;qa08_sg=g2;qa08_sb=b2;\n"
TRACE=r"""  /* In real produced pixelBuffer after PPU math and brightness only;
   * one source-qualified 5484-frame route; 2 exact normal-frame controls. */
  if (getenv("UR_QA08_RF017_FINISH_OPERAND_TRACE") &&
      ((snes_frame_counter == 3680 && y == 1 &&
         (x == 92 || x == 93 || x == 96 || x == 97)) ||
       ((snes_frame_counter == 3792 || snes_frame_counter == 3872) &&
         x == 121 && y == 166) ||
       (snes_frame_counter == 1856 && y == 1 &&
         (x == 96 || x == 97)))) {
    fprintf(stderr,
       "UR_QA08_FINISH_OPERAND frame=%d x=%d y=%d "
       "main=%d sub=%d math=%d window=%d "
       "pre_main=%d,%d,%d pre_sub=%d,%d,%d "
       "post_math=%d,%d,%d final=%u,%u,%u "
       "inidisp=%02x cgadsub=%02x cgwsel=%02x tm=%02x ts=%02x\n",
       snes_frame_counter,x,y-1,
       qa08_main,qa08_sub,qa08_math,qa08_window,
       qa08_mr,qa08_mg,qa08_mb,qa08_sr,qa08_sg,qa08_sb,
       r,g,b,
       (unsigned)pixelBuffer[2],(unsigned)pixelBuffer[1],
       (unsigned)pixelBuffer[0],
       (unsigned)ppu->inidisp,(unsigned)ppu->cgadsub,
       (unsigned)ppu->cgwsel,(unsigned)ppu->screenEnabled[0],
       (unsigned)ppu->screenEnabled[1]);
  }
"""
PARTS=((ENTRY,ENTRY+DECL),(MAIN,MAIN+GETMAIN),
       (WINDOW,WINDOW+GETWINDOW),(MATH_END,MATH_END+GETMATH),
       (SUB,SUB+GETSUB),(BEFORE_END,BEFORE_END+TRACE))

def patch(src:str)->str:
    if MARK in src:
        if any(src.count(new)!=1 for old,new in PARTS) or src.count(MARK)!=1:
            raise ValueError("partial/altered RF017 finish operand observer")
        return src
    if ("UR_QA08_FINISH_OPERAND frame=" in src or
        any(src.count(old)!=1 for old,new in PARTS) or
        src.count(HEADER)!=1 or
        "#include <stdio.h>" in src or "#include <stdlib.h>" in src):
        raise ValueError("pinned original PPU finish observer source no longer exact")
    result=src.replace(HEADER,HEADER+"#include <stdio.h>\n#include <stdlib.h>\n",1)
    for old,new in PARTS:
        result=result.replace(old,new,1)
    return result

def stage(game:Path,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("foreign game/SNESRecomp source revision")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("RF017 generated source missing")
    target=game/RELATIVE
    before=target.read_text(encoding="utf-8")
    result=patch(before)
    if write and result!=before:target.write_text(result,encoding="utf-8")
    return target
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-candidate",action="store_true")
    a=p.parse_args()
    try:path=stage(a.game,write=a.apply_candidate)
    except (ValueError,OSError) as exc:p.exit(2,f"QA08_FINISH_OPERAND_REJECT: {exc}\n")
    print("QA08_FINISH_OPERAND_ONLY",path,"staged="+str(int(a.apply_candidate)),
          "guest_PPU_unchanged=1 release=0")
if __name__=="__main__":main()

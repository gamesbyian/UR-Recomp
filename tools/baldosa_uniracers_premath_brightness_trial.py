#!/usr/bin/env python3
"""Strict pinned experimental Uniracers-only Original PPU pre-math brightness.

Disposable A/B trial only. 2014 Snes9x resolves brightness-quantized
source colours BEFORE colour math; Baldosa legacy resolves math first and
applies master brightness after 5-to-8 bit expansion. This models the
observed eight true native PPU operands, not a frame-position palette LUT.

No guest/CPU/APU, Original raster timing, Modern, remastered asset, or
widescreen changes. Must remain DRAFT until source-qualified 1P/2P whole
picture regression + independent visual QA; never patch SNESRecomp upstream.
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

SOURCE=Path("snesrecomp/runner/src/snes/ppu_legacy.c")
MARK="UR_QA08_TITLE_PREMATH_FIVEBIT_BRIGHTNESS_TRIAL"
START="static void ppu_render_pixel(Ppu *ppu, int x, int y) {\n"
AFTER_SUB="    // TODO: subscreen pixels can be clipped to black as well\n"
OUTPUT=(
"  pixelBuffer[0] = ((b << 3) | (b >> 2)) * PPU_brightness(ppu) / 15;\n"
"  pixelBuffer[1] = ((g << 3) | (g >> 2)) * PPU_brightness(ppu) / 15;\n"
"  pixelBuffer[2] = ((r << 3) | (r >> 2)) * PPU_brightness(ppu) / 15;\n"
)
REPLACEMENT=(
"  /* Brightness already quantized before colour-math operands. Original\n"
"   * SNES5 source stage; do not reapply it after full add/sub. */\n"
"  pixelBuffer[0] = (b << 3) | (b >> 2);\n"
"  pixelBuffer[1] = (g << 3) | (g >> 2);\n"
"  pixelBuffer[2] = (r << 3) | (r >> 2);\n"
)
INTRO=(
"/* "+MARK+": exact 5-bit master brightness on colour operands.\n"
" * Only this opt-in Uniracers Original QA diagnostic, not common core. */\n"
"static int ur_qa08_premath_brightness5(int value, int brightness) {\n"
"  return (value * brightness + 7) / 15;\n"
"}\n"
)
BRIGHTEN=(
"    /* "+MARK+": source-colour quantization before full/half add.\n"
"     * Existing layer winner, window, operand selection, and mode untouched. */\n"
"    const int ur_qa08_br = PPU_brightness(ppu);\n"
"    r = ur_qa08_premath_brightness5(r,ur_qa08_br);\n"
"    g = ur_qa08_premath_brightness5(g,ur_qa08_br);\n"
"    b = ur_qa08_premath_brightness5(b,ur_qa08_br);\n"
"    r2 = ur_qa08_premath_brightness5(r2,ur_qa08_br);\n"
"    g2 = ur_qa08_premath_brightness5(g2,ur_qa08_br);\n"
"    b2 = ur_qa08_premath_brightness5(b2,ur_qa08_br);\n"
)
FIXED={
 "PPU_fixedColorR(ppu)":"ur_qa08_premath_brightness5(PPU_fixedColorR(ppu),ur_qa08_br)",
 "PPU_fixedColorG(ppu)":"ur_qa08_premath_brightness5(PPU_fixedColorG(ppu),ur_qa08_br)",
 "PPU_fixedColorB(ppu)":"ur_qa08_premath_brightness5(PPU_fixedColorB(ppu),ur_qa08_br)",
}
def patched(source:str)->str:
    if MARK in source:
        if (source.count(MARK)!=2 or source.count(INTRO)!=1 or
            source.count(BRIGHTEN)!=1 or source.count(REPLACEMENT)!=1 or
            source.count(OUTPUT)!=0):
            raise ValueError("partial or altered title pre-math candidate")
        return source
    if (source.count(START)!=1 or source.count(AFTER_SUB)!=1 or
        source.count(OUTPUT)!=1 or
        any(source.count(k)!=1 for k in FIXED) or
        "ur_qa08_premath_brightness5" in source):
        raise ValueError("unknown pinned original PPU/competing brightness patch")
    out=source.replace(START,INTRO+START,1)
    out=out.replace(AFTER_SUB,BRIGHTEN+AFTER_SUB,1)
    for name,replacement in FIXED.items():
        out=out.replace(name,replacement,1)
    return out.replace(OUTPUT,REPLACEMENT,1)

def brightness5(value:int,b:int)->int:
    if not 0<=value<32 or not 0<=b<=15:
        raise ValueError("source 5-bit channel or PPU master brightness invalid")
    return (value*b+7)//15

def stage(game:Path,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV or pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("foreign source, cross-title common SNESRecomp disallowed")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("real RF017 guest dispatch missing")
    target=game/SOURCE
    previous=target.read_text(encoding="utf-8")
    candidate=patched(previous)
    if write and candidate!=previous:
        target.write_text(candidate,encoding="utf-8")
    return target
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-candidate",action="store_true")
    a=p.parse_args()
    try: result=stage(a.game,write=a.apply_candidate)
    except (ValueError,OSError) as exc:p.exit(2,f"QA08_PREMATH_TRIAL_REJECTED: {exc}\n")
    print("QA08_PREMATH_SOURCE_TRIAL",result,
          "staged="+str(int(a.apply_candidate)),
          "native_source_unchanged=0 release_quality_accepted=0")
if __name__=="__main__":main()

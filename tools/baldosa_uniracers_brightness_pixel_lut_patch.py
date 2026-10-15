#!/usr/bin/env python3
"""QA-08 title-scoped PPU master-brightness pixel-precision candidate.

Source proven from the immutable 2014 Snes9x global mul_brightness[16][32]
table: all 512 values EXACTLY (channel5 * brightness + 7) // 15, then
5→8 bit channel expansion. Pinned Baldosa applies brightness AFTER
5→8 expansion, often leaving incorrect noncanonical 8-bit channels
on menu, countdown and result scenes, affecting 50k+ source pixels.

Apply only to the disposable pinned Uniracers Windows game checkout,
NOT to the SNESRecomp framework upstream/cross-title renderer. Do not
change 65816 guest, CPU/APU clocks, PPU OAM/HDMA timing, host Modern
input/business, saves or intentional 7:6 / 256x224 geometry.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV,
    )
except ImportError:
    from baldosa_uniracers_hdma_firstline_patch import (
        pinned_revision, GAME_REV, CORE_REV,
    )

MARK="UR_QA08_2014_SNES9X_5BIT_BRIGHTNESS_CANDIDATE"
FILE=Path("snesrecomp/runner/src/snes/ppu.c")
OLD="""        ((i << 3) | (i >> 2)) * ppu_brightness / 15;"""
NEW="""        /* UR_QA08_2014_SNES9X_5BIT_BRIGHTNESS_CANDIDATE: same 512-entry
         * 2014 original Snes9x brightness LUT. Quantize SNES 5-bit colour
         * BEFORE expanding it to 8-bit display; avoid 8-bit division truncation.
         * Game-scoped experimental raster only, NOT cross-title core policy. */
        (((i * ppu_brightness + 7) / 15) << 3) |
        (((i * ppu_brightness + 7) / 15) >> 2);"""
BEFORE="""    if (PPU_brightness(ppu) != ppu->lastBrightnessMult) {
      uint8_t ppu_brightness = PPU_brightness(ppu);
      ppu->lastBrightnessMult = ppu_brightness;
      for (int i = 0; i < 32; i++)
        ppu->brightnessMultHalf[i * 2] = ppu->brightnessMultHalf[i * 2 + 1] = ppu->brightnessMult[i] =
"""
AFTER="""      // Store 31 extra entries to remove the need for clamping to 31.
      memset(&ppu->brightnessMult[32], ppu->brightnessMult[31], 31);
"""


def patch_source(source:str)->str:
    if source.count(BEFORE)!=1 or source.count(AFTER)!=1:
        raise ValueError("pinned PPU 5-bit output brightness table owner changed")
    start=source.index(BEFORE)+len(BEFORE)
    end=source.index(AFTER,start)
    body=source[start:end]
    if MARK in source:
        if source.count(MARK)!=1 or body!=NEW+"\n":
            raise ValueError("modified or partial 5-bit brightness candidate")
        return source
    if source.count(OLD)!=1 or body!=OLD+"\n":
        raise ValueError("other PPU brightness revision or unsupported core")
    return source[:start]+NEW+"\n"+source[end:]


def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV:
        raise ValueError("Uniracers title source commit does not match")
    core=game/"snesrecomp"
    if pinned_revision(core)!=CORE_REV:
        raise ValueError("SNESRecomp framework source commit does not match")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("expected generated Uniracers guest absent")
    file=game/FILE
    original=file.read_text(encoding="utf-8")
    changed=patch_source(original)
    if write and changed!=original:
        file.write_text(changed,encoding="utf-8")
    return file


def mul_snes9x_2014(brightness:int,channel5:int)->int:
    """Exact pinned Snes9x 2014 globals.cpp lookup all 16x32 entries."""
    if not 0<=brightness<16 or not 0<=channel5<32:
        raise ValueError("invalid actual SNES PPU brightness/channel")
    return (brightness*channel5+7)//15


def expanded_snes9x_brightness(brightness:int,channel5:int)->int:
    five=mul_snes9x_2014(brightness,channel5)
    return (five<<3)|(five>>2)


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",required=True,type=Path)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try:
        file=apply_game(a.game,write=a.apply_candidate)
    except (ValueError,OSError) as exc:
        ap.exit(2,f"UR_QA08_BRIGHTNESS_CANDIDATE_REJECTED: {exc}\n")
    print(f"UR_QA08_BRIGHTNESS_2014_CANDIDATE applied={int(a.apply_candidate)} "
          f"file={file} original_table_entries=512 same_guest=1 "
          "actual_windows_menu_result_raster=UNVERIFIED "
          "cross_title_upstream=none release_approved=0")


if __name__=="__main__":
    main()

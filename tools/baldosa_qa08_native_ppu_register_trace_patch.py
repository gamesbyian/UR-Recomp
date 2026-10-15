#!/usr/bin/env python3
"""Read-only native Original PPU state witness for qualified 2P fades/results.

Game-scoped, opt-in ONLY in the disposable pinned Windows Uniracers title.
No source PPU rendering, HDMA, CPU/APU, guest data or Modern changes.
The active legacy PPU is sampled at the beginning of three native lines,
and only in short scene windows independently selected from Snes9x sources.
The original reference's INIDISP/CGADSUB and CGRAM are read from existing
Snes9x snesref debug exports, never reconstructed by editing the guest.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools.baldosa_uniracers_brightness_pixel_lut_patch import (
        pinned_revision,GAME_REV,CORE_REV,LEGACY_MARK,
    )
except ImportError:
    from baldosa_uniracers_brightness_pixel_lut_patch import (
        pinned_revision,GAME_REV,CORE_REV,LEGACY_MARK,
    )

RELATIVE=Path("snesrecomp/runner/src/snes/ppu_legacy.c")
MARK="UR_QA08_READONLY_NATIVE_ORIGINAL_PPU_STATE"
HEADER='#include <stdbool.h>\n'
ENTRY="void ppu_draw_whole_line_legacy(Ppu *ppu, int line) {\n  // actual line\n"
TRACE="  /* UR_QA08_READONLY_NATIVE_ORIGINAL_PPU_STATE: graphics-only source witness.\n   * Three in-frame lines and a few scene windows, never a raster write.\n   * The environment variable is set only by the single real 2P QA route. */\n  if ((line == 1 || line == 112 || line == 114) &&\n      getenv(\"UR_QA08_WINDOWS_PPU_STATE_TRACE\")) {\n    const int frame = snes_frame_counter;\n    if ((frame >= 3616 && frame <= 3690) ||\n        (frame >= 4000 && frame <= 4090) ||\n        (frame >= 4170 && frame <= 4180) ||\n        (frame >= 5170 && frame <= 5190)) {\n      uint32_t cgram_fnv = 2166136261u;\n      for (int j = 0; j < 256; ++j) {\n        const uint16_t word = ppu->cgram[j];\n        cgram_fnv ^= (uint8_t)word;\n        cgram_fnv *= 16777619u;\n        cgram_fnv ^= (uint8_t)(word >> 8);\n        cgram_fnv *= 16777619u;\n      }\n      fprintf(stderr,\n          \"UR_QA08_WIN_PPU_STATE frame=%d line=%d inidisp=%02x \"\n          \"brightness=%u forced_blank=%u cgadsub=%02x cgwsel=%02x \"\n          \"fixedcolor=%04x cg6c=%04x cg6d=%04x cg6e=%04x cg6f=%04x cgram_fnv=%08x\\n\",\n          frame,line,(unsigned)ppu->inidisp,\n          (unsigned)PPU_brightness(ppu),(unsigned)(!!PPU_forcedBlank(ppu)),\n          (unsigned)ppu->cgadsub,(unsigned)ppu->cgwsel,\n          (unsigned)ppu->fixedColor,\n          (unsigned)ppu->cgram[0x6c],(unsigned)ppu->cgram[0x6d],\n          (unsigned)ppu->cgram[0x6e],(unsigned)ppu->cgram[0x6f],\n          (unsigned)cgram_fnv);\n    }\n  }\n"



def patch_source(original:str)->str:
    if LEGACY_MARK not in original:
        raise ValueError("corrected 2014 source brightness must be staged first")
    if original.count(HEADER)!=1 or original.count(ENTRY)!=1:
        raise ValueError("unrecognized active original raster draw hook")
    if MARK in original:
        if (original.count(MARK)!=1 or original.count(TRACE)!=1
            or original.count("#include <stdio.h>\n")!=1
            or original.count("#include <stdlib.h>\n")!=1):
            raise ValueError("native PPU state probe incomplete or tampered")
        return original
    return (original.replace(HEADER,HEADER+"#include <stdio.h>\n#include <stdlib.h>\n",1)
           .replace(ENTRY,ENTRY+TRACE,1))


def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if pinned_revision(game)!=GAME_REV:
        raise ValueError("unrecognized game")
    if pinned_revision(game/"snesrecomp")!=CORE_REV:
        raise ValueError("unrecognized framework")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("Uniracers guest source not generated")
    file=game/RELATIVE
    original=file.read_text(encoding="utf-8")
    patched=patch_source(original)
    if write and original!=patched:
        file.write_text(patched,encoding="utf-8")
    return file


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-candidate",action="store_true")
    a=p.parse_args()
    try:
        f=apply_game(a.game,write=a.apply_candidate)
    except (ValueError,OSError) as exc:
        p.exit(2,f"UR_QA08_NATIVE_PPU_REGISTER_REJECTED: {exc}\n")
    print(f"UR_QA08_NATIVE_PPU_READONLY source={f} "
          f"staged={int(a.apply_candidate)} "
          "active_when_opt_in_only=1 release_accepted=0")


if __name__=="__main__":
    main()

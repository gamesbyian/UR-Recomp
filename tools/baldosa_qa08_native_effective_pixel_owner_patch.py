#!/usr/bin/env python3
"""Title-scoped read-only per-pixel SNES PPU layer/OBJ provenance observer.

Stage ONLY on exact-pinned disposable Uniracers Windows Baldosa checkout.
Source-qualified (native x, output y) samples:
  early 2P arrow guest1280 (55,65)
  medal/adjacent OBJ guest4032 and 4176 (207,91),(205,115),(205,139),
  (225,96),(225,120). Output raster y = active legacy raster line - 1.

Logs *existing* resolver outputs, not speculative post-hoc layer re-evaluation.
Does not modify framebuffer, OBJ state, CGRAM, CPU/APU, guest, Modern or input.
"""
from __future__ import annotations
import argparse
from pathlib import Path

try:
    from tools import baldosa_qa08_native_ppu_register_trace_patch as previous
except ImportError:
    import baldosa_qa08_native_ppu_register_trace_patch as previous

RELATIVE=previous.RELATIVE
MARK="UR_QA08_NATIVE_EFFECTIVE_PIXEL_OWNER"
INTRO="static void ppu_render_pixel(Ppu *ppu, int x, int y) {\n"
MAIN="    int mainLayer = ppu_resolve_pixel(ppu, x, y, false, &r, &g, &b);\n"
WINDOW="    bool colorWindowState = ppu_window_contains(ppu, 5, x);\n"
MATH="    bool mathEnabled = mainLayer < 6 && (PPU_mathEnabled(ppu) >> mainLayer & 1) && !(\n"
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
  if (((snes_frame_counter == 1280 && x == 55 && y == 66) ||
       ((snes_frame_counter == 4032 || snes_frame_counter == 4176) &&
        ((x == 207 && y == 92) ||
         (x == 205 && (y == 116 || y == 140)) ||
         (x == 225 && (y == 97 || y == 121))))) &&
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
    if (snes_frame_counter != 1280) {
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

def patch_source(src:str)->str:
    if MARK in src:
        expected=[(INTRO+DECL,1),(MAIN+CAPTURE_MAIN,1),
                  (WINDOW+CAPTURE_WINDOW,1),(MATH+CAPTURE_MATH,1),
                  (SUB+CAPTURE_SUB,1),(END+TRACE,1)]
        if any(src.count(fragment)!=n for fragment,n in expected):
            raise ValueError("partial/tampered pixel provenance instrument")
        return src
    if previous.MARK not in src or previous.LEGACY_MARK not in src or (
        src.count(previous.TRACE)!=1
    ):
        raise ValueError("original PPU source state + brightness guards absent")
    for a in (INTRO,MAIN,WINDOW,MATH,SUB,END):
        if src.count(a)!=1:
            raise ValueError("pinned active PPU render/compositor source changed: "+a.strip())
    if "#include <stdio.h>" not in src or "#include <stdlib.h>" not in src:
        raise ValueError("pinned read-only trace headers missing")
    for anchor,replacement in (
        (INTRO,INTRO+DECL),
        (MAIN,MAIN+CAPTURE_MAIN),
        (WINDOW,WINDOW+CAPTURE_WINDOW),
        (MATH,MATH+CAPTURE_MATH),
        (SUB,SUB+CAPTURE_SUB),
        (END,END+TRACE),
    ):
        src=src.replace(anchor,replacement,1)
    return src

def apply_game(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if previous.pinned_revision(game)!=previous.GAME_REV:
        raise ValueError("unrecognized Uniracers guest pin")
    if previous.pinned_revision(game/"snesrecomp")!=previous.CORE_REV:
        raise ValueError("unrecognized native PPU core pin")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("unrecognized generated 65816 guest")
    file=game/RELATIVE
    original=file.read_text(encoding="utf-8")
    patched=patch_source(original)
    if write and original!=patched:
        file.write_text(patched,encoding="utf-8")
    return file

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",required=True,type=Path)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try:
        path=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        ap.exit(2,f"QA08_EFFECTIVE_PIXEL_OWNER_REJECTED: {exc}\n")
    print("QA08_NATIVE_EFFECTIVE_PIXEL_OWNER",path,
          "staged="+str(int(a.apply_candidate)),
          "guest_and_raster_modified=0 release_gate=0")

if __name__=="__main__":
    main()

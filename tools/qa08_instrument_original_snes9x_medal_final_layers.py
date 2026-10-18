#!/usr/bin/env python3
"""Diagnostic only: trace actual original Snes9x medal BG/OBJ depth stages.

Apply after the pinned original sprite-painter call probe. Emit bounded
read-only stage witnesses. No guest clock, pixel, tile, layer or input edits.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_ORIGINAL_MEDAL_FINAL_LAYER_SOURCE"
REQUIRES = "UR_QA08_ORIGINAL_SNES9X_ACTIVE_MEDAL_TILE_CALL"
ENTRY = "static inline void RenderScreen (bool8 sub)\n{"
OBJ = "\t\tDrawOBJS(D + 4);"
MACRO = "\t\t}\n\n\tswitch (PPU.BGMode)"
END = "\tDrawBackdrop();\n}"
SOURCE = r"""
/* UR_QA08_ORIGINAL_MEDAL_FINAL_LAYER_SOURCE:
 * Genuine original host PPU depth after OBJ, after each BG and final backdrop.
 * Subscreen is explicitly excluded. No native frame alignment asserted. */
static void urqa08_original_medal_layer(const char *stage, int bg, bool8 sub)
{
    if (sub) return;
    const unsigned f=(unsigned)ICPU.Frame;
    if (!((f>=4028 && f<=4036) || (f>=4172 && f<=4180))) return;
    static const int xs[5]={207,205,205,225,225};
    static const int ys[5]={91,115,139,96,120};
    for (unsigned i=0;i<5;i++) {
        const int x=xs[i], y=ys[i];
        if (y<(int)GFX.StartY || y>(int)GFX.EndY) continue;
        const unsigned p=(unsigned)y*(unsigned)GFX.PPL+(unsigned)x;
        fprintf(stderr,
          "UR_QA08_ORIGINAL_MEDAL_LAYER frame=%u range=%u,%u "
          "x=%d y=%d stage=%s bg=%d bgmode=%d "
          "depth=%02x rgb565=%04x source_callback_proven=0 "
          "native_frame_proven=0\n",
          f,(unsigned)GFX.StartY,(unsigned)GFX.EndY,
          x,y,stage,bg,(int)PPU.BGMode,
          (unsigned)GFX.DB[p],(unsigned)GFX.S[p]);
    }
}
"""

def patch_source(text: str) -> str:
    if MARK in text:
        raise ValueError("source already has the final-layer probe")
    for needle in (REQUIRES, ENTRY, OBJ, MACRO, END):
        if text.count(needle) != 1:
            raise ValueError("original 2014 Snes9x stage anchor missing/duplicated: " + needle[:32])
    text = text.replace(ENTRY, SOURCE + "\n" + ENTRY, 1)
    text = text.replace(OBJ, OBJ + '\n\t\turqa08_original_medal_layer("OBJ", -1, sub);', 1)
    text = text.replace(MACRO,
                        '\t\t\turqa08_original_medal_layer("BG", n, sub); \\\n' + MACRO,
                        1)
    text = text.replace(END,
                        '\tDrawBackdrop();\n\turqa08_original_medal_layer("FINAL", -1, sub);\n}',
                        1)
    for needle in ('urqa08_original_medal_layer("OBJ", -1, sub);',
                   'urqa08_original_medal_layer("BG", n, sub);',
                   'urqa08_original_medal_layer("FINAL", -1, sub);'):
        if text.count(needle) != 1:
            raise ValueError("incomplete layer instrument: " + needle)
    return text

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    try:
        raw = a.source.read_text(encoding="utf-8")
        patched = patch_source(raw)
        if a.apply:
            a.source.write_text(patched, encoding="utf-8")
    except (ValueError, OSError) as exc:
        p.exit(2, "QA08_ORIGINAL_FINAL_LAYER_REFUSED: " + str(exc) + "\n")
    print("QA08_ORIGINAL_MEDAL_FINAL_LAYER applied=" + str(int(a.apply)),
          "original_source_depth=1 guest_write=0 native_alignment_proven=0")

if __name__ == "__main__":
    main()

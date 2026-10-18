#!/usr/bin/env python3
"""Read-only SNESRecomp physical OBJ tile-fetch/winner witness for QA08 medal.

The already-proven current RF017 native PPU pixel owner probe identifies real
OBJ zbuffer palette colours but does not tell which OAM slot and which 4bpp
VRAM tile wrote the pixel. Instrument the *existing* PpuEvaluateSprites slot
fetch loop at its actual output write, not another sprite decoder or renderer.
The last such write wins by SNES OAM priority, unless a later extension
overwrites the OBJ buffer (verified against the effective pixel owner).
No PPU, DMA, CPU/APU, SRAM or presentation state is changed by this logging.
This file only belongs on the disposable, never-to-merge source instrument.
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

REL = Path("snesrecomp/runner/src/snes/ppu.c")
MARK = "UR_QA08_MEDAL_ACTUAL_OBJ_4BPP_FETCH_READONLY"
ANCHOR = """        // Lower OAM indices are processed later and overwrite higher ones.
                dst[0] = z + pixel;
                if(ppu->extraObjectCount)
"""
TRACE = r"""        // Lower OAM indices are processed later and overwrite higher ones.
                dst[0] = z + pixel;
                /* UR_QA08_MEDAL_ACTUAL_OBJ_4BPP_FETCH_READONLY. This is the
                 * genuine, already decoded 4bpp fetch and OAM priority write
                 * at five source-registered medal points. Read-only, not a
                 * second compositor, palette correction or temporal shift.
                 * All same-coordinate candidate writes are retained: the
                 * last surviving write owns the per-line OBJ buffer unless
                 * the later extra-object stage replaces it. */
                if ((snes_frame_counter == 4032 ||
                     snes_frame_counter == 4048 ||
                     snes_frame_counter == 4064 ||
                     snes_frame_counter == 4080 ||
                     snes_frame_counter == 4176) &&
                    (((col + x + px == 207) && (line == 91)) ||
                     ((col + x + px == 205) &&
                      (line == 115 || line == 139)) ||
                     ((col + x + px == 225) &&
                      (line == 96 || line == 120))) &&
                    getenv("UR_QA08_WINDOWS_OBJ_FETCH_TRACE")) {
                  fprintf(stderr,
                    "UR_QA08_WIN_OBJ_FETCH frame=%u x=%d raster_y=%d "
                    "slot=%u oam=%04x attrs=%04x "
                    "oam_tile=%02x used_tile=%03x objadr=%04x "
                    "row=%d src_col=%d px=%d "
                    "palette=%02x priority=%u pixel=%x plane=%08x "
                    "writer_obj=%04x\n",
                    (unsigned)snes_frame_counter, col + x + px, line,
                    (unsigned)slot,
                    (unsigned)ppu->oam[index], (unsigned)oam1,
                    (unsigned)(oam1 & 255), (unsigned)usedTile,
                    (unsigned)objAdr, row, col, px,
                    (unsigned)paletteBase, (unsigned)prio,
                    (unsigned)pixel, (unsigned)plane,
                    (unsigned)(z + pixel));
                }
                if(ppu->extraObjectCount)
"""

def patch_source(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 1 or source.count(TRACE) != 1:
            raise ValueError("source-side OBJ fetch witness drift/partial injection")
        # Removing only the exactly qualified trace must recover canonical PPU.
        before = source.replace(TRACE, ANCHOR, 1)
        if before.count(ANCHOR) != 1:
            raise ValueError("cannot reverse the source-only trace")
        return source
    if (source.count(ANCHOR) != 1 or
        '#include <stdio.h>' not in source or
        '#include <stdlib.h>' not in source or
        "static bool ppu_evaluateSprites" not in source or
        "PpuComposeExtraObjects(" not in source or
        "PpuRenderVram(ppu)" not in source):
        raise ValueError("pinned genuine SNESRecomp physical OBJ fetch changed")
    if "UR_QA08_WIN_OBJ_FETCH" in source:
        raise ValueError("competing medal fetch observer already injected")
    return source.replace(ANCHOR, TRACE, 1)

def apply_game(game: Path, *, write: bool = False) -> Path:
    game = game.resolve()
    if pinned_revision(game) != GAME_REV or pinned_revision(game / "snesrecomp") != CORE_REV:
        raise ValueError("game/core source identity changed")
    if not (game / "src/gen/dispatch_v2.c").is_file():
        raise ValueError("generated native Uniracers USA guest missing")
    path = game / REL
    original = path.read_text(encoding="utf-8")
    patched = patch_source(original)
    if write and patched != original:
        path.write_text(patched, encoding="utf-8")
    return path

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game",required=True,type=Path)
    ap.add_argument("--apply-candidate",action="store_true")
    a=ap.parse_args()
    try:
        path=apply_game(a.game,write=a.apply_candidate)
    except (OSError,ValueError) as exc:
        ap.exit(2,f"QA08_SOURCE_MEDAL_4BPP_FETCH_REJECTED: {exc}\n")
    print("QA08_SOURCE_MEDAL_OBJ_FETCH",path,
          "staged="+str(int(a.apply_candidate)),
          "guest_CPU_unchanged=1 product=0 original_PPU_release=0")
if __name__=="__main__":
    main()

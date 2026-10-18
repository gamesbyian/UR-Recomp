#!/usr/bin/env python3
"""Observe six late RF017 result-epoch CPU CGRAM writer packets, read-only.

Only in a disposable exact-pinned Windows Uniracers title; no changes to CPU,
guest code, native PPU computation, DMA order, palette values or Modern.
Log actual $2121/$2122 *input* transactions with host SNES frame, beam and
pre-write CGRAM port pointer/latch, explicitly separate from raster snapshots.
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

RELATIVE = Path("snesrecomp/runner/src/snes/ppu.c")
MARK = "UR_QA08_NATIVE_LATE_CGRAM_PORT_CHRONOLOGY"
ANCHOR = "void ppu_write(Ppu* ppu, uint8_t adr, uint8_t val) {\n  ppu_wlog_note(adr, val);\n"
TRACE = r"""  /* UR_QA08_NATIVE_LATE_CGRAM_PORT_CHRONOLOGY: observation only, before the
   * production PPU port/latch handler runs. This records the guest writer
   * phase, not a reconstructed or corrected colour. Short bounded route. */
  if ((adr == 0x21 || adr == 0x22) &&
      getenv("UR_QA08_WINDOWS_LATE_CGRAM_TRACE") &&
      snes_frame_counter >= 5152 && snes_frame_counter <= 5195 &&
      g_snes && ppu == g_snes->ppu) {
    fprintf(stderr,
      "UR_QA08_WIN_LATE_CGRAM_WRITE frame=%d v=%u h=%u adr=%02x "
      "val=%02x src=%u ptr=%02x second=%u\n",
      snes_frame_counter, (unsigned)g_snes->vPos,
      (unsigned)g_snes->hPos, (unsigned)adr, (unsigned)val,
      (unsigned)g_ppu_wlog_src, (unsigned)ppu->cgramPointer,
      (unsigned)(!!ppu->cgramSecondWrite));
  }
"""

def patch_source(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 1 or source.count(TRACE) != 1:
            raise ValueError("partial or tampered original PPU port witness")
        return source
    if (source.count(ANCHOR) != 1 or
        "#include <stdio.h>" not in source or
        "#include <stdlib.h>" not in source or
        "case 0x21:" not in source or "case 0x22:" not in source):
        raise ValueError("pinned native PPU port handler differs")
    return source.replace(ANCHOR, ANCHOR + TRACE, 1)

def apply_game(game: Path, *, write: bool = False) -> Path:
    game = game.resolve()
    if pinned_revision(game) != GAME_REV:
        raise ValueError("unrecognized Uniracers guest")
    if pinned_revision(game/"snesrecomp") != CORE_REV:
        raise ValueError("unrecognized SNESRecomp core")
    if not (game/"src/gen/dispatch_v2.c").is_file():
        raise ValueError("Uniracers native guest is not generated")
    f = game/RELATIVE
    old = f.read_text(encoding="utf-8")
    new = patch_source(old)
    if write and old != new:
        f.write_text(new, encoding="utf-8")
    return f

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--apply-candidate", action="store_true")
    a = p.parse_args()
    try:
        f = apply_game(a.game, write=a.apply_candidate)
    except (ValueError, OSError) as exc:
        p.exit(2, f"UR_QA08_LATE_CGRAM_PORT_REJECT: {exc}\n")
    print("UR_QA08_LATE_CGRAM_PORT_READONLY", f,
          "staged="+str(int(a.apply_candidate)), "release=0")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Inject a bounded, host-only x=255 composition trace into staged SNESRecomp."""
from __future__ import annotations

import argparse
from pathlib import Path


def patch_ppu(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    needle = """  uint32 *dst = (uint32*)&ppu->renderBuffer[(y - 1) * ppu->renderPitch], *dst_org = dst;
"""
    insert = r'''  {
    static int ws_edge_trace = -1;
    if (ws_edge_trace < 0)
      ws_edge_trace = getenv("SNESRECOMP_WS_EDGE_TRACE") ? 1 : 0;
    if (ws_edge_trace && y >= 144 && y <= 145 &&
        snes_frame_counter >= 2888 && snes_frame_counter <= 2905) {
      const int sx = 255;
      const int bi = sx + kPpuExtraLeftRight;
      unsigned span = 0;
      while (span < cwin.nr &&
             !(cwin.edges[span] <= sx && sx < cwin.edges[span + 1]))
        span++;
      unsigned cwbit = span < cwin.nr ? ((cwin.bits >> span) & 1u) : 0xffu;
      fprintf(stderr,
              "WS_EDGE frame=%d y=%u x=%d extra=%u main=%04X sub=%04X obj=%04X "
              "cgwsel=%02X cgadsub=%02X fixed=%04X tm=%02X ts=%02X "
              "tmw=%02X tsw=%02X cwin_nr=%u cwin_bits=%02X cwin_span=%u "
              "cwin_bit=%u cwin_l=%d cwin_r=%d\n",
              snes_frame_counter, y, sx, ppu->extraLeftRight,
              ppu->bgBuffers[0].data[bi], ppu->bgBuffers[1].data[bi],
              ppu->objBuffer.data[bi], ppu->cgwsel, ppu->cgadsub,
              ppu->fixedColor, ppu->screenEnabled[0], ppu->screenEnabled[1],
              ppu->screenWindowed[0], ppu->screenWindowed[1],
              cwin.nr, cwin.bits, span, cwbit,
              span < cwin.nr ? cwin.edges[span] : -999,
              span < cwin.nr ? cwin.edges[span + 1] : -999);
    }
  }

'''
    if needle not in text:
        raise SystemExit(f"{path}: composition insertion point not found")
    text = text.replace(needle, insert + needle, 1)

    candidate_needle = """        int pixel = (bits >> 0) & 1 | (bits >> 7) & 2 |
                    (bits >> 14) & 4 | (bits >> 21) & 8;
        if (pixel == 0) continue;
"""
    candidate_insert = r'''        int pixel = (bits >> 0) & 1 | (bits >> 7) & 2 |
                    (bits >> 14) & 4 | (bits >> 21) & 8;
        {
          static int ws_obj_trace = -1;
          if (ws_obj_trace < 0)
            ws_obj_trace = getenv("SNESRECOMP_WS_EDGE_TRACE") ? 1 : 0;
          const int screen_x = col + x + px;
          if (ws_obj_trace && screen_x == 255 &&
              line >= 143 && line <= 144 &&
              snes_frame_counter >= 2888 && snes_frame_counter <= 2905) {
            int rawx = ppu->oam[index] & 0xff;
            rawx |= ((ppu->highOam[index >> 3] >> (index & 7)) & 1) << 8;
            fprintf(stderr,
                    "WS_OBJ_CAND frame=%d line=%d slot=%d rawx=%d x=%d "
                    "size=%d col=%d px=%d row=%u oam1=%04X usedTile=%d "
                    "plane=%08X z=%04X pixel=%02X tiles=%d extraL=%u extraR=%u\\n",
                    snes_frame_counter, line, slot, rawx, x, spriteSize,
                    col, px, row, oam1, usedTile, plane, z, pixel, tilesFound,
                    ppu->extraLeftCur, ppu->extraRightCur);
          }
        }
        if (pixel == 0) continue;
'''
    if candidate_needle not in text:
        raise SystemExit(f"{path}: OBJ candidate insertion point not found")
    text = text.replace(candidate_needle, candidate_insert, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ppu_c", type=Path)
    args = ap.parse_args()
    patch_ppu(args.ppu_c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

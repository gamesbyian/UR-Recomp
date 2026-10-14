#!/usr/bin/env python3
"""Diagnostic-only pixel composer witness in pinned SNESRecomp PPU.

A single guarded read of main/sub priority buffers and output framebuffer at
guest-target candidate 2208. No PPU, guest, art, OAM or window data is mutated.
Apply only to disposable Baldosa pinned framework before compiling QA-08 AOT.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_NATIVE_PPU_PIXEL"
ANCHOR = "          dst[0] = color_map[b] | color_map[g] << 8 | color_map[r] << 16;\n"
ADD = r'''
          /* UR_QA08_NATIVE_PPU_PIXEL. One read-only pixel witness per selected
           * row/column on one explicitly requested emulator frame. The
           * source-space X=133 means native internal index 272+(133-43)=362.
           * This watches actual main/sub OBJ/BG tags BEFORE overlay export.
           * Never infer original-hardware timing or artist approval. */
          {
            static long qa08_frame = -2;
            if (qa08_frame == -2) {
              char *end = NULL;
              const char *setting = getenv("UR_QA08_PPU_PIXEL_FRAME");
              qa08_frame = -1;
              if (setting && *setting) {
                unsigned long target = strtoul(setting, &end, 10);
                if (end != setting && *end == '\0' && target <= 500000UL)
                  qa08_frame = (long)target;
              }
            }
            if (qa08_frame >= 0 &&
                (unsigned long)snes_frame_counter == (unsigned long)qa08_frame &&
                ppu->extraLeftCur == 43 && ppu->extraRightCur == 43 &&
                (y == 51 || y == 163) &&
                i == kPpuExtraLeftRight+90) {
              const uint16_t subp = ppu->bgBuffers[1].data[i];
              const unsigned main_rgb15 = PpuPixelColor(ppu, pixel, i) & 0x7fff;
              const unsigned sub_rgb15 =
                  (subp & 0xff) ? (PpuPixelColor(ppu, subp, i) & 0x7fff) : 0;
              const unsigned source_x =
                  i - kPpuExtraLeftRight + ppu->extraLeftCur;
              fprintf(stderr,
                "UR_QA08_NATIVE_PPU_PIXEL frame=%u x=%u y=%u "
                "main=%04X sub=%04X main15=%04X sub15=%04X "
                "final=%06X cgadsub=%02X cgwsel=%02X fixed15=%04X "
                "math=%u rendered_sub=%u sub_present=%u clip_main=%u\n",
                (unsigned)snes_frame_counter, source_x, y-1,
                (unsigned)pixel, (unsigned)subp,
                main_rgb15, sub_rgb15, (unsigned)(dst[0] & 0xffffff),
                (unsigned)ppu->cgadsub, (unsigned)ppu->cgwsel,
                (unsigned)ppu->fixedColor,
                (unsigned)((math_enabled_cur & (1u << main_layer)) != 0),
                (unsigned)rendered_subscreen, (unsigned)((subp & 0xff) != 0),
                (unsigned)((cw_clip_math & 1u) != 0));
            }
          }
'''

def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("pinned PPU pixel probe already applied")
    if source.count(ANCHOR) != 1 or "static NOINLINE void PpuDrawWholeLine(" not in source:
        raise ValueError("pinned PPU compositor source anchor changed")
    return source.replace(ANCHOR, ANCHOR + ADD, 1)

def apply(framework: Path, check_only: bool = False) -> Path:
    p = framework / "runner/src/snes/ppu.c"
    changed = patch_source(p.read_text(encoding="utf8"))
    if not check_only:
        p.write_text(changed, encoding="utf8")
    return p

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--framework", required=True, type=Path)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    try:
        result = apply(args.framework, args.check_only)
    except (ValueError, OSError) as exc:
        ap.exit(2, f"QA08 PPU composer probe rejected: {exc}\n")
    print(f"QA08 original PPU pixel probe staged={not args.check_only} file={result}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

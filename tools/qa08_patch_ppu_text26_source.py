#!/usr/bin/env python3
"""Read-only 26-source-pixel native PPU probe, reusing the accepted emitter.

Only patches a disposable pinned SNESRecomp PPU after the existing, separately
accepted two-point QA-08 probe. Requires explicit frame2208 opt-in to emit.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.qa08_patch_ppu_pixel_compose_probe import (
        ADD as TWO_POINT_ADD, ANCHOR,
    )
except ModuleNotFoundError:
    from qa08_patch_ppu_pixel_compose_probe import ADD as TWO_POINT_ADD, ANCHOR

MARK = "UR_QA08_NATIVE_PPU_TEXT26"
OLD = """                (y == 51 || y == 163) &&
                i == kPpuExtraLeftRight+90) {"""
NEW = """                ((y >= 48 && y <= 53) || (y >= 160 && y <= 165)) &&
                (i >= kPpuExtraLeftRight+89 &&
                 i <= kPpuExtraLeftRight+93) &&
                (qa08_text26_masks[y >= 160 ? y-160 : y-48] &
                 (1u << (i - (kPpuExtraLeftRight+89)))) != 0) {"""

def probe_block() -> str:
    if TWO_POINT_ADD.count(OLD) != 1:
        raise ValueError("accepted two-point source condition has changed")
    src = TWO_POINT_ADD.replace(
        "UR_QA08_NATIVE_PPU_PIXEL", MARK
    ).replace(
        "UR_QA08_PPU_PIXEL_FRAME", "UR_QA08_PPU_TEXT26_FRAME"
    ).replace(
        "qa08_frame", "qa08_text26_frame"
    ).replace(
        "            if (qa08_text26_frame >= 0 &&",
        "            /* Row 47..52 and +112: bits encode X132,133,135,136. */\n"
        "            static const uint8_t qa08_text26_masks[6] = {2,27,11,3,3,1};\n"
        "            if (qa08_text26_frame >= 0 &&"
    ).replace(OLD, NEW)
    if src == TWO_POINT_ADD or src.count(MARK) < 2 or NEW not in src:
        raise ValueError("source pixel probe derivation failed")
    return src

def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("26-pixel source instrumentation already present")
    if source.count(ANCHOR) != 1 or TWO_POINT_ADD not in source:
        raise ValueError("accepted original two-pixel native PPU source patch missing")
    return source.replace(ANCHOR, ANCHOR + probe_block(), 1)

def apply(framework: Path, check_only: bool = False) -> Path:
    p = framework / "runner/src/snes/ppu.c"
    patched = patch_source(p.read_text(encoding="utf8"))
    if not check_only:
        p.write_text(patched, encoding="utf8")
    return p

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--framework", type=Path, required=True)
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    try:
        result = apply(a.framework, a.check_only)
    except (ValueError, OSError) as exc:
        ap.exit(2, f"QA08 native PPU text26 probe rejected: {exc}\n")
    print(f"QA08 PPU source-text 26 staged={not a.check_only} file={result}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

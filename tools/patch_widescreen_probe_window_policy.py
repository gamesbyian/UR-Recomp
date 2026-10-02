#!/usr/bin/env python3
"""Add a disposable switch that preserves authentic 0/255 PPU window edges."""
from __future__ import annotations

import argparse
from pathlib import Path


def patch_ppu(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = """  PpuWidescreenAdjustPinnedWindowEdges(win->edges[0], window_right, &w1l,
                                       &w1r, &w2l, &w2r);
"""
    new = """  if (!getenv("SNESRECOMP_WS_KEEP_PINNED_WINDOWS"))
    PpuWidescreenAdjustPinnedWindowEdges(win->edges[0], window_right, &w1l,
                                         &w1r, &w2l, &w2r);
"""
    if old not in text:
        raise SystemExit(f"{path}: pinned-window call site not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ppu_c", type=Path)
    args = ap.parse_args()
    patch_ppu(args.ppu_c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply a disposable native-widescreen host hook to a generated SNESRecomp project.

This patch is for CI/reconnaissance only. It changes presentation geometry, never
Uniracers guest code or WRAM state. The pinned runner's SNESRECOMP_WS_EXTRA
environment variable supplies the per-side margin.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def patch_host(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    include_anchor = '#include "host_main.h"\n'
    if include_anchor not in text:
        raise SystemExit(f"{path}: host_main include anchor not found")
    text = text.replace(
        include_anchor,
        include_anchor + '#include "snes/ppu.h"\n',
        1,
    )

    struct_anchor = "static const SnesDesktopHostGame kGameHost = {\n"
    if struct_anchor not in text:
        raise SystemExit(f"{path}: game-host anchor not found")

    helper = """static void WidescreenProbePrepareFrame(
    int drawable_w, int drawable_h, int *frame_w, int *frame_h)
{
    (void)drawable_w;
    (void)drawable_h;
    int extra = PpuWsExtraOverride();
    if (extra < 0)
        extra = 0;
    *frame_w = 256 + extra * 2;
    *frame_h = 224;
}

"""
    text = text.replace(struct_anchor, helper + struct_anchor, 1)

    field_anchor = '    .num_players         = @PLAYERS@,\n'
    if field_anchor not in text:
        # setup_project has already substituted the player count.
        import re
        m = re.search(r"^    \.num_players\s*=\s*\d+,\n", text, re.M)
        if not m:
            raise SystemExit(f"{path}: num_players anchor not found")
        field_anchor = m.group(0)

    fields = (
        field_anchor
        + "    .native_widescreen    = 1,\n"
        + "    .prepare_frame        = WidescreenProbePrepareFrame,\n"
    )
    text = text.replace(field_anchor, fields, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("main_c", type=Path)
    args = ap.parse_args()
    patch_host(args.main_c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

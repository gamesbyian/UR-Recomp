#!/usr/bin/env python3
"""Attach +24 course-derived host raster to an isolated Baldosa checkout.

This is stacked AFTER the proven source-racer observer/renderer bridge.
Do not touch AOT guest C, ROM, project-wide framework pins or product host.
Only bounded 2P route frames 1800..2450 are widened when calibrated.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK = "UR_BALDOSA_WS24_SHADOW_PRESENTATION"
ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"
BEFORE = "    .begin_sim_frame    = &ur_baldosa_hd_begin_sim_frame,\n"
AFTER = "    .begin_sim_frame    = &ur_baldosa_ws24_begin_sim_frame,\n"
DRAW_BEFORE = "    .draw_frame         = &ur_baldosa_hd_draw_frame,\n"
DRAW_AFTER = "    .draw_frame         = &ur_baldosa_ws24_draw_frame,\n"
SLOT = "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
API = """/* UR_BALDOSA_WS24_SHADOW_PRESENTATION: disposable host-only test. */
extern void ur_baldosa_ws24_prepare_frame(int, int, int*, int*);
extern void ur_baldosa_ws24_begin_sim_frame(unsigned);
extern int ur_baldosa_ws24_draw_frame(uint8_t*, size_t,
    const uint8_t*, int, int, double);
"""


def patch_main(source: str) -> str:
    if MARK in source:
        return source
    required = (ANCHOR, BEFORE, DRAW_BEFORE, SLOT,
                ".presentation_scale = &ur_baldosa_hd_presentation_scale,")
    if any(source.count(s) != 1 for s in required):
        raise ValueError("Expected the stable #1074 bridge; refusing a different host ABI")
    source = source.replace(ANCHOR, API + "\n" + ANCHOR, 1)
    source = source.replace(BEFORE, AFTER, 1)
    source = source.replace(DRAW_BEFORE, DRAW_AFTER, 1)
    source = source.replace(
        SLOT,
        SLOT + "    .native_widescreen = 1,\n"
             + "    .prepare_frame     = &ur_baldosa_ws24_prepare_frame,\n",
        1)
    return source


def patch_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if "UR_BALDOSA_NATIVE_RACER_PRESENTATION" not in source:
        raise ValueError("Stage the established source-racer bridge first")
    files = (
        root / "tools/baldosa_native_ws24_presentation.cpp",
        root / "native/title/uniracers_ws_margins.c",
        root / "native/product/widescreen_output_composition.cpp",
    )
    if any(not f.is_file() for f in files):
        raise ValueError("Missing repository-owned course/world materializer")
    inc = (root / "native/title").resolve().as_posix()
    product_inc = (root / "native/product").resolve().as_posix()
    shim = files[0].resolve().as_posix()
    return source.rstrip() + (
        "\n\n# " + MARK + ": world course table => PPU shadow, never guest VRAM\n"
        + f'set_source_files_properties("{shim}" PROPERTIES INCLUDE_DIRECTORIES "{inc}")\n'
        + f'target_include_directories(UniracersSNESRecomp PRIVATE "{product_inc}")\n'
        + "target_sources(UniracersSNESRecomp PRIVATE\n"
        + "".join(f'    "{f.resolve().as_posix()}"\n' for f in files)
        + ")\n"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--ur-root", type=Path, required=True)
    a = p.parse_args()
    game, root = a.game.resolve(), a.ur_root.resolve()
    for filename, transform in (
        ("src/main.c", patch_main),
        ("CMakeLists.txt", lambda value: patch_cmake(value, root)),
    ):
        f = game / filename
        before = f.read_text(encoding="utf-8")
        after = transform(before)
        if before != after:
            f.write_text(after, encoding="utf-8")
        print(f"{f}: {'staged' if before != after else 'already staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

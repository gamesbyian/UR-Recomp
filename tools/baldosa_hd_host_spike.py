#!/usr/bin/env python3
"""Attach UR-Recomp's existing racer HD compositor to a *disposable* Baldosa host.

Run baldosa_guest_adapter_spike.py first. Never rewrite guest/generated C or
modify the product's SNESRecomp pin. Ema's host keeps frame/input ownership.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK = "UR_BALDOSA_NATIVE_RACER_PRESENTATION"
PROTOTYPES = """extern int ur_baldosa_hd_presentation_scale(void);
extern void ur_baldosa_hd_begin_sim_frame(unsigned number);
extern int ur_baldosa_hd_draw_frame(uint8_t *dst, size_t pitch,
    const uint8_t *field, int frame_w, int frame_h, double alpha);
"""
FIELD = "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"


def patch_main(source: str) -> str:
    if MARK in source:
        return source
    if source.count(FIELD) != 1 or source.count(ANCHOR) != 1:
        raise ValueError("Expected the pinned Baldosa + UR observer hooks; refuse unknown ABI")
    source = source.replace(ANCHOR, "/* " + MARK + " */\n" + PROTOTYPES + "\n" + ANCHOR, 1)
    return source.replace(
        FIELD, FIELD + "    .begin_sim_frame    = &ur_baldosa_hd_begin_sim_frame,\n"
        + "    .draw_frame         = &ur_baldosa_hd_draw_frame,\n"
        + "    .presentation_scale = &ur_baldosa_hd_presentation_scale,\n", 1)


def patch_cmake(source: str, ur_root: Path) -> str:
    if MARK in source:
        return source
    if "UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE" not in source:
        raise ValueError("Stage the existing observer first, keeping baseline API stable")
    files = [
        ur_root / "tools/baldosa_native_racer_presentation.cpp",
        ur_root / "native/presentation/racer_hd_presenter.cpp",
        ur_root / "native/presentation/racer_oam_placement.cpp",
        ur_root / "native/product/presentation_density_compositor.cpp",
    ]
    for f in files:
        if not f.is_file():
            raise ValueError(f"Missing real UR presentation implementation: {f}")
    inc = (ur_root / "native/presentation").resolve().as_posix()
    product_inc = (ur_root / "native/product").resolve().as_posix()
    shim = files[0].resolve().as_posix()
    return source.rstrip() + (
        "\n\n# " + MARK + ": reused UR source-derived presenter, isolated AOT\n"
        + f'set_source_files_properties("{shim}" PROPERTIES INCLUDE_DIRECTORIES "{inc};{product_inc}")\n'
        + "target_sources(UniracersSNESRecomp PRIVATE\n"
        + "".join(f'    "{f.resolve().as_posix()}"\n' for f in files)
        + ")\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--ur-root", type=Path, required=True)
    args = ap.parse_args()
    game, root = args.game.resolve(), args.ur_root.resolve()
    for file, patch in [
        (game / "src/main.c", patch_main),
        (game / "CMakeLists.txt", lambda s: patch_cmake(s, root)),
    ]:
        before = file.read_text(encoding="utf-8")
        after = patch(before)
        if after != before:
            file.write_text(after, encoding="utf-8")
        print(f"{file}: {'staged' if after != before else 'already staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Add a read-only original PPU witness to exactly one pinned Windows guest.

Applies after the existing Baldosa Modern native pause adapter, never in a
shared SNESRecomp checkout or cross-title core. The host has an existing
end_sim_frame hook called AFTER original PPU draw; returning no frame and
writing no guest state cannot modify the original renderer, Modern frontend
or the SNES input/clock. Source snapshots remain opt-in and manual QA only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_WINDOWS_ORIGINAL_PPU_CAPTURE"
MAIN_ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"
STATS_ANCHOR = "    .after_run_frame     = &ur_baldosa_product_after_run_frame,\n"
DECL = (
    "/* " + MARK + ": read-only original source on completed raster. */\n"
    "extern void ur_qa08_windows_capture_original_source("
    "const uint8_t *field, unsigned number);\n"
)
SOURCE = "tools/baldosa_qa08_windows_original_capture.cpp"


def patch_game_main(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 1 or source.count(
            "    .end_sim_frame      = &ur_qa08_windows_capture_original_source,\n"
        ) != 1:
            raise ValueError("incomplete/tampered original PPU observer")
        return source
    if ("UR_BALDOSA_NATIVE_PRODUCT_PAUSE" not in source
        or source.count(MAIN_ANCHOR) != 1
        or source.count(STATS_ANCHOR) != 1
        or ".end_sim_frame" in source):
        raise ValueError("unknown pinned Windows Modern guest graphics boundary")
    return (source.replace(MAIN_ANCHOR, DECL + "\n" + MAIN_ANCHOR, 1)
                  .replace(STATS_ANCHOR, STATS_ANCHOR +
                      "    .end_sim_frame      = &ur_qa08_windows_capture_original_source,\n", 1))


def patch_game_cmake(source: str, root: Path) -> str:
    if MARK in source:
        if source.count(MARK) != 1 or source.count(SOURCE) != 1:
            raise ValueError("incomplete/tampered QA-08 witness CMake")
        return source
    if ("UR_BALDOSA_NATIVE_PRODUCT_PAUSE" not in source or
        "target_sources(UniracersSNESRecomp PRIVATE" not in source):
        raise ValueError("pinned Windows native host sources not staged")
    observer = (root / SOURCE).resolve()
    if not observer.is_file():
        raise ValueError("read-only source observer implementation absent")
    return source.rstrip() + (
        "\n\n# " + MARK + ": opt-in post-PPU capture, NEVER a compositor\n"
        f'target_sources(UniracersSNESRecomp PRIVATE "{observer.as_posix()}")\n'
    )


def plan(game: Path, root: Path) -> list[tuple[Path, str, str]]:
    game, root = game.resolve(), root.resolve()
    changes = [
        (game / "src/main.c", patch_game_main),
        (game / "CMakeLists.txt", lambda text: patch_game_cmake(text, root)),
    ]
    result = []
    for path, transform in changes:
        old = path.read_text(encoding="utf-8")
        result.append((path, old, transform(old)))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", required=True, type=Path)
    ap.add_argument("--ur-root", required=True, type=Path)
    ap.add_argument("--apply-candidate", action="store_true")
    args = ap.parse_args()
    try:
        edits = plan(args.game, args.ur_root)
        for path, old, new in edits:
            if args.apply_candidate and old != new:
                path.write_text(new, encoding="utf-8")
            print(f"QA08_WIN_PPU_OBSERVER file={path} "
                  f"changed={int(new != old)} apply={int(args.apply_candidate)}")
    except (ValueError, OSError) as exc:
        ap.exit(2, f"QA08_WIN_PPU_OBSERVER_REJECTED: {exc}\n")


if __name__ == "__main__":
    main()

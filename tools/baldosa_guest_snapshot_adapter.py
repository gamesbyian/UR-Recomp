#!/usr/bin/env python3
"""Stage our existing racer guest-state reader inside Baldosa's native host.

This is a disposable build-time integration experiment, not a generated-C
rewrite and not a second gameplay authority. The guest source is unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ENTRY_ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"
FIELD_ANCHOR = "    .game_info           = &kGameInfo,\n"
MARKER = "# UR_BALDOSA_RACER_SNAPSHOT_ADAPTER"


def patched_main(source: str) -> str:
    if MARKER in source:
        return source
    if source.count(ENTRY_ANCHOR) != 1 or source.count(FIELD_ANCHOR) != 1:
        raise ValueError("pinned Baldosa host API anchors changed")
    source = source.replace(
        ENTRY_ANCHOR,
        "/* " + MARKER + " */\n"
        "void ur_baldosa_racer_snapshot_after_frame("
        "const SnesDesktopHostFrameStats *stats);\n\n"
        + ENTRY_ANCHOR, 1
    )
    return source.replace(
        FIELD_ANCHOR,
        FIELD_ANCHOR + "    .after_run_frame = &ur_baldosa_racer_snapshot_after_frame,\n",
        1,
    )


def patched_cmake(source: str, project_root: Path) -> str:
    if MARKER in source:
        return source
    if "add_executable(UniracersSNESRecomp" not in source:
        raise ValueError("pinned Baldosa CMake target changed")
    experiment = (project_root / "native" / "experiments" / "baldosa_guest_snapshot_bridge.cpp").resolve()
    presentation = (project_root / "native" / "presentation").resolve()
    paths = (experiment, presentation / "racer_guest_snapshot.cpp",
             presentation / "racer_replacement_selector.cpp")
    for path in paths:
        if not path.is_file():
            raise ValueError(f"missing first-party adapter source {path}")
    return (
        source.rstrip() + "\n\n# " + MARKER + "\n"
        "target_include_directories(UniracersSNESRecomp PRIVATE \"" + presentation.as_posix() + "\")\n"
        "target_compile_features(UniracersSNESRecomp PRIVATE cxx_std_17)\n"
        "target_sources(UniracersSNESRecomp PRIVATE\n"
        + "".join(f'    "{path.as_posix()}"\n' for path in paths)
        + ")\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, type=Path)
    ap.add_argument("--repo-root", required=True, type=Path)
    args = ap.parse_args()
    source = args.game / "src/main.c"
    cmake = args.game / "CMakeLists.txt"
    main_before, cmake_before = source.read_text(), cmake.read_text()
    new_main = patched_main(main_before)
    new_cmake = patched_cmake(cmake_before, args.repo_root)
    source.write_text(new_main)
    cmake.write_text(new_cmake)
    print("First-party racer WRAM observer staged on Baldosa after_run_frame; native guest C unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

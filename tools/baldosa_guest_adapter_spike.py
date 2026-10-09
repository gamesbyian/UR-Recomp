#!/usr/bin/env python3
"""Apply a deliberately read-only UR-Recomp racer snapshot bridge to an isolated Baldosa build.

Never patch source inside UR-Recomp production build; this stages three UR-Recomp
translation units into Ema's exact pinned title via external CMake source refs.
The injection is intentionally guarded and idempotent. Native AOT game remains
its upstream version for the first baseline run.
"""
from __future__ import annotations

import argparse
from pathlib import Path

HOST_MARK = "UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE"
PROTOTYPE = (
    "extern void ur_baldosa_guest_snapshot_after_run_frame("
    "const SnesDesktopHostFrameStats *stats);\n"
)
FIELD = "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
GAME_FIELD = "    .game_info           = &kGameInfo,\n"
BEFORE_HOST = "static const SnesDesktopHostGame kGameHost = {\n"


def patch_main(text: str) -> str:
    if HOST_MARK in text:
        return text
    if text.count(BEFORE_HOST) != 1 or text.count(GAME_FIELD) != 1:
        raise ValueError("Unexpected Baldosa host; do not splice against an unknown revision")
    return (
        text.replace(BEFORE_HOST, "/* " + HOST_MARK + " */\n" + PROTOTYPE + "\n" + BEFORE_HOST, 1)
        .replace(GAME_FIELD, GAME_FIELD + FIELD, 1)
    )


def patch_cmake(text: str, repo_root: Path) -> str:
    if HOST_MARK in text:
        return text
    needle = "snesrecomp_target_desktop_host(UniracersSNESRecomp)"
    if text.count(needle) != 1:
        raise ValueError("Expected desktop target missing in Baldosa pinned CMake")
    root = repo_root.resolve()
    cpp = root / "tools" / "baldosa_guest_snapshot_probe.cpp"
    src = root / "native" / "presentation"
    appendix = (
        "\n# " + HOST_MARK + ": external read-only integration experiment\n"
        f'target_include_directories(UniracersSNESRecomp PRIVATE "{src.as_posix()}")\n'
        "target_sources(UniracersSNESRecomp PRIVATE\n"
        f'    "{cpp.as_posix()}"\n'
        f'    "{(src / "racer_guest_snapshot.cpp").as_posix()}"\n'
        f'    "{(src / "racer_replacement_selector.cpp").as_posix()}"\n'
        ")\n"
    )
    return text + appendix


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game", required=True, type=Path)
    p.add_argument("--ur-root", required=True, type=Path)
    args = p.parse_args()
    game = args.game.resolve()
    for file, patch in ((game / "src" / "main.c", patch_main),
                        (game / "CMakeLists.txt", lambda text: patch_cmake(text, args.ur_root))):
        before = file.read_text(encoding="utf-8")
        after = patch(before)
        if after == before:
            print(f"already staged: {file}")
        else:
            file.write_text(after, encoding="utf-8")
            print(f"staged: {file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

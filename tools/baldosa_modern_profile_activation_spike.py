#!/usr/bin/env python3
"""Stage the existing Modern active-profile pre-SRAM callback in pinned Baldosa.

Run only AFTER baldosa_product_pause_spike.py and
baldosa_modern_user_data_spike.py.  This uses the upstream title's own
after_config callback, already invoked before the native guest reads SRAM.
No second desktop host, input loop, guest-state writes, or save formats.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_MODERN_PROFILE_ACTIVATION"
MAIN_HOST = "static const SnesDesktopHostGame kGameHost = {\n"
MAIN_PAUSE = "    .after_run_frame     = &ur_baldosa_product_after_run_frame,\n"
NATIVE_MARK = "UR_BALDOSA_NATIVE_PRODUCT_PAUSE"
ROOT_MARK = "UR_BALDOSA_MODERN_USER_DATA_ROOT"
SOURCES = (
    "host_product_store.cpp",
    "host_profile_runtime.cpp",
    "host_profile_store.cpp",
    "host_profile_state.cpp",
    "host_profile_catalog.cpp",
    "modern_racer_identity.cpp",
)


def patch_main(source: str) -> str:
    if MARK in source:
        return source
    if NATIVE_MARK not in source:
        raise ValueError("Pinned native Modern pause seam must already be staged")
    if source.count(MAIN_HOST) != 1 or source.count(MAIN_PAUSE) != 1:
        raise ValueError("Pinned host descriptor changed; no profile wiring")
    source = source.replace(
        MAIN_HOST,
        "/* " + MARK + ": existing Modern active profile, before guest SRAM. */\n"
        "extern int ur_baldosa_modern_try_activate_profile(void);\n"
        "extern void ur_baldosa_modern_profile_before_run_frame(void);\n"
        "static void ur_baldosa_modern_profile_after_config(void) {\n"
        "    if (!ur_baldosa_modern_try_activate_profile()) {\n"
        "        fprintf(stderr, \"UR-STARTUP-SAVE-ROOT: selected Modern profile rejected\\n\");\n"
        "        exit(7);\n"
        "    }\n"
        "}\n" + MAIN_HOST,
        1)
    # Title main.c already includes stdio? Include both here for exit/fprintf,
    # using one guarded hook marker rather than changing the host runtime.
    source = "#include <stdio.h>\n#include <stdlib.h>\n" + source
    return source.replace(
        MAIN_PAUSE,
        "    .after_config        = &ur_baldosa_modern_profile_after_config,\n"
        "    .before_run_frame    = &ur_baldosa_modern_profile_before_run_frame,\n"
        + MAIN_PAUSE, 1)


def patch_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if NATIVE_MARK not in source:
        raise ValueError("Pinned Modern native CMake hook must already be staged")
    bridge = (root / "tools/baldosa_modern_profile_activation.cpp").resolve()
    product = (root / "native/product").resolve()
    selected = [bridge, *(product / s for s in SOURCES)]
    for path in selected:
        if not path.is_file():
            raise ValueError(f"Missing established Modern product component: {path}")
    args = " ".join(f'"{p.as_posix()}"' for p in selected)
    fixture = (root / "tools/baldosa_modern_profile_native_fixture.cpp").resolve()
    if not fixture.is_file():
        raise ValueError(f"Missing real Modern profile fixture builder: {fixture}")
    fixture_args = " ".join(f'"{p.as_posix()}"' for p in (
        fixture,
        product / "output_resolution_policy.cpp",
        product / "host_product_state.cpp",
        *(product / s for s in SOURCES),
    ))
    return source.rstrip() + (
        "\n\n# " + MARK + ": typed read-only Modern state and profile SRAM root\n"
        "target_sources(UniracersSNESRecomp PRIVATE " + args + ")\n"
        # Test-only executable, not part of the shipping game target. Uses
        # the SAME Modern product codecs as the real Windows frontend.
        "add_executable(ur-baldosa-modern-profile-fixture " + fixture_args + ")\n"
        f'target_include_directories(ur-baldosa-modern-profile-fixture PRIVATE "{product.as_posix()}")\n")


def plan(game: Path, root: Path):
    files = (
        (game / "src/main.c", patch_main),
        (game / "CMakeLists.txt", lambda s: patch_cmake(s, root)),
    )
    pending = []
    for path, transform in files:
        before = path.read_text(encoding="utf-8")
        pending.append((path, before, transform(before)))
    return pending


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--ur-root", type=Path, required=True)
    args = ap.parse_args()
    for path, before, after in plan(args.game.resolve(), args.ur_root.resolve()):
        if after != before:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if after == before else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

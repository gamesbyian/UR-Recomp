#!/usr/bin/env python3
"""Wire the durable modern Uniracers product host into a generated project."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_ANCHOR = '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
FIELD_ANCHOR = '    .game_info           = &kGameInfo,\n'


def patch_main_text(source: str) -> str:
    if "ur_uniracers_modern_after_run_frame" in source:
        return source
    if INCLUDE_ANCHOR not in source:
        raise ValueError("generated host include anchor not found")
    if FIELD_ANCHOR not in source:
        raise ValueError("generated host game_info field not found")

    source = source.replace(
        INCLUDE_ANCHOR,
        INCLUDE_ANCHOR + '#include "uniracers_modern_host.h"\n',
        1,
    )
    return source.replace(
        FIELD_ANCHOR,
        FIELD_ANCHOR
        + "    .after_run_frame       = &ur_uniracers_modern_after_run_frame,\n"
        + "    .system_key_down       = &ur_uniracers_modern_system_key_down,\n"
        + "    .system_gamepad_button = &ur_uniracers_modern_system_gamepad_button,\n"
        + "    .system_overlay         = &ur_uniracers_modern_system_overlay,\n",
        1,
    )


def patch_cmake_text(source: str, product_root: Path = ROOT) -> str:
    marker = "# UR_MODERN_PRODUCT_HOST"
    if marker in source:
        return source

    match = re.search(r"add_executable\(([^\s\)]+)", source)
    if not match:
        raise ValueError("generated CMake target anchor not found")
    target = match.group(1)
    product_dir = (product_root / "native" / "product").as_posix()
    title_dir = (product_root / "native" / "title").as_posix()
    product_sources = [
        "host_product_state.cpp",
        "host_product_store.cpp",
        "session_control.cpp",
        "session_runtime_adapter.cpp",
        "race_restart_anchor.cpp",
        "race_restart_lifecycle.cpp",
        "modern_session_runtime.cpp",
        "modern_session_c_api.cpp",
        "modern_pause_menu.cpp",
        "modern_pause_input.cpp",
        "uniracers_modern_host.cpp",
    ]
    source_lines = "\n".join(
        f'    "{product_dir}/{name}"' for name in product_sources
    )

    return (
        source.rstrip()
        + "\n\n"
        + marker
        + "\n"
        + f'target_include_directories({target} PRIVATE "{product_dir}" "{title_dir}")\n'
        + f"target_sources({target} PRIVATE\n"
        + source_lines
        + "\n"
        + f'    "{title_dir}/uniracers_restart_policy.cpp"\n'
        + ")\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("main_c", type=Path)
    parser.add_argument("--cmake", type=Path, required=True)
    args = parser.parse_args()

    args.main_c.write_text(
        patch_main_text(args.main_c.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    args.cmake.write_text(
        patch_cmake_text(args.cmake.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

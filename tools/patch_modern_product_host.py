#!/usr/bin/env python3
"""Wire the durable modern Uniracers product host into a generated project."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_ANCHOR = '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
FIELD_ANCHOR = '    .game_info           = &kGameInfo,\n'
GAME_INFO_ANCHOR = 'const RtlGameInfo kGameInfo = {\n'
SAVE_PREFIX_ANCHOR = '    .save_name_prefix = "save",\n'


def patch_main_text(source: str) -> str:
    if "ur_uniracers_modern_compute_viewport" in source:
        return source

    widescreen_fields = (
        "    .native_widescreen      = 1,\n"
        "    .native_widescreen_enabled = &ur_uniracers_modern_native_widescreen_enabled,\n"
        "    .prepare_frame          = &ur_uniracers_modern_prepare_frame,\n"
        "    .compute_viewport       = &ur_uniracers_modern_compute_viewport,\n"
    )

    if "ur_uniracers_modern_presentation_hz" in source:
        anchor = (
            "    .presentation_hz        = &ur_uniracers_modern_presentation_hz,\n"
        )
        if anchor not in source:
            raise ValueError("existing modern host presentation field not found")
        return source.replace(anchor, anchor + widescreen_fields, 1)

    if "ur_uniracers_modern_after_run_frame" in source:
        overlay_anchor = (
            "    .system_overlay         = &ur_uniracers_modern_system_overlay,\n"
        )
        if overlay_anchor not in source:
            raise ValueError("existing modern host overlay field not found")
        return source.replace(
            overlay_anchor,
            overlay_anchor
            + "    .presentation_hz        = &ur_uniracers_modern_presentation_hz,\n"
            + widescreen_fields,
            1,
        )
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
        + "    .system_overlay         = &ur_uniracers_modern_system_overlay,\n"
        + "    .presentation_hz        = &ur_uniracers_modern_presentation_hz,\n"
        + widescreen_fields,
        1,
    )


def patch_game_rtl_text(source: str) -> str:
    """Wire the scaffold's existing title session-reset hook into RtlGameInfo."""
    if ".session_reset = &GameSessionReset" in source:
        return source
    if GAME_INFO_ANCHOR not in source or SAVE_PREFIX_ANCHOR not in source:
        raise ValueError("generated game_rtl session-reset anchors not found")
    source = source.replace(
        GAME_INFO_ANCHOR,
        "void GameSessionReset(void);\n\n" + GAME_INFO_ANCHOR,
        1,
    )
    return source.replace(
        SAVE_PREFIX_ANCHOR,
        SAVE_PREFIX_ANCHOR + "    .session_reset = &GameSessionReset,\n",
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
        "output_resolution_policy.cpp",
        "output_resolution_runtime_policy.cpp",
        "widescreen_output_composition.cpp",
        "host_product_state.cpp",
        "host_product_store.cpp",
        "host_profile_state.cpp",
        "host_profile_store.cpp",
        "completed_run_record.cpp",
        "completed_run_capture.cpp",
        "completed_run_comparison.cpp",
        "session_control.cpp",
        "session_runtime_adapter.cpp",
        "race_restart_anchor.cpp",
        "race_restart_lifecycle.cpp",
        "modern_session_runtime.cpp",
        "modern_session_c_api.cpp",
        "modern_pause_menu.cpp",
        "modern_pause_input.cpp",
        "modern_options_menu.cpp",
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
        + f'    "{title_dir}/uniracers_course_identity.cpp"\n'
        + f'    "{title_dir}/uniracers_run_data.cpp"\n'
        + ")\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("main_c", type=Path)
    parser.add_argument("--game-rtl", type=Path, required=True)
    parser.add_argument("--cmake", type=Path, required=True)
    args = parser.parse_args()

    args.main_c.write_text(
        patch_main_text(args.main_c.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    args.game_rtl.write_text(
        patch_game_rtl_text(args.game_rtl.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    args.cmake.write_text(
        patch_cmake_text(args.cmake.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

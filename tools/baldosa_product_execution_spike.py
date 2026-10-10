#!/usr/bin/env python3
"""Stage the Modern HUMAN input hook onto the proven pinned Baldosa host.

A deliberately small framework delta in a disposable Baldosa checkout:
partition human input BEFORE the scripted/debug words are OR'd in. The
existing whole-frame lockstep callback remains untouched and ordinary SDL
run-ahead retains its original ownership. No guest, UI or renderer rewrite.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_PRODUCT_INPUT_SEAM"
OBSERVER = "UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE"
FIELD = "    .num_players         = 2,\n"
PROTO = ("extern uint32_t ur_baldosa_product_filter_human_frame_inputs("
         "uint32_t word, unsigned frame);\n")
ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"

# Exact pinned Ema host anchors; fail if upstream changes them.
HEADER_ANCHOR = "  uint32_t (*filter_frame_inputs)(uint32_t word, unsigned frame);\n"
SCRIPT_ANCHOR = "    inputs |= TickScript();\n"
WORD_ANCHOR = ("      uint32 word = inputs | GetActiveControllers() "
               "| debug_server_get_controller_active_mask();\n")
FRAME_STATS_ANCHOR = (
    "  int audio_output_rate;     /* device rate, 0 when audio is disabled */\n")
NATIVE_RUNAHEAD_ANCHOR = "    bool runahead_captured = false;\n"
GUEST_FRAME_STATS_ANCHOR = "        .guest_seconds = now - guest_start,\n"
NATIVE_FILTER_ANCHOR = (
    "        word = game->filter_frame_inputs(word, filtered_frames++);\n")


def patch_main(source: str) -> str:
    if MARK in source:
        return source
    if OBSERVER not in source:
        raise ValueError("First stage the verified Baldosa guest snapshot bridge")
    if source.count(ANCHOR) != 1 or source.count(FIELD) != 1:
        raise ValueError("Unrecognized Baldosa native host layout")
    replacement = (FIELD +
        "#ifndef __EMSCRIPTEN__\n"
        "    /* " + MARK + " */\n"
        "    .filter_human_frame_inputs = "
        "&ur_baldosa_product_filter_human_frame_inputs,\n"
        "#endif\n")
    return (source.replace(ANCHOR, PROTO + "\n" + ANCHOR, 1)
                  .replace(FIELD, replacement, 1))


def patch_framework_header(source: str) -> str:
    if MARK in source:
        return source
    if source.count(HEADER_ANCHOR) != 1 or source.count(FRAME_STATS_ANCHOR) != 1:
        raise ValueError("Pinned Baldosa host descriptor/frame stats not recognized")
    addition = (HEADER_ANCHOR +
        "  /* " + MARK + ": mapped HUMAN input only, before scripts/debug;\n"
        "   * optional; absence retains the exact upstream input behavior. */\n"
        "  uint32_t (*filter_human_frame_inputs)(uint32_t word, unsigned frame);\n")
    stats = (FRAME_STATS_ANCHOR +
        "  /* " + MARK + ": actual mapped guest word for completed frame;\n"
        "   * not a second execution loop or replay input generator. */\n"
        "  uint32_t resolved_controller_word;\n")
    return source.replace(HEADER_ANCHOR, addition, 1).replace(
        FRAME_STATS_ANCHOR, stats, 1)


def patch_framework_source(source: str) -> str:
    if MARK in source:
        return source
    required = (
        SCRIPT_ANCHOR, WORD_ANCHOR, NATIVE_RUNAHEAD_ANCHOR,
        GUEST_FRAME_STATS_ANCHOR, NATIVE_FILTER_ANCHOR,
    )
    if any(source.count(anchor) != 1 for anchor in required):
        raise ValueError("Pinned Baldosa input merge/frame ownership boundaries not recognized")

    # Existing mapped-human-only filter remains before script/debug, and the
    # existing RtlRunFrame/optional run-ahead path is never replaced.
    start = (
        "    /* " + MARK + ": one mapped human-only sample. */\n"
        "    inputs |= GetActiveControllers();\n"
        "    if (game->filter_human_frame_inputs)\n"
        "      inputs = game->filter_human_frame_inputs(inputs, frameCtr);\n"
        + SCRIPT_ANCHOR)
    source = source.replace(SCRIPT_ANCHOR, start, 1)
    source = source.replace(
        NATIVE_RUNAHEAD_ANCHOR,
        "    /* " + MARK + ": source-visible input for this completed guest frame. */\n"
        "    uint32 resolved_guest_word = 0;\n" + NATIVE_RUNAHEAD_ANCHOR,
        1)
    source = source.replace(
        WORD_ANCHOR,
        "      uint32 word = inputs | debug_server_get_controller_active_mask();\n"
        "      resolved_guest_word = word;\n",
        1)
    source = source.replace(
        NATIVE_FILTER_ANCHOR,
        NATIVE_FILTER_ANCHOR + "        resolved_guest_word = word;\n",
        1)
    return source.replace(
        GUEST_FRAME_STATS_ANCHOR,
        GUEST_FRAME_STATS_ANCHOR +
        "        .resolved_controller_word = resolved_guest_word,\n",
        1)


def patch_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if OBSERVER not in source:
        raise ValueError("First stage verified read-only observer sources")
    cpp = (root / "tools/baldosa_native_product_execution.cpp").resolve()
    inc = (root / "native/product").resolve()
    if not cpp.is_file() or not (inc / "baldosa_execution_backend.hpp").is_file():
        raise ValueError("Missing project-owned product C ABI bridge")
    return source.rstrip() + (
        "\n\n# " + MARK + ": human-only input hook, no second runtime\n"
        + f'set_source_files_properties("{cpp.as_posix()}" PROPERTIES '
          f'INCLUDE_DIRECTORIES "{inc.as_posix()}")\n'
        + f'target_sources(UniracersSNESRecomp PRIVATE "{cpp.as_posix()}")\n'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--ur-root", type=Path, required=True)
    args = ap.parse_args()
    root, game = args.ur_root.resolve(), args.game.resolve()
    changes = [
        (game / "src/main.c", patch_main),
        (game / "CMakeLists.txt", lambda s: patch_cmake(s, root)),
        (game / "snesrecomp/runner/src/desktop/host_main.h",
         patch_framework_header),
        (game / "snesrecomp/runner/src/desktop/host_main.c",
         patch_framework_source),
    ]
    # Validate ALL four source transformations before writing any. A bad
    # framework pin must not leave a partially staged checkout.
    pending = []
    for path, apply in changes:
        before = path.read_text(encoding="utf-8")
        pending.append((path, before, apply(before)))
    for path, before, after in pending:
        if after != before:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Opt-in exact 37-frame Original source PPU capture in disposable native host.

This changes only the *source capture decision* in a disposable CI checkout
of the pinned first-party host C++ file. The native PPU, game, course,
widened world, output, ROM and generated 65816 code are never mutated.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_AUTHENTIC_37FRAME_SOURCE_CAPTURE"
ANCHOR = '    const char* live = std::getenv("UR_BALDOSA_FIXED_ORIGINAL_SOURCE_LATE_FRAME");'
DECISION = """    if (!matches(primary, g_frame) &&
        !matches(extra, g_frame) &&
        !matches(live, g_frame))
        return;"""
NEW_DECISION = """    /* UR_QA08_AUTHENTIC_37FRAME_SOURCE_CAPTURE: diagnostic, never shipping.
     * Original Snes9x callback 2188..2224 corresponds to native guest
     * 2189..2225. Preserve literal source coordinates and 7:6 PAR. */
    const char* qa08_window = std::getenv("UR_QA08_NATIVE_ORIGINAL_WINDOW37");
    const bool qa08_source_window =
        qa08_window && std::strcmp(qa08_window, "source-window-37") == 0 &&
        g_frame >= 2189u && g_frame <= 2225u;
    if (!qa08_source_window &&
        !matches(primary, g_frame) &&
        !matches(extra, g_frame) &&
        !matches(live, g_frame))
        return;"""


def patch(source: str) -> str:
    if MARK in source:
        raise ValueError("original native source 37-frame patch already present")
    if (source.count(ANCHOR) != 1 or source.count(DECISION) != 1
        or "void capture_fixed_original_source(" not in source
        or '"ur-baldosa-original-source"' not in source
        or 'frame_w' not in source or "g_frame = number;" not in source):
        raise ValueError("pinned original source capture presenter changed")
    # Only the source capture decision and completed-simulation diagnostic
    # callback are staged. Neither replaces the PPU buffer or modifies input.

    callback_anchor = 'extern "C" int ur_baldosa_hd_presentation_scale(void) {'
    if source.count(callback_anchor) != 1:
        raise ValueError("pinned host source callback ABI changed")
    source = source.replace(DECISION, NEW_DECISION, 1)
    callback = """/* UR_QA08_AUTHENTIC_37FRAME_SOURCE_CAPTURE: per simulated frame
 * before sparse presentation; never modifies native PPU or guest. */
extern "C" void ur_qa08_original_source_37_end_sim_frame(
    const std::uint8_t* field, unsigned frame) {
    const char* arm = std::getenv("UR_QA08_NATIVE_ORIGINAL_WINDOW37");
    if (arm && std::strcmp(arm, "source-window-37") == 0 &&
        field && g_frame == frame && frame >= 2189u && frame <= 2225u)
        capture_fixed_original_source(field, 256, 224);
}

"""
    return source.replace(callback_anchor, callback + callback_anchor, 1)


def patch_host(source: str) -> str:
    """Stage single read-only completed-simulation PPU capture host callback."""
    if MARK in source:
        raise ValueError("native host 37-frame source hook already present")
    anchor = "static const SnesDesktopHostGame kGameHost = {\n"
    begin = "    .begin_sim_frame    = &ur_baldosa_hd_begin_sim_frame,\n"
    if source.count(anchor) != 1 or source.count(begin) != 1:
        raise ValueError("pinned native host simulation completion ABI changed")
    declaration = (
        "/* " + MARK + ": read-only completed true guest frame PPU source. */\n"
        "extern void ur_qa08_original_source_37_end_sim_frame("
        "const uint8_t*, unsigned);\n"
    )
    source = source.replace(anchor, declaration + anchor, 1)
    return source.replace(
        begin,
        begin + "    .end_sim_frame      = &ur_qa08_original_source_37_end_sim_frame,\n",
        1
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, type=Path,
                   help="Disposable CI checkout source; NOT shipping source")
    p.add_argument("--game", type=Path, help="Disposable pinned Baldosa src/main.c")
    p.add_argument("--apply-experiment", action="store_true")
    args = p.parse_args()
    try:
        if args.apply_experiment and args.game is None:
            raise ValueError("must explicitly stage both PPU callback and host registration")
        old = args.file.read_text(encoding="utf-8")
        result = patch(old)
        if args.game is not None:
            host = args.game.read_text(encoding="utf-8")
            registered = patch_host(host)
        if args.apply_experiment:
            args.file.write_text(result, encoding="utf-8")
            args.game.write_text(registered, encoding="utf-8")
    except (OSError, ValueError) as err:
        p.exit(2, f"QA08_NATIVE_ORIGINAL_WINDOW37_REJECTED {err}\n")
    print(f"QA08_NATIVE_ORIGINAL_WINDOW37_STAGED applied={args.apply_experiment} "
          f"target={args.file} host={args.game}")


if __name__ == "__main__":
    main()

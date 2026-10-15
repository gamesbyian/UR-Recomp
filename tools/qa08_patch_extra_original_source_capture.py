#!/usr/bin/env python3
"""DISPOSABLE read-only native PPU source captures at two moving 2P frames.

No renderer, simulation, image, OAM or presentation change. The original
Snes9x 37-callback source has independently verified that original
callbacks2191/2223 differ markedly from the accepted postGO2207 scene.
The corresponding *candidate* native guest frame numbers 2192/2224
must still be observed, never synthesized or assumed phase-equivalent.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_QA08_ADDITIONAL_ORIGINAL_2P_SOURCE_WINDOWS"
ANCHOR_ENV = (
    '    const char* live = std::getenv("UR_BALDOSA_FIXED_ORIGINAL_SOURCE_LATE_FRAME");\n'
)
ANCHOR_IF = (
    "    if (!matches(primary, g_frame) &&\n"
    "        !matches(extra, g_frame) &&\n"
    "        !matches(live, g_frame))\n"
    "        return;\n"
)
EXTRA_ENV = (
    "    /* UR_QA08_ADDITIONAL_ORIGINAL_2P_SOURCE_WINDOWS:\n"
    "     * Opt-in exact observed moving native source frames ONLY, never\n"
    "     * fabricate a frame or alter the active PPU. */\n"
    '    const char* qa08_a = std::getenv("UR_QA08_ADDITIONAL_SOURCE_FRAME_A");\n'
    '    const char* qa08_b = std::getenv("UR_QA08_ADDITIONAL_SOURCE_FRAME_B");\n'
)
EXTRA_IF = (
    "    if (!matches(primary, g_frame) &&\n"
    "        !matches(extra, g_frame) &&\n"
    "        !matches(live, g_frame) &&\n"
    "        !(g_frame == 2192 && matches(qa08_a, g_frame)) &&\n"
    "        !(g_frame == 2224 && matches(qa08_b, g_frame)))\n"
    "        return;\n"
)


def patch_source(source: str) -> str:
    if MARK in source:
        raise ValueError("additional original PPU source capture already staged")
    start = source.find("void capture_fixed_original_source(")
    end = source.find("\n// Compare the actual composited raster", start)
    observer = source[start:end] if start >= 0 and end > start else ""
    if (source.count("void capture_fixed_original_source(") != 1
        or observer.count(ANCHOR_ENV) != 1
        or observer.count(ANCHOR_IF) != 1
        or observer.count("const bool saved = save_presented_pam(") != 1
        or "if (!field || width != 256 || height != 224" not in observer
        or "ur-baldosa-original-source" not in observer):
        raise ValueError("pinned native Original-source observer changed")
    patched = source.replace(ANCHOR_ENV, ANCHOR_ENV + EXTRA_ENV, 1)
    patched = patched.replace(ANCHOR_IF, EXTRA_IF, 1)
    return patched


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--apply-experiment", action="store_true")
    args = p.parse_args()
    try:
        before = args.source.read_text(encoding="utf-8")
        after = patch_source(before)
        if args.apply_experiment:
            args.source.write_text(after, encoding="utf-8")
    except (ValueError, OSError) as exc:
        p.exit(2, f"QA08_MOVING_NATIVE_SOURCE_CAPTURE_REJECTED {exc}\n")
    print("QA08_MOVING_SOURCE_CAPTURE_STAGED "
          f"applied={args.apply_experiment} file={args.source} "
          "guest_and_renderer_unchanged=true native_frames_not_yet_captured=true")


if __name__ == "__main__":
    main()

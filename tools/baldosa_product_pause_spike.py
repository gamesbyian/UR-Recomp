#!/usr/bin/env python3
"""Stage a real, acknowledged Baldosa guest-frame pause/resume host seam.

Apply only after baldosa_guest_adapter_spike.py and
baldosa_product_execution_spike.py (and optional renderer). Changes are
validated as a group before writing to a disposable pinned Baldosa checkout.
The host keeps its existing SDL event loop, renderer, audio and guest runner.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_NATIVE_PRODUCT_PAUSE"
REQUIRED = "UR_BALDOSA_PRODUCT_INPUT_SEAM"

# The descriptor addition sits BELOW the existing input hook to preserve ABI
# ownership and the established web lockstep field.
HEADER = "  uint32_t (*filter_human_frame_inputs)(uint32_t word, unsigned frame);\n"
PUBLIC = "int snesrecomp_desktop_frame_width(void);\n"
GLOBAL = "static uint8 g_paused, g_turbo, g_cursor = true;\n"
EVENT = "    if (!running)\n      break;\n    OverlaySelftestPadMainTick(frameCtr);\n"
PAUSE_GATE = ("    if (g_paused && !g_savestate_menu_hotkey && !g_rewind_hotkey &&\n"
              "        !g_open_launcher_hotkey) {\n")
LEGACY_COMMAND = "  if (j == kKeys_Turbo) {\n"
STAT = "    .after_run_frame     = &ur_baldosa_guest_snapshot_after_run_frame,\n"
HOST = "static const SnesDesktopHostGame kGameHost = {\n"


def patch_host_header(source: str) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source or source.count(HEADER) != 1 or source.count(PUBLIC) != 1:
        raise ValueError("Baldosa input host ABI not staged or changed")
    addition = (
        HEADER +
        "  /* " + MARK + ": tick while paused, after SDL events, before guest. */\n"
        "  void (*product_tick)(void);\n")
    public = (
        "/* Title-facing synchronous host control; false means no state change.\n"
        " * No cross-thread invocation; offline only. Query is for acknowledgement. */\n"
        "int snesrecomp_desktop_product_set_paused(int paused);\n"
        "int snesrecomp_desktop_product_is_paused(void);\n"
        + PUBLIC)
    return source.replace(HEADER, addition, 1).replace(PUBLIC, public, 1)


def patch_host_source(source: str) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source or any(source.count(s) != 1 for s in (GLOBAL, EVENT, PAUSE_GATE, LEGACY_COMMAND)):
        raise ValueError("Pinned Baldosa input and SDL event loop changed")
    # g_paused already gates RtlRunFrame, pacing debt and SetAudioPaused.
    # Never invent a second frame loop or freeze by replacing controller words.
    extra = (
        GLOBAL +
        "/* " + MARK + ": only Modern's own pause may be cleared by Modern. */\n"
        "static bool g_product_pause_owned;\n"
        "int snesrecomp_desktop_product_set_paused(int wanted) {\n"
        "  if (g_netplay_session) return 0;\n"
        "  if (wanted) {\n"
        "    if (g_paused && !g_product_pause_owned) return 0;\n"
        "    g_product_pause_owned = true;\n"
        "    g_paused = 1;\n"
        "    return 1;\n"
        "  }\n"
        "  if (!g_product_pause_owned) return 0;\n"
        "  g_paused = 0;\n"
        "  g_product_pause_owned = false;\n"
        "  return 1;\n"
        "}\n"
        "int snesrecomp_desktop_product_is_paused(void) {\n"
        "  return g_product_pause_owned && g_paused;\n"
        "}\n")
    loop = (
        "    if (!running)\n      break;\n"
        "    /* " + MARK + ": title may resume while no guest frames advance. */\n"
        "    if (game->product_tick) game->product_tick();\n"
        "    OverlaySelftestPadMainTick(frameCtr);\n")
    # No legacy guest-state mutation, save/load, or parallel overlay may
    # bypass a Modern-owned pause. Presentation hotkeys remain permissible.
    commands = (
        "  /* " + MARK + ": host-owned pause blocks guest hotkeys. */\n"
        "  if (g_product_pause_owned) {\n"
        "    switch (j) {\n"
        "    case kKeys_Fullscreen: case kKeys_WindowBigger:\n"
        "    case kKeys_WindowSmaller: case kKeys_DisplayPerf:\n"
        "    case kKeys_Screenshot: case kKeys_VolumeUp:\n"
        "    case kKeys_VolumeDown: break;\n"
        "    default: return;\n"
        "    }\n"
        "  }\n"
        + LEGACY_COMMAND)
    gate = (
        "    /* " + MARK + ": never open stock overlays during product pause. */\n"
        "    if (g_product_pause_owned) {\n"
        "      g_savestate_menu_hotkey = g_rewind_hotkey = g_open_launcher_hotkey = 0;\n"
        "      snes_host_clock_reset(&video_clock, MonotonicSeconds(),\n"
        "          g_simulation_hz, presentation_hz);\n"
        "      HostSleepMs(16);\n"
        "      continue;\n"
        "    }\n" + PAUSE_GATE)
    return (source.replace(GLOBAL, extra, 1).replace(EVENT, loop, 1)
                  .replace(LEGACY_COMMAND, commands, 1)
                  .replace(PAUSE_GATE, gate, 1))


def patch_game_main(source: str) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source or source.count(HOST) != 1 or source.count(STAT) != 1:
        raise ValueError("Stage the native human-input observer before pause")
    decl = (
        "/* " + MARK + ": product lifecycle, no guest or Modern UI rewrite */\n"
        "extern void ur_baldosa_product_after_run_frame("
        "const SnesDesktopHostFrameStats *stats);\n"
        "extern void ur_baldosa_product_host_tick(void);\n")
    host = (
        "    .after_run_frame     = &ur_baldosa_product_after_run_frame,\n"
        "    .product_tick        = &ur_baldosa_product_host_tick,\n")
    return source.replace(HOST, decl + HOST, 1).replace(STAT, host, 1)


def patch_game_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source:
        raise ValueError("Stage the native human-input object first")
    path = (root / "tools/baldosa_native_pause_lifecycle.cpp").resolve()
    authority = (root / "tools/baldosa_native_product_pause_authority.cpp").resolve()
    for source in (path, authority):
        if not source.is_file():
            raise ValueError(f"Missing project-owned native pause implementation: {source}")
    return source.rstrip() + (
        "\n\n# " + MARK + ": linked on original pinned game host\n"
        + f'target_sources(UniracersSNESRecomp PRIVATE '
          f'"{path.as_posix()}" "{authority.as_posix()}")\\n'
    )


def plan(game: Path, root: Path):
    changes = [
        (game / "src/main.c", patch_game_main),
        (game / "CMakeLists.txt", lambda s: patch_game_cmake(s, root)),
        (game / "snesrecomp/runner/src/desktop/host_main.h", patch_host_header),
        (game / "snesrecomp/runner/src/desktop/host_main.c", patch_host_source),
    ]
    pending = []
    for path, transform in changes:
        before = path.read_text(encoding="utf-8")
        pending.append((path, before, transform(before)))
    return pending


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--ur-root", type=Path, required=True)
    args = ap.parse_args()
    pending = plan(args.game.resolve(), args.ur_root.resolve())
    for path, old, new in pending:
        if old != new:
            path.write_text(new, encoding="utf-8")
        print(f"{path}: {'already staged' if old == new else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

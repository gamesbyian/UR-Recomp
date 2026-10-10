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
# Existing dependency-free Modern session runtime linked into the SAME AOT
# game, only for its acknowledged native pause lifecycle (no second host).
MODERN_SESSION_SOURCES = (
    "output_resolution_policy.cpp",
    "host_product_state.cpp",
    "session_control.cpp",
    "session_runtime_adapter.cpp",
    "race_restart_anchor.cpp",
    "race_restart_lifecycle.cpp",
    "modern_session_runtime.cpp",
    "modern_session_c_api.cpp",
    "modern_pause_menu.cpp",
    "modern_pause_input.cpp",
)
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
# Pinned Baldosa's own SDL handlers are authoritative. No parallel event loop.
KEY_EVENT = ("static void HandleInput(int keyCode, int keyMod, bool pressed) {\n"
             "  int j = FindCmdForSdlKey(keyCode, (SDL_Keymod)keyMod);\n")
PAD_EVENT = ("static void HandleGamepadInput(GamepadInfo *gi, int button, bool pressed) {\n"
             "  if (!!(gi->modifiers & (1 << button)) == pressed)\n"
             "    return;\n"
             "  gi->modifiers ^= 1 << button;\n")
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
        "  void (*product_tick)(void);\n"
        "  /* Paint into the already frozen host raster, no guest execution. */\n"
        "  int (*product_pause_draw)(uint8_t*, size_t, int, int);\n"
        "  /* Optional Modern physical edge dispatch before guest mapping. */\n"
        "  int (*product_system_key)(int key, int pressed);\n"
        "  int (*product_system_gamepad)(int player, int button, int pressed);\n")
    public = (
        "/* Title-facing synchronous host control; false means no state change.\n"
        " * No cross-thread invocation; offline only. Query is for acknowledgement. */\n"
        "int snesrecomp_desktop_product_set_paused(int paused);\n"
        "int snesrecomp_desktop_product_is_paused(void);\n"
        "unsigned snesrecomp_desktop_product_pause_presentations(void);\n"
        + PUBLIC)
    return source.replace(HEADER, addition, 1).replace(PUBLIC, public, 1)


def patch_host_source(source: str) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source or any(source.count(s) != 1 for s in
                                     (GLOBAL, EVENT, PAUSE_GATE, LEGACY_COMMAND,
                                      KEY_EVENT, PAD_EVENT)):
        raise ValueError("Pinned Baldosa input and SDL event loop changed")
    # g_paused already gates RtlRunFrame, pacing debt and SetAudioPaused.
    # Never invent a second frame loop or freeze by replacing controller words.
    extra = (
        GLOBAL +
        "/* " + MARK + ": only Modern's own pause may be cleared by Modern. */\n"
        "static bool g_product_pause_owned;\n"
        "static unsigned g_product_pause_presentations;\n"
        "unsigned snesrecomp_desktop_product_pause_presentations(void) {\n"
        "  return g_product_pause_presentations;\n"
        "}\n"
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
        "      /* Present exactly the LAST captured frame using the existing\n"
        "       * frozen overlay compositor, never draw_ppu_frame or RtlRunFrame. */\n"
        "      PresentFrozenWithOverlay();\n"
        "      ++g_product_pause_presentations;\n"
        "      snes_host_clock_reset(&video_clock, MonotonicSeconds(),\n"
        "          g_simulation_hz, presentation_hz);\n"
        "      HostSleepMs(16);\n"
        "      continue;\n"
        "    }\n" + PAUSE_GATE)
    key = (
        "static void HandleInput(int keyCode, int keyMod, bool pressed) {\n"
        "  if (g_game->product_system_key &&\n"
        "      g_game->product_system_key(keyCode, pressed ? 1 : 0)) return;\n"
        "  int j = FindCmdForSdlKey(keyCode, (SDL_Keymod)keyMod);\n")
    pad = (
        PAD_EVENT
        + "  if (g_game->product_system_gamepad &&\n"
          "      g_game->product_system_gamepad(gi->index, button, pressed ? 1 : 0)) {\n"
          "    /* Clear legacy command latch on a consumed physical edge. */\n"
          "    gi->last_cmd[button] = 0;\n"
          "    return;\n"
          "  }\n")
    # Reuse the pinned framework's existing frozen renderer. The Modern
    # panel is applied after its frozen source raster and before its OSD.
    frozen_end = "  ComposeOsd(pixel_buffer, pitch, draw_w, draw_h, draw_w >= 512 ? 1 : 2);\\n"
    if source.count(frozen_end) != 1:
        raise ValueError("Pinned frozen-frame compositor moved")
    source = source.replace(frozen_end,
        "  /* " + MARK + ": host Modern pause is ONLY a frozen raster overlay. */\\n"
        "  if (g_product_pause_owned && g_game->product_pause_draw)\\n"
        "    g_game->product_pause_draw(pixel_buffer, (size_t)pitch, draw_w, draw_h);\\n"
        + frozen_end, 1)
    return (source.replace(GLOBAL, extra, 1).replace(EVENT, loop, 1)
                  .replace(LEGACY_COMMAND, commands, 1)
                  .replace(PAUSE_GATE, gate, 1)
                  .replace(KEY_EVENT, key, 1)
                  .replace(PAD_EVENT, pad, 1))


def patch_game_main(source: str) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source or source.count(HOST) != 1 or source.count(STAT) != 1:
        raise ValueError("Stage the native human-input observer before pause")
    decl = (
        "/* " + MARK + ": product lifecycle, no guest or Modern UI rewrite */\n"
        "extern void ur_baldosa_product_after_run_frame("
        "const SnesDesktopHostFrameStats *stats);\n"
        "extern void ur_baldosa_product_host_tick(void);\n"
        "extern int ur_baldosa_product_pause_draw(uint8_t *pixels,\n"
        "    size_t pitch, int width, int height);\n"
        "extern int ur_baldosa_product_system_key(int key, int pressed);\n"
        "extern int ur_baldosa_product_system_gamepad("
        "int player, int button, int pressed);\n")
    host = (
        "    .after_run_frame     = &ur_baldosa_product_after_run_frame,\n"
        "    .product_tick        = &ur_baldosa_product_host_tick,\n"
        "    .product_pause_draw  = &ur_baldosa_product_pause_draw,\n"
        "    .product_system_key  = &ur_baldosa_product_system_key,\n"
        "    .product_system_gamepad = &ur_baldosa_product_system_gamepad,\n")
    return source.replace(HOST, decl + HOST, 1).replace(STAT, host, 1)


def patch_game_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if REQUIRED not in source:
        raise ValueError("Stage the native human-input object first")
    path = (root / "tools/baldosa_native_pause_lifecycle.cpp").resolve()
    authority = (root / "tools/baldosa_native_product_pause_authority.cpp").resolve()
    native_root = (root / "tools/baldosa_native_modern_root.cpp").resolve()
    modern_root = (root / "native/product").resolve()
    modern_sources = [modern_root / name for name in MODERN_SESSION_SOURCES]
    for candidate in (path, authority, native_root, *modern_sources):
        if not candidate.is_file():
            raise ValueError(f"Missing project-owned native pause implementation: {candidate}")
    modern_args = " ".join(f'"{file.as_posix()}"' for file in modern_sources)
    return source.rstrip() + (
        "\n\n# " + MARK + ": same AOT host, real Modern acknowledged pause API\n"
        + f'target_include_directories(UniracersSNESRecomp PRIVATE "{modern_root.as_posix()}")\n'
        + f'target_sources(UniracersSNESRecomp PRIVATE '
          f'"{path.as_posix()}" "{authority.as_posix()}" "{native_root.as_posix()}" {modern_args})\n'
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

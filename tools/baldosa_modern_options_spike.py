#!/usr/bin/env python3
"""Stage the native Modern Options host seam into the pinned Baldosa host.

The visible Modern root owns the Options panel, the controller/keyboard
navigation, the persisted ``HostSettings`` (``options-v1.txt``) and every
message the player sees.  The pinned framework only owns the window, swap
interval and mixer.  This disposable-checkout patch exports exactly four
narrow, bounds-checked C functions over the framework's *existing* machinery:

* ``snesrecomp_desktop_product_get_display`` / ``..._apply_display`` re-use
  the same fullscreen and swap-interval transitions the framework's own
  in-game launcher takes in ``ApplyLiveSettings`` (and, before the window
  exists, simply set the parsed ``g_config`` the window is created from);
* ``snesrecomp_desktop_product_get_volume`` / ``..._set_volume`` re-use
  ``ApplyVolume`` and the framework's own ``[Sound] Volume`` persistence.

No guest, simulation, input or save code is touched.  Only controls that this
host genuinely applies are exported: nothing here is a placeholder.  The
patch is guarded, atomic across files and idempotent.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_MODERN_OPTIONS"

# The text immediately after ``ApplyLiveSettings``: the seam is placed where
# every static it needs (g_config, g_window, VSyncInterval, ApplyVolume,
# g_current_window_scale, ChangeWindowScale ...) is already declared.
ANCHOR = (
    "/* Why a launcher edit cannot be applied to the live session, or NULL. */\n"
)

SEAM = (
    "/* " + MARK + ": narrow product seam over existing framework machinery.\n"
    " * Display: 0 windowed, 1 borderless desktop fullscreen, 2 exclusive.\n"
    " * VSync:   0 off, 1 on, 2 adaptive (the framework's kSnesVSync_*).\n"
    " * Every setter validates its argument and reports whether it applied. */\n"
    "int snesrecomp_desktop_product_get_display(int *fullscreen, int *vsync) {\n"
    "  if (!fullscreen || !vsync) return 0;\n"
    "  *fullscreen = g_config.fullscreen > 2 ? 0 : (int)g_config.fullscreen;\n"
    "  *vsync = g_config.vsync > 2 ? 1 : (int)g_config.vsync;\n"
    "  return 1;\n"
    "}\n"
    "int snesrecomp_desktop_product_apply_display(int fullscreen, int vsync) {\n"
    "  if (fullscreen < 0 || fullscreen > 2 || vsync < 0 || vsync > 2)\n"
    "    return 0;\n"
    "  const uint8 before_fullscreen = g_config.fullscreen;\n"
    "  const uint8 before_vsync = g_config.vsync;\n"
    "  g_config.fullscreen = (uint8)fullscreen;\n"
    "  g_config.vsync = (uint8)vsync;\n"
    "  /* Before the window exists the parsed config is all that is needed. */\n"
    "  if (!g_window) return 1;\n"
    "  const uint32 fs_mask =\n"
    "      SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP | SDL_WINDOW_FULLSCREEN;\n"
    "  if (g_config.fullscreen != before_fullscreen) {\n"
    "    uint32 want = g_config.fullscreen == 2 ? SDL_WINDOW_FULLSCREEN\n"
    "                : g_config.fullscreen      ? SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP : 0;\n"
    "    g_win_flags = (g_win_flags & ~fs_mask) | want;\n"
    "    SDL_SetWindowFullscreen(g_window, want);\n"
    "    g_cursor = want == 0;\n"
    "    snesrecomp_sdl_show_cursor(g_cursor);\n"
    "    g_fullscreen_changed = true;\n"
    "    bool custom_size = g_config.window_width != 0 && g_config.window_height != 0;\n"
    "    if (!custom_size && want == 0) {\n"
    "      if (g_config.window_scale)\n"
    "        g_current_window_scale = IntMin(g_config.window_scale, kMaxWindowScale);\n"
    "      ChangeWindowScale(0);\n"
    "    }\n"
    "  }\n"
    "  if (g_config.vsync != before_vsync) {\n"
    "#ifndef SNESRECOMP_NO_DESKTOP_GL\n"
    "    snesrecomp_opengl_set_vsync(VSyncInterval());\n"
    "#endif\n"
    "    if (g_renderer_funcs.Reconfigure) g_renderer_funcs.Reconfigure();\n"
    "  }\n"
    "  return 1;\n"
    "}\n"
    "int snesrecomp_desktop_product_get_volume(void) {\n"
    "  return g_config.volume < 0 ? 0 : g_config.volume > 100 ? 100 : g_config.volume;\n"
    "}\n"
    "/* Returns the applied percent, or -1 for an out-of-range request. The\n"
    " * framework's own config.ini [Sound] Volume is rewritten immediately so a\n"
    " * hard kill keeps the level the player just heard. */\n"
    "int snesrecomp_desktop_product_set_volume(int percent) {\n"
    "  if (percent < 0 || percent > 100) return -1;\n"
    "  g_config.volume = percent;\n"
    "  ApplyVolume();\n"
    "  g_volume_changed = true;\n"
    "  if (g_active_config_file) WriteConfigFile(g_active_config_file);\n"
    "  return g_config.volume;\n"
    "}\n\n"
)

DECLARATIONS = (
    "int snesrecomp_desktop_product_get_display(int *fullscreen, int *vsync);\n"
    "int snesrecomp_desktop_product_apply_display(int fullscreen, int vsync);\n"
    "int snesrecomp_desktop_product_get_volume(void);\n"
    "int snesrecomp_desktop_product_set_volume(int percent);\n"
)

HEADER_ANCHOR = "int snesrecomp_desktop_frame_width(void);\n"


def once(source: str, needle: str, replacement: str) -> str:
    if source.count(needle) != 1:
        raise ValueError(
            f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    return source.replace(needle, replacement, 1)


def patch_host_main(source: str) -> str:
    if MARK in source:
        return source
    # Every static the seam names must already exist at the insertion point.
    for needed in ("static bool g_volume_changed;",
                   "static bool g_fullscreen_changed;",
                   "static const char *g_active_config_file;",
                   "static void ApplyLiveSettings(const Config *before)",
                   "static int VSyncInterval(void)"):
        if source.count(needed) != 1:
            raise ValueError(
                f"Pinned native Baldosa host diverged: {needed[:100]!r}")
    return once(source, ANCHOR, SEAM + ANCHOR)


def patch_host_header(source: str) -> str:
    if MARK in source:
        return source
    return once(
        source, HEADER_ANCHOR,
        "/* " + MARK + ": host-owned Options seam, see host_main.c. */\n"
        + DECLARATIONS + HEADER_ANCHOR)


def plan(game: Path):
    paths = (
        (game / "snesrecomp/runner/src/desktop/host_main.c", patch_host_main),
        (game / "snesrecomp/runner/src/desktop/host_main.h", patch_host_header),
    )
    pending = []
    # Atomic preparation: verify ALL pinned seams before changing any file.
    for path, change in paths:
        old = path.read_text(encoding="utf-8")
        pending.append((path, old, change(old)))
    return pending


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    args = parser.parse_args()
    for path, before, after in plan(args.game.resolve()):
        if before != after:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

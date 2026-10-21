#!/usr/bin/env python3
"""Stage SDL3 display/window lifecycle hardening into the pinned Baldosa host.

SDL3 removed SDL2's ``SDL_WINDOW_FULLSCREEN_DESKTOP``: a fullscreen window is
borderless desktop fullscreen unless the host first hands it a concrete mode
with ``SDL_SetWindowFullscreenMode``. The pinned host and the Modern Options
seam only ever call ``SDL_SetWindowFullscreen(window, true)``, so the Display
setting's exclusive FULLSCREEN (2) was indistinguishable from BORDERLESS (1)
in the SDL3 Windows product, and switching between them changed nothing.

This disposable-checkout patch adds, using the project-owned
``native/product/display_window_lifecycle_policy.h`` for every decision:

* ``UrApplyFullscreenMode``: before every fullscreen transition (Options
  seam, in-game launcher, the framework's Alt+Enter key and window
  creation) give the window the closest exclusive mode to its display's
  desktop mode for setting 2, or clear it for 1/0. A display that offers no
  such mode makes the Options seam report a refusal, which it already rolls
  back; at start-up the window stays borderless and says so;
* display events, handled in ``HandleDeviceEvent``'s default branch so the
  main, overlay and netplay pumps all see them: an exclusive window that
  lands on another display, or whose desktop mode changes, is re-moded for
  that display; a windowed window left unreachable after a monitor change
  is moved back onto the primary display; after a DPI change a window that
  no longer fits is re-clamped through the framework's ``ChangeWindowScale``;
* ``SNESRECOMP_UR_DISPLAY_LIFECYCLE_ACCEPTANCE=1|exit`` (SDL3 only): drives
  windowed/borderless/exclusive transitions through the real Options seam
  and Alt+Enter command, then an unreachable-window rescue, with fail-closed
  ``UR_DISPLAY_ACCEPT`` lines. Inert unless set.

Guest, simulation, input, timing and pacing are untouched. Must run after
``baldosa_modern_options_spike.py``. Guarded, atomic and idempotent.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SDL_DISPLAY_LIFECYCLE"
POLICY = "native/product/display_window_lifecycle_policy.h"
OPTIONS_MARK = "UR_BALDOSA_MODERN_OPTIONS"

HELPERS_ANCHOR = "static bool HandleDeviceEvent(const SDL_Event *event) {\n"

DEFAULT_BRANCH = (
    "      HandleGamepadInput(gi, raw_buttons[event->jbutton.button],\n"
    "                         event->type == SDL_JOYBUTTONDOWN);\n"
    "    }\n"
    "    return true;\n"
    "  default:\n"
    "    return false;\n"
)
DEFAULT_BRANCH_NEW = DEFAULT_BRANCH.replace(
    "  default:\n    return false;\n",
    "  default:\n"
    "    UrDisplayEvent(event);  /* " + MARK + ": observe, never consume */\n"
    "    return false;\n")

OPTIONS_SDL3 = (
    "    const int fullscreen_applied = SDL_SetWindowFullscreen(g_window, want != 0) ? 1 : 0;\n"
)
OPTIONS_SDL3_NEW = (
    "    /* " + MARK + ": SDL3 needs the mode decided before every transition. */\n"
    "    const int fullscreen_applied = UrApplyFullscreenMode(g_config.fullscreen) &&\n"
    "        SDL_SetWindowFullscreen(g_window, want != 0) ? 1 : 0;\n"
)

LAUNCHER = (
    "    g_win_flags = (g_win_flags & ~fs_mask) | want;\n"
    "    SDL_SetWindowFullscreen(g_window, want);\n"
)
LAUNCHER_NEW = (
    "    g_win_flags = (g_win_flags & ~fs_mask) | want;\n"
    "    UrApplyFullscreenMode(g_config.fullscreen);  /* " + MARK + " */\n"
    "    SDL_SetWindowFullscreen(g_window, want);\n"
)

HOTKEY = (
    "      g_win_flags ^= SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP;\n"
    "      SDL_SetWindowFullscreen(g_window, g_win_flags & SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP);\n"
)
HOTKEY_NEW = (
    "      g_win_flags ^= SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP;\n"
    "      /* " + MARK + ": this key moves between windowed and BORDERLESS;\n"
    "       * never re-enter an exclusive mode left from an earlier setting. */\n"
    "      UrApplyFullscreenMode(1);\n"
    "      SDL_SetWindowFullscreen(g_window, g_win_flags & SNESRECOMP_SDL_WINDOW_FULLSCREEN_DESKTOP);\n"
)

CREATED = "  g_window = window;\n"
CREATED_NEW = (
    "  g_window = window;\n"
    "  /* " + MARK + ": a window created fullscreen is borderless in SDL3. */\n"
    "  if (g_config.fullscreen == 2 && !UrApplyFullscreenMode(2))\n"
    "    printf(\"UR_DISPLAY startup exclusive unavailable; staying borderless\\n\");\n"
)

TICK_ANCHOR = "    OverlaySelftestPadMainTick(frameCtr);\n"
TICK_NEW = TICK_ANCHOR + "    UrDisplayLifecycleAcceptanceTick();  /* " + MARK + " */\n"


def helpers(policy: Path) -> str:
    return (
        "/* " + MARK + ": display/window lifecycle over the existing window.\n"
        " * Decisions live in the project-owned policy header. */\n"
        f'#include "{policy.as_posix()}"\n'
        + HELPERS + ACCEPTANCE + "\n"
    )


HELPERS = r'''static unsigned g_ur_display_reconciles;
/* Give the window an exclusive mode for its current display (setting 2) or
 * clear it (0/1). Returns 0 only when exclusive was wanted and impossible. */
static int UrApplyFullscreenMode(int display_setting) {
#if SNESRECOMP_SDL3
  if (!g_window) return 1;
  if (ur_display_fullscreen_mode_request(display_setting) == UR_FULLSCREEN_MODE_DESKTOP) {
    if (!SDL_SetWindowFullscreenMode(g_window, NULL)) {
      printf("UR_DISPLAY fullscreen_mode=desktop error=%s\n", SDL_GetError());
      return 0;
    }
    return 1;
  }
  const SDL_DisplayID display = SDL_GetDisplayForWindow(g_window);
  const SDL_DisplayMode *desktop = display ? SDL_GetDesktopDisplayMode(display) : NULL;
  SDL_DisplayMode mode;
  if (!desktop ||
      !SDL_GetClosestFullscreenDisplayMode(display, desktop->w, desktop->h,
                                           desktop->refresh_rate,
                                           desktop->pixel_density > 1.0f, &mode) ||
      !SDL_SetWindowFullscreenMode(g_window, &mode)) {
    printf("UR_DISPLAY fullscreen_mode=exclusive_unavailable display=%u error=%s\n",
           (unsigned)display, SDL_GetError());
    return 0;
  }
  printf("UR_DISPLAY fullscreen_mode=exclusive display=%u mode=%dx%d@%.3f\n",
         (unsigned)display, mode.w, mode.h, mode.refresh_rate);
  return 1;
#else
  /* SDL2 keeps distinct desktop/exclusive flags; nothing to decide. */
  (void)display_setting;
  return 1;
#endif
}
#if SNESRECOMP_SDL3
static void UrDisplayReconcile(const char *reason) {
  ++g_ur_display_reconciles;
  const SDL_WindowFlags flags = SDL_GetWindowFlags(g_window);
  if (flags & SDL_WINDOW_FULLSCREEN) {
    if (g_config.fullscreen != 2) return;
    /* Re-mode only when the window's mode no longer belongs to the display
     * it is on, or that display's desktop mode moved. */
    const SDL_DisplayID display = SDL_GetDisplayForWindow(g_window);
    const SDL_DisplayMode *have = SDL_GetWindowFullscreenMode(g_window);
    const SDL_DisplayMode *desktop = display ? SDL_GetDesktopDisplayMode(display) : NULL;
    if (have && desktop && have->displayID == display &&
        have->w == desktop->w && have->h == desktop->h)
      return;
    printf("UR_DISPLAY reconcile reason=%s action=remode display=%u\n", reason,
           (unsigned)display);
    UrApplyFullscreenMode(2);
    return;
  }
  if (flags & (SDL_WINDOW_MINIMIZED | SDL_WINDOW_MAXIMIZED)) return;
  int count = 0;
  SDL_DisplayID *displays = SDL_GetDisplays(&count);
  if (!displays) return;
  UrDisplayRect usable[16];
  int n = 0;
  for (int i = 0; i < count && n < 16; i++) {
    SDL_Rect r;
    if (SDL_GetDisplayUsableBounds(displays[i], &r)) {
      usable[n].x = r.x; usable[n].y = r.y; usable[n].w = r.w; usable[n].h = r.h;
      n++;
    }
  }
  SDL_free(displays);
  UrDisplayRect win;
  SDL_GetWindowPosition(g_window, &win.x, &win.y);
  SDL_GetWindowSize(g_window, &win.w, &win.h);
  if (n > 0 && !ur_display_window_reachable(win, usable, n, 32)) {
    SDL_Rect r;
    if (!SDL_GetDisplayUsableBounds(SDL_GetPrimaryDisplay(), &r)) return;
    UrDisplayRect target = {r.x, r.y, r.w, r.h};
    UrDisplayRect to = ur_display_window_rescue(win, target);
    printf("UR_DISPLAY reconcile reason=%s action=rescue from=%d,%d to=%d,%d size=%dx%d\n",
           reason, win.x, win.y, to.x, to.y, to.w, to.h);
    if (to.w != win.w || to.h != win.h) SDL_SetWindowSize(g_window, to.w, to.h);
    SDL_SetWindowPosition(g_window, to.x, to.y);
    return;
  }
  const bool custom_size = g_config.window_width != 0 && g_config.window_height != 0;
  SDL_Rect r;
  if (!custom_size && SDL_GetDisplayUsableBounds(SDL_GetDisplayForWindow(g_window), &r)) {
    UrDisplayRect here = {r.x, r.y, r.w, r.h};
    UrDisplayRect size_only = {r.x, r.y, win.w, win.h};
    if (!ur_display_window_fits(size_only, here)) {
      printf("UR_DISPLAY reconcile reason=%s action=rescale size=%dx%d usable=%dx%d\n",
             reason, win.w, win.h, r.w, r.h);
      ChangeWindowScale(0);
    }
  }
}
#endif
static void UrDisplayEvent(const SDL_Event *event) {
#if SNESRECOMP_SDL3
  if (!g_window) return;
  switch (event->type) {
  case SDL_EVENT_WINDOW_DISPLAY_CHANGED: UrDisplayReconcile("window_display_changed"); break;
  case SDL_EVENT_WINDOW_DISPLAY_SCALE_CHANGED: UrDisplayReconcile("display_scale_changed"); break;
  case SDL_EVENT_DISPLAY_DESKTOP_MODE_CHANGED: UrDisplayReconcile("desktop_mode_changed"); break;
  case SDL_EVENT_DISPLAY_ADDED: UrDisplayReconcile("display_added"); break;
  case SDL_EVENT_DISPLAY_REMOVED: UrDisplayReconcile("display_removed"); break;
  default: break;
  }
#else
  (void)event;
#endif
}
'''

# Drives the PRODUCT Options seam and the framework's own Alt+Enter command;
# each step waits for the window to settle and is then checked.
ACCEPTANCE = r'''#if SNESRECOMP_SDL3
static int g_ur_disp_step, g_ur_disp_wait, g_ur_disp_failed, g_ur_disp_on = -1;
static int g_ur_disp_vsync = 1, g_ur_disp_original = 0;
static void UrDisplayAcceptExpect(const char *step, bool ok) {
  const SDL_WindowFlags flags = SDL_GetWindowFlags(g_window);
  const SDL_DisplayMode *mode = SDL_GetWindowFullscreenMode(g_window);
  int x = 0, y = 0, w = 0, h = 0;
  SDL_GetWindowPosition(g_window, &x, &y);
  SDL_GetWindowSize(g_window, &w, &h);
  printf("UR_DISPLAY_ACCEPT step=%s pass=%d fullscreen=%d exclusive_mode=%s setting=%d "
         "window=%d,%d,%dx%d\n", step, ok ? 1 : 0, (flags & SDL_WINDOW_FULLSCREEN) ? 1 : 0,
         mode ? "set" : "none", (int)g_config.fullscreen, x, y, w, h);
  if (!ok) g_ur_disp_failed = 1;
}
static bool UrDisplayIsExclusive(void) {
  const SDL_DisplayID display = SDL_GetDisplayForWindow(g_window);
  const SDL_DisplayMode *mode = SDL_GetWindowFullscreenMode(g_window);
  const SDL_DisplayMode *desktop = display ? SDL_GetDesktopDisplayMode(display) : NULL;
  return (SDL_GetWindowFlags(g_window) & SDL_WINDOW_FULLSCREEN) && mode && desktop &&
         mode->w == desktop->w && mode->h == desktop->h;
}
static bool UrDisplayIsBorderless(void) {
  return (SDL_GetWindowFlags(g_window) & SDL_WINDOW_FULLSCREEN) &&
         SDL_GetWindowFullscreenMode(g_window) == NULL;
}
static bool UrDisplayIsWindowed(void) {
  return !(SDL_GetWindowFlags(g_window) & SDL_WINDOW_FULLSCREEN);
}
static bool UrDisplayApply(int setting) {
  return snesrecomp_desktop_product_apply_display(setting, g_ur_disp_vsync) == 1 &&
         g_config.fullscreen == setting;
}
static bool UrDisplayAcceptReachable(void) {
  int count = 0, n = 0;
  UrDisplayRect usable[16], win;
  SDL_DisplayID *displays = SDL_GetDisplays(&count);
  for (int i = 0; displays && i < count && n < 16; i++) {
    SDL_Rect r;
    if (SDL_GetDisplayUsableBounds(displays[i], &r)) {
      usable[n].x = r.x; usable[n].y = r.y; usable[n].w = r.w; usable[n].h = r.h; n++;
    }
  }
  SDL_free(displays);
  SDL_GetWindowPosition(g_window, &win.x, &win.y);
  SDL_GetWindowSize(g_window, &win.w, &win.h);
  return ur_display_window_reachable(win, usable, n, 32) != 0;
}
static bool g_ur_disp_applied;
static void UrDisplayLifecycleAcceptanceTick(void) {
  if (g_ur_disp_on < 0) {
    const char *v = HostGetenv("UR_DISPLAY_LIFECYCLE_ACCEPTANCE");
    /* "1" runs the scenario; "exit" also quits when it is done. */
    g_ur_disp_on = v && (atoi(v) || strcmp(v, "exit") == 0) ? 1 : 0;
  }
  if (!g_ur_disp_on || g_ur_disp_step < 0 || !g_window) return;
  if (g_ur_disp_wait > 0) { g_ur_disp_wait--; return; }
  g_ur_disp_wait = 20;
  SDL_SyncWindow(g_window);
  switch (g_ur_disp_step++) {
  case 0: {
    int fs = 0;
    snesrecomp_desktop_product_get_display(&fs, &g_ur_disp_vsync);
    g_ur_disp_original = fs;
    if (fs != 0) g_ur_disp_applied = UrDisplayApply(0);
    break;
  }
  case 1:
    UrDisplayAcceptExpect("start_windowed", UrDisplayIsWindowed());
    g_ur_disp_applied = UrDisplayApply(1);
    break;
  case 2:
    UrDisplayAcceptExpect("borderless", g_ur_disp_applied && UrDisplayIsBorderless());
    g_ur_disp_applied = UrDisplayApply(2);
    break;
  case 3:
    /* The SDL3 defect: this used to stay borderless with no mode. */
    UrDisplayAcceptExpect("borderless_to_exclusive", g_ur_disp_applied && UrDisplayIsExclusive());
    g_ur_disp_applied = UrDisplayApply(1);
    break;
  case 4:
    UrDisplayAcceptExpect("exclusive_to_borderless", g_ur_disp_applied && UrDisplayIsBorderless());
    g_ur_disp_applied = UrDisplayApply(0);
    break;
  case 5:
    UrDisplayAcceptExpect("borderless_to_windowed", g_ur_disp_applied && UrDisplayIsWindowed());
    g_ur_disp_applied = UrDisplayApply(2);
    break;
  case 6:
    UrDisplayAcceptExpect("windowed_to_exclusive", g_ur_disp_applied && UrDisplayIsExclusive());
    HandleCommand(kKeys_Fullscreen, true);   /* the framework's Alt+Enter */
    HandleCommand(kKeys_Fullscreen, false);
    break;
  case 7:
    UrDisplayAcceptExpect("hotkey_leaves_fullscreen",
                          UrDisplayIsWindowed() && g_config.fullscreen == 0);
    HandleCommand(kKeys_Fullscreen, true);
    HandleCommand(kKeys_Fullscreen, false);
    break;
  case 8:
    /* Alt+Enter means borderless, never the exclusive mode used earlier. */
    UrDisplayAcceptExpect("hotkey_enters_borderless",
                          UrDisplayIsBorderless() && g_config.fullscreen == 1);
    g_ur_disp_applied = UrDisplayApply(0);
    break;
  case 9:
    UrDisplayAcceptExpect("windowed_again", g_ur_disp_applied && UrDisplayIsWindowed());
    SDL_SetWindowPosition(g_window, -30000, -30000);
    break;
  case 10:
    /* Only meaningful if the OS really left the window unreachable. */
    if (UrDisplayAcceptReachable()) {
      printf("UR_DISPLAY_ACCEPT step=offscreen_rescue not_exercised=1\n");
      g_ur_disp_step = 12;
      break;
    }
    {
      SDL_Event ev;
      memset(&ev, 0, sizeof(ev));
      ev.type = SDL_EVENT_DISPLAY_REMOVED;  /* through the ordinary pump */
      SDL_PushEvent(&ev);
    }
    break;
  case 11:
    UrDisplayAcceptExpect("offscreen_rescue", UrDisplayAcceptReachable());
    break;
  case 12:
    if (g_ur_disp_original != 0) UrDisplayApply(g_ur_disp_original);
    break;
  default: {
    printf("UR_DISPLAY_LIFECYCLE_ACCEPTANCE result=%s reconciles=%u\n",
           g_ur_disp_failed ? "fail" : "pass", g_ur_display_reconciles);
    fflush(stdout);
    g_ur_disp_step = -1;
    const char *v = HostGetenv("UR_DISPLAY_LIFECYCLE_ACCEPTANCE");
    if (v && strcmp(v, "exit") == 0) {
      SDL_Event quit;
      memset(&quit, 0, sizeof(quit));
      quit.type = SDL_QUIT;
      SDL_PushEvent(&quit);
    }
    break;
  }
  }
  fflush(stdout);
}
#else
static void UrDisplayLifecycleAcceptanceTick(void) {}
#endif
'''


def once(source: str, needle: str, replacement: str) -> str:
    if source.count(needle) != 1:
        raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    return source.replace(needle, replacement, 1)


def patch_host_main(source: str, policy: Path) -> str:
    if MARK in source:
        return source
    if OPTIONS_MARK not in source:
        raise ValueError("Stage baldosa_modern_options_spike.py before the display seam")
    for needle in (HELPERS_ANCHOR, DEFAULT_BRANCH, OPTIONS_SDL3, LAUNCHER,
                   HOTKEY, CREATED, TICK_ANCHOR):
        if source.count(needle) != 1:
            raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    source = once(source, HELPERS_ANCHOR, helpers(policy) + HELPERS_ANCHOR)
    source = once(source, DEFAULT_BRANCH, DEFAULT_BRANCH_NEW)
    source = once(source, OPTIONS_SDL3, OPTIONS_SDL3_NEW)
    source = once(source, LAUNCHER, LAUNCHER_NEW)
    source = once(source, HOTKEY, HOTKEY_NEW)
    source = once(source, CREATED, CREATED_NEW)
    return once(source, TICK_ANCHOR, TICK_NEW)


def plan(game: Path, root: Path):
    policy = (root / POLICY).resolve()
    if not policy.is_file():
        raise ValueError(f"Missing project-owned display policy: {policy}")
    path = game / "snesrecomp/runner/src/desktop/host_main.c"
    before = path.read_text(encoding="utf-8")
    return [(path, before, patch_host_main(before, policy))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--ur-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    for path, before, after in plan(args.game.resolve(), args.ur_root.resolve()):
        if before != after:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

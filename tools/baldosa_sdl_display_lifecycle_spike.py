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

# The framework's window-size keys (Ctrl+Up/Down, Ctrl+wheel) change only the
# live scale; config.ini kept the old WindowScale, so the size was forgotten.
SCALE_STEP = (
    "  int new_scale = IntMax(IntMin(g_current_window_scale + scale_step, max_scale), 1);\n"
    "  g_current_window_scale = new_scale;\n"
)
SCALE_STEP_NEW = SCALE_STEP + (
    "  /* " + MARK + ": a player's explicit size step is remembered at exit.\n"
    "   * A re-clamp (step 0, after a display or DPI change) is not a choice. */\n"
    "  if (scale_step != 0 && new_scale != g_config.window_scale) {\n"
    "    g_config.window_scale = (uint8)new_scale;\n"
    "    g_fullscreen_changed = true;  /* the host's persist-display-at-exit flag */\n"
    "  }\n"
)

CREATED = "  g_window = window;\n"
CREATED_NEW = (
    "  g_window = window;\n"
    "  /* " + MARK + ": a window created fullscreen is borderless in SDL3. */\n"
    "  if (g_config.fullscreen == 2 && !UrApplyFullscreenMode(2))\n"
    "    printf(\"UR_DISPLAY startup exclusive unavailable; staying borderless\\n\");\n"
)

# After the renderer has the window: an OpenGL renderer can recreate it, which
# drops a position set earlier.
RENDERER_READY = "  g_audio_mutex = SDL_CreateMutex();\n"
RENDERER_READY_NEW = (
    "  UrRestoreWindowPlacement();  /* " + MARK + ": back on the display it was on */\n"
    + RENDERER_READY
)

# The in-game launcher's own event loop drains display events too: a monitor
# removed or rescaled while it was open is reconciled when it returns.
LAUNCHER_RETURN = "  SDL_FlushEvent(SDL_QUIT);\n"
LAUNCHER_RETURN_NEW = LAUNCHER_RETURN + (
    "#if SNESRECOMP_SDL3\n"
    "  UrDisplayReconcile(\"launcher_returned\");  /* " + MARK + " */\n"
    "#endif\n"
)

# The host's own clean-exit config write; the window still exists here.
EXIT_SAVE = (
    "  /* A volume or fullscreen change made with the keys survives the session,\n"
    "   * like the launcher's. */\n"
)
EXIT_SAVE_NEW = (
    "  UrSaveWindowPlacement();  /* " + MARK + " */\n" + EXIT_SAVE
)

# Staged by baldosa_product_pause_spike.py: product keys come first and get
# no modifiers, so a visible Modern root took Alt+Enter's Return as CONFIRM.
PRODUCT_KEY = (
    "static void HandleInput(int keyCode, int keyMod, bool pressed) {\n"
    "  if (g_game->product_system_key &&\n"
    "      g_game->product_system_key(keyCode, pressed ? 1 : 0)) return;\n"
)
PRODUCT_KEY_NEW = (
    "static void HandleInput(int keyCode, int keyMod, bool pressed) {\n"
    "  /* " + MARK + ": the window command (Alt+Enter) always reaches the\n"
    "   * framework; it is never a Modern menu confirm. */\n"
    "  const bool ur_window_command =\n"
    "      FindCmdForSdlKey(keyCode, (SDL_Keymod)keyMod) == kKeys_Fullscreen;\n"
    "  if (!ur_window_command && g_game->product_system_key &&\n"
    "      g_game->product_system_key(keyCode, pressed ? 1 : 0)) return;\n"
)

TICK_ANCHOR = "    OverlaySelftestPadMainTick(frameCtr);\n"
TICK_NEW = TICK_ANCHOR + (
    "    UrDisplayLifecycleAcceptanceTick();  /* " + MARK + " */\n"
    "    UrDisplayPlacementSmokeTick();\n")


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
/* Window placement across launches: the display (by name + bounds, see
 * ur_display_placement_match) and the last windowed position, in
 * window-placement.txt next to config.ini. Missing, ambiguous or damaged
 * data leaves the window where SDL put it (the primary display). */
#if SNESRECOMP_SDL3
static int g_ur_place_has_window;
static UrDisplayRect g_ur_place_window;
static int UrPlacementPath(char *out, size_t cap) {
  const char *cfg = g_active_config_file;
  const char *slash = NULL;
  if (!cfg || !*cfg) return 0;
  for (const char *c = cfg; *c; ++c) if (*c == '/' || *c == '\\') slash = c;
  const size_t dir = slash ? (size_t)(slash - cfg + 1) : 0;
  if (dir + sizeof("window-placement.txt") > cap) return 0;
  memcpy(out, cfg, dir);
  memcpy(out + dir, "window-placement.txt", sizeof("window-placement.txt"));
  return 1;
}
static int UrUsableDisplays(UrDisplayRect *usable, int cap) {
  int count = 0, n = 0;
  SDL_DisplayID *ids = SDL_GetDisplays(&count);
  for (int i = 0; ids && i < count && n < cap; i++) {
    SDL_Rect r;
    if (SDL_GetDisplayUsableBounds(ids[i], &r)) {
      usable[n].x = r.x; usable[n].y = r.y; usable[n].w = r.w; usable[n].h = r.h; n++;
    }
  }
  SDL_free(ids);
  return n;
}
static void UrRestoreWindowPlacement(void) {
  char path[1100], line[600], name[256] = {0};
  UrDisplayRect bounds = {0, 0, 0, 0};
  int have_bounds = 0, maximized = 0;
  if (!g_window || !UrPlacementPath(path, sizeof(path))) return;
  FILE *f = fopen(path, "rb");
  if (!f) return;
  if (!fgets(line, sizeof(line), f) || strncmp(line, "ur-window-placement-v1", 22) != 0) {
    fclose(f);
    return;
  }
  while (fgets(line, sizeof(line), f)) {
    line[strcspn(line, "\r\n")] = 0;
    if (strncmp(line, "display_name=", 13) == 0)
      snprintf(name, sizeof(name), "%s", line + 13);
    else if (strcmp(line, "maximized=1") == 0)
      maximized = 1;
    else if (sscanf(line, "display_bounds=%d,%d,%d,%d",
                    &bounds.x, &bounds.y, &bounds.w, &bounds.h) == 4)
      have_bounds = 1;
    else if (sscanf(line, "window=%d,%d,%d,%d", &g_ur_place_window.x,
                    &g_ur_place_window.y, &g_ur_place_window.w,
                    &g_ur_place_window.h) == 4)
      g_ur_place_has_window = g_ur_place_window.w > 0 && g_ur_place_window.h > 0;
  }
  fclose(f);
  if (!have_bounds || !name[0]) return;
  int count = 0, n = 0;
  SDL_DisplayID *ids = SDL_GetDisplays(&count);
  UrDisplayIdentity candidates[16];
  SDL_DisplayID candidate_ids[16];
  for (int i = 0; ids && i < count && n < 16; i++) {
    SDL_Rect r;
    if (!SDL_GetDisplayBounds(ids[i], &r)) continue;
    candidates[n].name = SDL_GetDisplayName(ids[i]);
    candidates[n].bounds.x = r.x; candidates[n].bounds.y = r.y;
    candidates[n].bounds.w = r.w; candidates[n].bounds.h = r.h;
    candidate_ids[n++] = ids[i];
  }
  SDL_free(ids);
  const int match = ur_display_placement_match(name, bounds, candidates, n);
  if (match < 0) {
    printf("UR_DISPLAY placement saved_display_missing name=%s\n", name);
    return;
  }
  const SDL_DisplayID target = candidate_ids[match];
  if (SDL_GetWindowFlags(g_window) & SDL_WINDOW_FULLSCREEN) {
    if (SDL_GetDisplayForWindow(g_window) != target) {
      /* Leave fullscreen, move, then re-enter with that display's mode. */
      SDL_SetWindowFullscreen(g_window, false);
      SDL_SyncWindow(g_window);
      SDL_SetWindowPosition(g_window, SDL_WINDOWPOS_CENTERED_DISPLAY(target),
                            SDL_WINDOWPOS_CENTERED_DISPLAY(target));
      SDL_SyncWindow(g_window);
      if (!UrApplyFullscreenMode(g_config.fullscreen)) UrApplyFullscreenMode(1);
      SDL_SetWindowFullscreen(g_window, true);
      SDL_SyncWindow(g_window);
    }
  } else {
    UrDisplayRect usable[16], want;
    const int u = UrUsableDisplays(usable, 16);
    SDL_GetWindowSize(g_window, &want.w, &want.h);
    want.x = g_ur_place_window.x;
    want.y = g_ur_place_window.y;
    if (g_ur_place_has_window && ur_display_window_reachable(want, usable, u, 32))
      SDL_SetWindowPosition(g_window, want.x, want.y);
    else
      SDL_SetWindowPosition(g_window, SDL_WINDOWPOS_CENTERED_DISPLAY(target),
                            SDL_WINDOWPOS_CENTERED_DISPLAY(target));
    SDL_SyncWindow(g_window);
    /* Maximize where it now is: on the saved display, over its saved spot. */
    if (maximized) {
      SDL_MaximizeWindow(g_window);
      SDL_SyncWindow(g_window);
    }
  }
  int x = 0, y = 0;
  SDL_GetWindowPosition(g_window, &x, &y);
  const SDL_WindowFlags restored = SDL_GetWindowFlags(g_window);
  printf("UR_DISPLAY placement restored display=%s fullscreen=%d maximized=%d window=%d,%d\n",
         name, (restored & SDL_WINDOW_FULLSCREEN) ? 1 : 0,
         (restored & SDL_WINDOW_MAXIMIZED) ? 1 : 0, x, y);
}
static void UrSaveWindowPlacement(void) {
  char path[1100];
  SDL_Rect r;
  if (!g_window || !UrPlacementPath(path, sizeof(path))) return;
  const SDL_DisplayID display = SDL_GetDisplayForWindow(g_window);
  const char *name = display ? SDL_GetDisplayName(display) : NULL;
  if (!name || !*name || !SDL_GetDisplayBounds(display, &r)) return;
  const SDL_WindowFlags flags = SDL_GetWindowFlags(g_window);
  if (!(flags & (SDL_WINDOW_FULLSCREEN | SDL_WINDOW_MINIMIZED | SDL_WINDOW_MAXIMIZED))) {
    SDL_GetWindowPosition(g_window, &g_ur_place_window.x, &g_ur_place_window.y);
    SDL_GetWindowSize(g_window, &g_ur_place_window.w, &g_ur_place_window.h);
    g_ur_place_has_window = 1;
  }
  FILE *f = fopen(path, "wb");
  if (!f) return;
  fputs("ur-window-placement-v1\ndisplay_name=", f);
  for (const char *c = name; *c; ++c) fputc(*c == '\r' || *c == '\n' ? ' ' : *c, f);
  fprintf(f, "\ndisplay_bounds=%d,%d,%d,%d\n", r.x, r.y, r.w, r.h);
  if (g_ur_place_has_window)
    fprintf(f, "window=%d,%d,%d,%d\n", g_ur_place_window.x, g_ur_place_window.y,
            g_ur_place_window.w, g_ur_place_window.h);
  /* A maximized window keeps the earlier windowed spot to come back to. */
  if ((flags & SDL_WINDOW_MAXIMIZED) && !(flags & SDL_WINDOW_FULLSCREEN))
    fputs("maximized=1\n", f);
  const int ok = fclose(f) == 0;
  printf("UR_DISPLAY placement saved=%d display=%s\n", ok, name);
}
/* SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE=move:X,Y | maximize | report | launcher
 * (test-only, inert unless set): move or maximize the window then quit
 * through the ordinary exit (which saves the placement), report where
 * launch put it and quit, or open the in-game launcher and report after. */
static void UrDisplayPlacementSmokeTick(void) {
  static int mode = -1, frames, tx, ty;
  if (mode < 0) {
    const char *v = HostGetenv("UR_DISPLAY_PLACEMENT_SMOKE");
    mode = !v ? 0 : strcmp(v, "report") == 0 ? 2 : strcmp(v, "maximize") == 0 ? 3
         : strcmp(v, "launcher") == 0 ? 4
         : sscanf(v, "move:%d,%d", &tx, &ty) == 2 ? 1 : 0;
  }
  if (!mode || !g_window || frames < 0) return;
  ++frames;
  /* launcher: open the in-game launcher once, then report after it returns. */
  if (mode == 4 && frames == 30) {
    g_open_launcher_hotkey = 1;
    return;
  }
  if ((mode == 1 || mode == 3) && frames == 40) {
    if (mode == 1) SDL_SetWindowPosition(g_window, tx, ty);
    else SDL_MaximizeWindow(g_window);
    SDL_SyncWindow(g_window);
    return;
  }
  if (frames != (mode == 2 ? 40 : mode == 4 ? 90 : 70)) return;
  int x = 0, y = 0;
  SDL_GetWindowPosition(g_window, &x, &y);
  const SDL_DisplayID display = SDL_GetDisplayForWindow(g_window);
  const char *name = display ? SDL_GetDisplayName(display) : NULL;
  const SDL_WindowFlags flags = SDL_GetWindowFlags(g_window);
  printf("UR_DISPLAY_PLACEMENT_SMOKE mode=%s window=%d,%d fullscreen=%d maximized=%d "
         "display=%s\n", mode == 1 ? "move" : mode == 3 ? "maximize" : mode == 4 ? "launcher" : "report", x, y,
         (flags & SDL_WINDOW_FULLSCREEN) ? 1 : 0, (flags & SDL_WINDOW_MAXIMIZED) ? 1 : 0,
         name ? name : "-");
  fflush(stdout);
  frames = -1;
  SDL_Event quit;
  memset(&quit, 0, sizeof(quit));
  quit.type = SDL_QUIT;
  SDL_PushEvent(&quit);
}
#else
static void UrRestoreWindowPlacement(void) {}
static void UrSaveWindowPlacement(void) {}
static void UrDisplayPlacementSmokeTick(void) {}
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
    /* A real Alt+Enter through the host key path, product hook included:
     * with the Modern root visible it must not be taken as CONFIRM. */
    HandleInput(SDLK_RETURN, SDL_KMOD_LALT, true);
    HandleInput(SDLK_RETURN, SDL_KMOD_LALT, false);
    break;
  case 7:
    UrDisplayAcceptExpect("hotkey_leaves_fullscreen",
                          UrDisplayIsWindowed() && g_config.fullscreen == 0);
    HandleInput(SDLK_RETURN, SDL_KMOD_LALT, true);
    HandleInput(SDLK_RETURN, SDL_KMOD_LALT, false);
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
  case 12: {
    /* The window-size key path: an explicit step is recorded for the exit
     * write; the step-0 re-clamp that display events use is not. */
    const int before = g_current_window_scale;
    ChangeWindowScale(before > 1 ? -1 : 1);
    const bool stepped = g_current_window_scale != before;
    const int recorded = g_config.window_scale;
    const bool persisted = recorded == g_current_window_scale && g_fullscreen_changed;
    ChangeWindowScale(0);
    UrDisplayAcceptExpect("window_scale_step_persisted",
                          stepped && persisted && g_config.window_scale == recorded);
    break;
  }
  case 13:
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
                   HOTKEY, CREATED, TICK_ANCHOR, PRODUCT_KEY, SCALE_STEP,
                   EXIT_SAVE, RENDERER_READY, LAUNCHER_RETURN):
        if source.count(needle) != 1:
            raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    source = once(source, HELPERS_ANCHOR, helpers(policy) + HELPERS_ANCHOR)
    source = once(source, DEFAULT_BRANCH, DEFAULT_BRANCH_NEW)
    source = once(source, OPTIONS_SDL3, OPTIONS_SDL3_NEW)
    source = once(source, LAUNCHER, LAUNCHER_NEW)
    source = once(source, HOTKEY, HOTKEY_NEW)
    source = once(source, CREATED, CREATED_NEW)
    source = once(source, PRODUCT_KEY, PRODUCT_KEY_NEW)
    source = once(source, SCALE_STEP, SCALE_STEP_NEW)
    source = once(source, EXIT_SAVE, EXIT_SAVE_NEW)
    source = once(source, RENDERER_READY, RENDERER_READY_NEW)
    source = once(source, LAUNCHER_RETURN, LAUNCHER_RETURN_NEW)
    return once(source, TICK_ANCHOR, TICK_NEW)


# The launcher asks for a 3.3 core context, but where no real GL driver
# exists (remote desktop, VMs, GPU-less machines) Windows hands back the GDI
# 1.1 one instead of failing. ImGui's GL3 loader then fails, its result is
# ignored, and the first draw dereferenced a null GL function: the in-game
# launcher hotkey crashed the whole game. Refuse such a context so the
# launcher reports UNAVAILABLE, which the host already handles.
LAUNCHER_GL = (
    "    SDL_GL_MakeCurrent(p->window, p->gl);\n"
    "    SDL_GL_SetSwapInterval(1);   // vsync \u2014 a launcher has no reason to spin\n"
)
LAUNCHER_GL_NEW = (
    "    SDL_GL_MakeCurrent(p->window, p->gl);\n"
    "    /* " + MARK + ": refuse a context too old for the GL3 renderer. */\n"
    "    {\n"
    "        typedef const unsigned char *(\n"
    "#ifdef _WIN32\n"
    "            __stdcall\n"
    "#endif\n"
    "            *UrGetString)(unsigned int);\n"
    "        UrGetString get_string = (UrGetString)SDL_GL_GetProcAddress(\"glGetString\");\n"
    "        const char *version = get_string ? (const char *)get_string(0x1F02u) : NULL;\n"
    "        const char *forced = getenv(\"SNESRECOMP_UR_LAUNCHER_GL_VERSION\");  /* test only */\n"
    "        if (forced && *forced) version = forced;\n"
    "        int major = 0;\n"
    "        for (const char *c = version; c && *c; ++c)\n"
    "            if (*c >= '0' && *c <= '9') { major = atoi(c); break; }\n"
    "        if (major < 3) {\n"
    "            fprintf(stderr, \"[launcher] UR_LAUNCHER_GL unusable version=%s\\n\",\n"
    "                    version ? version : \"(none)\");\n"
    "            SDL_GL_DestroyContext(p->gl);\n"
    "            p->gl = NULL;\n"
    "            SDL_DestroyWindow(p->window);\n"
    "            p->window = NULL;\n"
    "            if (s_quit_sdl) SDL_Quit();\n"
    "            return false;\n"
    "        }\n"
    "    }\n"
    "    SDL_GL_SetSwapInterval(1);   // vsync \u2014 a launcher has no reason to spin\n"
)


def patch_launcher_platform(source: str) -> str:
    if MARK in source:
        return source
    return once(source, LAUNCHER_GL, LAUNCHER_GL_NEW)


def plan(game: Path, root: Path):
    policy = (root / POLICY).resolve()
    if not policy.is_file():
        raise ValueError(f"Missing project-owned display policy: {policy}")
    path = game / "snesrecomp/runner/src/desktop/host_main.c"
    before = path.read_text(encoding="utf-8")
    launcher = game / "recomp-ui/src/common/launcher_platform_sdl3.c"
    launcher_before = launcher.read_text(encoding="utf-8")
    return [(path, before, patch_host_main(before, policy)),
            (launcher, launcher_before, patch_launcher_platform(launcher_before))]


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

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Desktop window lifecycle decisions for the pinned SNESRecomp host.
 *
 * SDL3 dropped SDL2's separate "fullscreen desktop" flag: a fullscreen
 * window is borderless desktop fullscreen unless the host first gives it a
 * concrete display mode with SDL_SetWindowFullscreenMode. The host's
 * Display setting (0 windowed, 1 borderless, 2 exclusive) therefore needs a
 * mode decision every time it enters or re-enters fullscreen, and again
 * when the window lands on another display or that display's mode changes.
 *
 * A windowed window can also be left unreachable when the monitor it was on
 * goes away, or overflow its display after a DPI change. These pure helpers
 * decide; the host performs the SDL calls. No SDL types, no state. */

typedef struct UrDisplayRect {
    int x, y, w, h;
} UrDisplayRect;

typedef enum UrFullscreenModeRequest {
    /* Leave the window fullscreen-mode-free (windowed or borderless). */
    UR_FULLSCREEN_MODE_DESKTOP = 0,
    /* Give the window an exclusive mode matching its display's desktop. */
    UR_FULLSCREEN_MODE_EXCLUSIVE = 1,
} UrFullscreenModeRequest;

/* The Display setting's fullscreen-mode request. Out-of-range values (the
 * Options seam refuses them) map to desktop so nothing exclusive is guessed. */
static inline UrFullscreenModeRequest ur_display_fullscreen_mode_request(
    int display_setting) {
    return display_setting == 2 ? UR_FULLSCREEN_MODE_EXCLUSIVE
                                : UR_FULLSCREEN_MODE_DESKTOP;
}

static inline int ur_display_rect_overlap(
    UrDisplayRect a, UrDisplayRect b, int *ow, int *oh) {
    const long long ax2 = (long long)a.x + a.w, ay2 = (long long)a.y + a.h;
    const long long bx2 = (long long)b.x + b.w, by2 = (long long)b.y + b.h;
    const long long x1 = a.x > b.x ? a.x : b.x;
    const long long y1 = a.y > b.y ? a.y : b.y;
    const long long x2 = ax2 < bx2 ? ax2 : bx2;
    const long long y2 = ay2 < by2 ? ay2 : by2;
    *ow = x2 > x1 ? (int)(x2 - x1) : 0;
    *oh = y2 > y1 ? (int)(y2 - y1) : 0;
    return *ow > 0 && *oh > 0;
}

/* A windowed window is reachable when the strip along its top edge (where
 * the title bar and the host's Ctrl-drag area are) shows at least
 * `min_visible` pixels of width and of height on some display's usable
 * area. Only the top strip counts: a window whose top is off-screen cannot
 * be dragged back with the mouse. */
static inline int ur_display_window_reachable(
    UrDisplayRect window, const UrDisplayRect *usable, int count,
    int min_visible) {
    UrDisplayRect strip = window;
    int i, ow, oh;
    if (window.w <= 0 || window.h <= 0) return 0;
    if (strip.h > min_visible) strip.h = min_visible;
    for (i = 0; i < count; ++i) {
        if (ur_display_rect_overlap(strip, usable[i], &ow, &oh) &&
            ow >= (min_visible < window.w ? min_visible : window.w) &&
            oh >= strip.h)
            return 1;
    }
    return 0;
}

/* Whole window inside the usable area. */
static inline int ur_display_window_fits(
    UrDisplayRect window, UrDisplayRect usable) {
    return window.w <= usable.w && window.h <= usable.h &&
           window.x >= usable.x && window.y >= usable.y &&
           (long long)window.x + window.w <= (long long)usable.x + usable.w &&
           (long long)window.y + window.h <= (long long)usable.y + usable.h;
}

/* Where to put an unreachable window: its size, shrunk to the target
 * usable area if needed, centred on it. */
static inline UrDisplayRect ur_display_window_rescue(
    UrDisplayRect window, UrDisplayRect usable) {
    UrDisplayRect out;
    out.w = window.w < usable.w ? window.w : usable.w;
    out.h = window.h < usable.h ? window.h : usable.h;
    if (out.w < 1) out.w = 1;
    if (out.h < 1) out.h = 1;
    out.x = usable.x + (usable.w - out.w) / 2;
    out.y = usable.y + (usable.h - out.h) / 2;
    return out;
}

#ifdef __cplusplus
}
#endif

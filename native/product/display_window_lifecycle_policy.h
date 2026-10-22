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

/* Which connected display a saved window placement belongs to.
 *
 * SDL display IDs are per-run, so a placement is remembered by the
 * display's name and desktop bounds. The same name at the same bounds is
 * the same display. The same name at different bounds is still that
 * display if exactly one display has the name (a resolution or layout
 * change). Anything else is ambiguous or gone: -1, and the window stays
 * on the primary display rather than guessing. */
typedef struct UrDisplayIdentity {
    const char *name;
    UrDisplayRect bounds;
} UrDisplayIdentity;

static inline int ur_display_name_equal(const char *a, const char *b) {
    if (!a || !b || !*a) return 0;
    while (*a && *a == *b) { ++a; ++b; }
    return *a == *b;
}

static inline int ur_display_placement_match(
    const char *saved_name, UrDisplayRect saved_bounds,
    const UrDisplayIdentity *displays, int count) {
    int i, named = 0, named_index = -1;
    for (i = 0; i < count; ++i) {
        if (!ur_display_name_equal(saved_name, displays[i].name)) continue;
        if (displays[i].bounds.x == saved_bounds.x &&
            displays[i].bounds.y == saved_bounds.y &&
            displays[i].bounds.w == saved_bounds.w &&
            displays[i].bounds.h == saved_bounds.h)
            return i;
        ++named;
        named_index = i;
    }
    return named == 1 ? named_index : -1;
}

/* Whether waiting for the panel's vblank would slow the game itself.
 *
 * The desktop host presents once per simulated frame and drops simulation
 * it falls behind on, so a swap interval locks the game to the panel. At
 * or near the guest rate (59.94/60 Hz panels against the SNES's ~60.1 Hz)
 * that is the usual sync-to-video. A panel more than 1% slower (a 50 Hz
 * TV, a 30 Hz mode) would run the game itself slower, so presents must
 * not wait there. An unknown refresh (0) keeps the setting. */
static inline int ur_display_vsync_cannot_carry(double panel_hz, double guest_hz) {
    return panel_hz > 0 && guest_hz > 0 && panel_hz < guest_hz * 0.99;
}

/* The window scale to open with when the player never chose one.
 *
 * The host opens at scale 2 of its 320x240 base, which on a 200% display
 * (a 4K laptop or monitor) is a quarter of the size the desktop draws
 * everything else at. Follow the display's content scale, so a 200% display
 * opens at 4, but never below the old default of 2, and step back toward 2
 * while the window would not fit 90% of the usable area. */
static inline int ur_display_default_window_scale(
    float content_scale, int base_w, int base_h, int usable_w, int usable_h,
    int max_scale) {
    int scale = content_scale > 0 ? (int)(2.0f * content_scale + 0.5f) : 2;
    if (scale < 2) scale = 2;
    if (max_scale >= 2 && scale > max_scale) scale = max_scale;
    while (scale > 2 && usable_w > 0 && usable_h > 0 &&
           ((long long)scale * base_w * 10 > (long long)usable_w * 9 ||
            (long long)scale * base_h * 10 > (long long)usable_h * 9))
        --scale;
    return scale;
}

#ifdef __cplusplus
}
#endif

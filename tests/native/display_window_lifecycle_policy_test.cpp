#include "display_window_lifecycle_policy.h"

#include <cassert>
#include <climits>

namespace {

constexpr UrDisplayRect kLeft{0, 0, 1920, 1040};       // taskbar-trimmed
constexpr UrDisplayRect kRight{1920, 0, 2560, 1400};

void only_exclusive_setting_requests_a_mode() {
    assert(ur_display_fullscreen_mode_request(2) == UR_FULLSCREEN_MODE_EXCLUSIVE);
    assert(ur_display_fullscreen_mode_request(1) == UR_FULLSCREEN_MODE_DESKTOP);
    assert(ur_display_fullscreen_mode_request(0) == UR_FULLSCREEN_MODE_DESKTOP);
    // Never guess exclusive from an out-of-range value.
    assert(ur_display_fullscreen_mode_request(3) == UR_FULLSCREEN_MODE_DESKTOP);
    assert(ur_display_fullscreen_mode_request(-1) == UR_FULLSCREEN_MODE_DESKTOP);
}

void a_window_on_a_display_is_reachable() {
    const UrDisplayRect displays[] = {kLeft, kRight};
    assert(ur_display_window_reachable({100, 100, 960, 720}, displays, 2, 32));
    // Straddling both monitors.
    assert(ur_display_window_reachable({1500, 200, 960, 720}, displays, 2, 32));
    // Mostly off the left edge but its title strip still shows 40 px.
    assert(ur_display_window_reachable({-920, 10, 960, 720}, displays, 2, 32));
}

void a_window_left_on_a_removed_monitor_is_not() {
    // The right monitor was unplugged; the window stayed at its old place.
    const UrDisplayRect left_only[] = {kLeft};
    assert(!ur_display_window_reachable({2200, 100, 960, 720}, left_only, 1, 32));
    // Only a sliver (< 32 px) of the title strip is visible.
    assert(!ur_display_window_reachable({1900, 100, 960, 720}, left_only, 1, 32));
}

void a_window_whose_top_is_off_screen_is_not_reachable() {
    const UrDisplayRect displays[] = {kLeft};
    // Body visible, title bar above the screen: cannot be dragged.
    assert(!ur_display_window_reachable({100, -600, 960, 720}, displays, 1, 32));
    // The case a window manager produced locally after a -30000 move.
    assert(!ur_display_window_reachable({-864, -628, 960, 695}, displays, 1, 32));
}

void degenerate_inputs_are_safe() {
    const UrDisplayRect displays[] = {kLeft};
    assert(!ur_display_window_reachable({0, 0, 0, 720}, displays, 1, 32));
    assert(!ur_display_window_reachable({0, 0, 960, 720}, displays, 0, 32));
    // Extreme coordinates do not overflow.
    assert(!ur_display_window_reachable({INT_MAX - 10, INT_MAX - 10, 960, 720},
                                        displays, 1, 32));
    // A window narrower than the minimum is reachable if fully shown.
    assert(ur_display_window_reachable({10, 10, 20, 20}, displays, 1, 32));
}

void fits_requires_the_whole_window() {
    assert(ur_display_window_fits({0, 0, 1920, 1040}, kLeft));
    assert(!ur_display_window_fits({0, 0, 1920, 1080}, kLeft));
    assert(!ur_display_window_fits({-1, 0, 960, 720}, kLeft));
    assert(ur_display_window_fits({1920, 0, 2560, 1400}, kRight));
}

void rescue_centres_and_shrinks_to_the_target() {
    UrDisplayRect r = ur_display_window_rescue({5000, 5000, 960, 720}, kLeft);
    assert(r.w == 960 && r.h == 720);
    assert(r.x == (1920 - 960) / 2 && r.y == (1040 - 720) / 2);
    assert(ur_display_window_fits(r, kLeft));
    // Larger than the target (DPI change / small monitor): shrunk to fit.
    r = ur_display_window_rescue({0, 0, 3840, 2160}, kLeft);
    assert(r.w == 1920 && r.h == 1040 && r.x == 0 && r.y == 0);
    assert(ur_display_window_fits(r, kLeft));
    // Offset target (monitor not at the origin).
    r = ur_display_window_rescue({-9000, 0, 960, 720}, kRight);
    assert(ur_display_window_fits(r, kRight));
    const UrDisplayRect right_only[] = {kRight};
    assert(ur_display_window_reachable(r, right_only, 1, 32));
}

void placement_matches_the_same_named_display() {
    const UrDisplayIdentity displays[] = {
        {"Built-in Display", {0, 0, 1920, 1080}},
        {"LG TV", {1920, 0, 3840, 2160}},
    };
    // Exact name and bounds.
    assert(ur_display_placement_match("LG TV", {1920, 0, 3840, 2160}, displays, 2) == 1);
    // The TV changed resolution: still the only display with that name.
    assert(ur_display_placement_match("LG TV", {1920, 0, 1920, 1080}, displays, 2) == 1);
    // Unplugged: no guess.
    const UrDisplayIdentity laptop_only[] = {{"Built-in Display", {0, 0, 1920, 1080}}};
    assert(ur_display_placement_match("LG TV", {1920, 0, 3840, 2160}, laptop_only, 1) == -1);
}

void identical_monitors_need_bounds_to_disambiguate() {
    const UrDisplayIdentity twins[] = {
        {"DELL U2720Q", {0, 0, 2560, 1440}},
        {"DELL U2720Q", {2560, 0, 2560, 1440}},
    };
    assert(ur_display_placement_match("DELL U2720Q", {2560, 0, 2560, 1440}, twins, 2) == 1);
    assert(ur_display_placement_match("DELL U2720Q", {0, 0, 2560, 1440}, twins, 2) == 0);
    // Layout changed and both share the name: ambiguous, stay on primary.
    assert(ur_display_placement_match("DELL U2720Q", {5120, 0, 2560, 1440}, twins, 2) == -1);
}

void unnamed_displays_never_match() {
    const UrDisplayIdentity anonymous[] = {{"", {0, 0, 1920, 1080}}, {nullptr, {0, 0, 1, 1}}};
    assert(ur_display_placement_match("", {0, 0, 1920, 1080}, anonymous, 2) == -1);
    assert(ur_display_placement_match(nullptr, {0, 0, 1920, 1080}, anonymous, 2) == -1);
}

void vsync_waits_only_where_the_panel_can_carry_the_game() {
    const double snes = 60.0988;
    assert(!ur_display_vsync_cannot_carry(60.0, snes));    // sync-to-video
    assert(!ur_display_vsync_cannot_carry(59.94, snes));
    assert(!ur_display_vsync_cannot_carry(144.0, snes));
    assert(ur_display_vsync_cannot_carry(50.0, snes));     // PAL TV: 83% speed
    assert(ur_display_vsync_cannot_carry(30.0, snes));
    assert(!ur_display_vsync_cannot_carry(0.0, snes));     // unknown: keep setting
    assert(!ur_display_vsync_cannot_carry(50.0, 0.0));
}

void default_window_scale_follows_the_display() {
    // 100%: the old default; 150%: 3; 200% on a 4K panel: 4.
    assert(ur_display_default_window_scale(1.0f, 320, 240, 1920, 1040, 10) == 2);
    assert(ur_display_default_window_scale(1.5f, 320, 240, 2560, 1400, 10) == 3);
    assert(ur_display_default_window_scale(2.0f, 320, 240, 3840, 2100, 10) == 4);
    // Too big for the usable area: step back, never below 2.
    assert(ur_display_default_window_scale(2.0f, 320, 240, 1280, 680, 10) == 2);
    assert(ur_display_default_window_scale(2.0f, 320, 240, 1920, 1040, 10) == 3);
    assert(ur_display_default_window_scale(0.5f, 320, 240, 640, 400, 10) == 2);
    // Unknown scale or bounds keep the old default; the cap still applies.
    assert(ur_display_default_window_scale(0.0f, 320, 240, 3840, 2100, 10) == 2);
    assert(ur_display_default_window_scale(3.0f, 320, 240, 0, 0, 10) == 6);
    assert(ur_display_default_window_scale(3.0f, 320, 240, 0, 0, 4) == 4);
}

}  // namespace

int main() {
    only_exclusive_setting_requests_a_mode();
    a_window_on_a_display_is_reachable();
    a_window_left_on_a_removed_monitor_is_not();
    a_window_whose_top_is_off_screen_is_not_reachable();
    degenerate_inputs_are_safe();
    fits_requires_the_whole_window();
    rescue_centres_and_shrinks_to_the_target();
    placement_matches_the_same_named_display();
    identical_monitors_need_bounds_to_disambiguate();
    unnamed_displays_never_match();
    vsync_waits_only_where_the_panel_can_carry_the_game();
    default_window_scale_follows_the_display();
    return 0;
}

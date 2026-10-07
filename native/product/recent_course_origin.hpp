#pragma once

#include <cstdint>

namespace ur::product {

/*
 * Pure admission for Recent Course observation.
 *
 * Left idle, the stock MAIN_MENU (0xD7) fades to the title surface (0x84) and
 * plays a split-screen attract demo race (docs/UI-STATE-MAP.md DEMO,
 * analysis/generated/attract-cycle.json). That race is a validated live
 * course, but the player never chose it, so it must not become the profile's
 * Recent Course.
 *
 * A player race always reaches the race from a stable frontend state
 * (main menu, rider select, tours, tracks or NOW_PLAYING); the demo reaches it
 * from the title surface. While a course loads, WRAM $009F is reused as
 * per-frame scratch and can momentarily hold any value, so only a
 * (race, frontend) pair held for kRecentCourseOriginStableFrames consecutive
 * frames counts. Real frontend states hold for 30+ frames; scratch changes
 * every frame.
 */
inline constexpr std::uint16_t kRecentCourseOriginStableFrames = 8;

struct RecentCourseOriginState {
    std::uint8_t race_active_state = 0;
    std::uint8_t frontend_state = 0;
    std::uint16_t run_frames = 0;
    bool title_origin = false;
};

constexpr bool recent_course_origin_clears(std::uint8_t frontend_state) noexcept {
    return frontend_state == 0xD7u ||  // main menu
           frontend_state == 0x3Cu ||  // rider select
           frontend_state == 0x6Du ||  // tours
           frontend_state == 0xF6u ||  // tracks
           frontend_state == 0x16u;    // now playing / committed pre-race
}

constexpr RecentCourseOriginState observe_recent_course_origin(
    RecentCourseOriginState state,
    std::uint8_t race_active_state,
    std::uint8_t frontend_state) noexcept {
    if (state.run_frames > 0 &&
        state.race_active_state == race_active_state &&
        state.frontend_state == frontend_state) {
        if (state.run_frames < kRecentCourseOriginStableFrames) {
            ++state.run_frames;
        }
    } else {
        state.race_active_state = race_active_state;
        state.frontend_state = frontend_state;
        state.run_frames = 1;
    }

    // Only a stable non-race frontend pair changes the origin. In-race frames
    // (including the post-finish 0x84 fade while $0313 is still 1) keep it.
    if (state.run_frames == kRecentCourseOriginStableFrames &&
        race_active_state != 0x01u) {
        if (frontend_state == 0x84u) {
            state.title_origin = true;
        } else if (recent_course_origin_clears(frontend_state)) {
            state.title_origin = false;
        }
    }
    return state;
}

constexpr bool recent_course_origin_admits(
    const RecentCourseOriginState& state) noexcept {
    return !state.title_origin;
}

}  // namespace ur::product

#pragma once

// Presentation-only Modern menu kinetics. No SDL, guest memory, physics,
// saved settings, controller ownership, or replacement-racer selection.
// Timing measurements: analysis/generated/menu-visual-language.json:
// original cursor 16 tile phases x 2 frames, 12-frame selection settle,
// and the 39-frame BG2 entrance profile. All clocks are injected 60Hz ticks.
// Geometry is supplied separately so title/root composition agents own layout.

#include "modern_overlay_composition.hpp"
#include "modern_stock_menu_palette.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

inline constexpr int kModernMenuMotionRows = 5;
inline constexpr int kModernMenuMotionSourcePeriod = 32;
inline constexpr int kModernMenuMotionSelectionFrames = 12;
inline constexpr int kModernMenuMotionEntranceFrames = 39;
inline constexpr int kModernMenuStockHeroMaxCycle = 8;

// Measured source values, not a physics easing simulation.
inline constexpr std::array<int, kModernMenuMotionSelectionFrames>
    kModernMenuMotionSourceCursorSteps{{6, 4, 3, 3, 2, 1, 1, 1, 1, 0, 0, 1}};
inline constexpr std::array<int, kModernMenuMotionEntranceFrames>
    kModernMenuMotionSourceEntranceDelta{{
        1, 2, 3, 4, 5, 6, 7, 8,
        8, 8, 8, 8, 8, 8, 8, 8,
        8, 8, 8, 8, 8, 8, 8, 8,
        8, 8, 8, 8, 8, 8, 8, 8,
        7, 6, 5, 4, 3, 2, 1
    }};

// Avoid ms*60 overflow while keeping a frame-precise externally supplied
// clock. Wall-clock acquisition is deliberately not part of this model.
constexpr std::uint64_t modern_menu_tick60(std::uint64_t milliseconds) noexcept {
    // 60 ticks per 1000 ms: for every representable uint64_t millisecond
    // value, this expression is <= milliseconds, so it cannot overflow.
    return (milliseconds / 1000u) * 60u +
           ((milliseconds % 1000u) * 60u) / 1000u;
}

// Explicit native acceptance capture clock. An external harness may pin a
// single menu pose using UR_MODERN_MENU_TEST_TICK60, without injecting any
// guest clock, UI input, or frame-count side effects. Strict decimal only:
// malformed / overflow values fail closed to the real presentation clock.
// This is a presentation screenshot override, never a saved setting.
inline std::uint64_t modern_menu_resolve_test_tick60(
    std::uint64_t presentation_tick60, const char* decimal) noexcept {
    if (!decimal || !*decimal) return presentation_tick60;
    std::uint64_t parsed = 0;
    for (const char* current = decimal; *current; ++current) {
        const unsigned char ch = static_cast<unsigned char>(*current);
        if (ch < '0' || ch > '9') return presentation_tick60;
        const auto digit = static_cast<std::uint64_t>(ch - '0');
        constexpr auto maximum = UINT64_MAX;
        if (parsed > (maximum - digit) / 10u)
            return presentation_tick60;
        parsed = parsed * 10u + digit;
    }
    return parsed;
}

struct ModernMenuMotionInput {
    std::uint64_t tick60 = 0;
    std::uint8_t selection = 0;
    bool visible = false;
    bool reduced_motion = false;
};

struct ModernMenuMotionState {
    bool visible = false;
    std::uint8_t selection = 0;
    std::uint8_t previous_selection = 0;
    // Absolute logical Y of the marker at the most recent focus change.
    // Rapid direction changes resume from the interpolated visible marker,
    // never teleport to the previous semantic row.
    int cursor_origin_y = 0;
    int cursor_row_pitch = 21;
    // Reduced-motion mode semantically completes an already-visible entrance.
    // Re-enabling animation must not resurrect an old transition.
    bool intro_suppressed = false;
    bool hero_hold_pose = false;
    std::uint64_t first_tick = 0;
    std::uint64_t selection_tick = 0;
    std::uint64_t last_tick = 0;
};

struct ModernMenuMotionPose {
    bool visible = false;
    std::uint8_t selection = 0;
    int cursor_spin_phase = 0;  // 0..15, 2 source ticks per phase
    int cursor_remainder_px = 0; // signed, relative to selected row
    int entrance_distance_px = 0; // measured stock BG2 slide remaining
    int hero_bob_px = 0;       // host composition only, opt-in stock hero
    int hero_lean_px = 0;      // host composition only, opt-in stock hero
    int hero_frame_ordinal = 0; // one-shot source-frame ordinal, then hold
    bool reduced_motion = false;
};

constexpr int modern_menu_clamp_age(std::uint64_t now,
                                   std::uint64_t then, int maximum) noexcept {
    return now < then ? 0 :
        (now - then >= static_cast<std::uint64_t>(maximum)
            ? maximum : static_cast<int>(now - then));
}

constexpr int modern_menu_entrance_remaining(int age) noexcept {
    if (age >= kModernMenuMotionEntranceFrames) return 0;
    int total = 256;
    for (int i = 0; i < age; ++i)
        total -= kModernMenuMotionSourceEntranceDelta[
            static_cast<std::size_t>(i)];
    return total;
}

constexpr int modern_menu_cursor_distance(int age, int row_pitch) noexcept {
    if (age >= kModernMenuMotionSelectionFrames) return 0;
    int travelled = 0;
    for (int i = 0; i < age; ++i)
        travelled += kModernMenuMotionSourceCursorSteps[
            static_cast<std::size_t>(i)];
    // Source steps total 23px for a 24px stock row. Normalize onto the
    // Modern visual row pitch without changing the semantic focus row.
    return row_pitch - (travelled * row_pitch + 11) / 23;
}

// Scale any origin-target distance by the measured remaining 23/23 cursor
// movement envelope. Round symmetrically to preserve exact endpoints.
constexpr int modern_menu_cursor_remaining_offset(int distance,
                                                    int age) noexcept {
    const int remaining = modern_menu_cursor_distance(age, 23);
    const auto absolute = distance < 0 ?
        -static_cast<std::int64_t>(distance) :
        static_cast<std::int64_t>(distance);
    const auto amount = static_cast<int>(
        (absolute * remaining + 11) / 23);
    return distance < 0 ? -amount : amount;
}

// Pure with respect to every guest state: repeated inputs return the same
// pose. Hide or backwards clock resets entry; selection changes interrupt
// immediately and keep the next input authoritative even during animation.
inline ModernMenuMotionPose advance_modern_menu_motion(
    ModernMenuMotionState& state, ModernMenuMotionInput input,
    int row_pitch = 21) noexcept {
    if (!input.visible) {
        state = {};
        return {};
    }
    const auto selection = static_cast<std::uint8_t>(
        input.selection % kModernMenuMotionRows);
    // Native row metrics are compact logical pixels, not untrusted
    // framebuffer extents. Reject pathological widths before multiplying
    // semantic row indices into stored 32-bit coordinates.
    if (row_pitch <= 0 || row_pitch > 64) row_pitch = 21;
    if (!state.visible || input.tick60 < state.last_tick ||
        state.cursor_row_pitch != row_pitch) {
        state.visible = true;
        state.selection = selection;
        state.previous_selection = selection;
        state.cursor_origin_y = static_cast<int>(selection) * row_pitch;
        state.cursor_row_pitch = row_pitch;
        state.intro_suppressed = false;
        state.hero_hold_pose = false;
        state.first_tick = input.tick60;
        state.selection_tick = input.tick60;
    } else if (selection != state.selection) {
        const int previous = static_cast<int>(state.selection);
        const int old_target_y = previous * row_pitch;
        int elapsed = modern_menu_clamp_age(
            input.tick60, state.selection_tick,
            kModernMenuMotionSelectionFrames);
        // The original input trace records a same-frame 6px step. Model a
        // moving marker after that first measured step even when the caller
        // repeats the exact UI tick for deterministic capture.
        if (state.cursor_origin_y != old_target_y &&
            elapsed < kModernMenuMotionSelectionFrames)
            ++elapsed;
        const int old_display_y = old_target_y +
            modern_menu_cursor_remaining_offset(
                state.cursor_origin_y - old_target_y, elapsed);
        state.previous_selection = state.selection;
        state.selection = selection;
        // A fresh enabled focus edge can animate its source clip again;
        // the already-suppressed screen entrance must stay settled.
        if (!input.reduced_motion)
            state.hero_hold_pose = false;
        // Only adjacent movement has a meaningful continuous path. Wrapped
        // or external multi-step focus switches snap to the real new target.
        const int target = static_cast<int>(selection);
        state.cursor_origin_y = (target == previous + 1 ||
                                 target == previous - 1)
            ? old_display_y : target * row_pitch;
        state.selection_tick = input.tick60;
    }
    state.last_tick = input.tick60;
    ModernMenuMotionPose pose{};
    pose.visible = true;
    pose.selection = selection;
    pose.reduced_motion = input.reduced_motion;
    if (input.reduced_motion) {
        // The semantic focus is already on this row. Suppress any ongoing
        // interpolation and entrance for this visible root session, so
        // switching reduced motion off cannot replay stale movement.
        state.cursor_origin_y = static_cast<int>(selection) * row_pitch;
        state.previous_selection = selection;
        state.selection_tick = input.tick60;
        state.intro_suppressed = true;
        state.hero_hold_pose = true;
        return pose;
    }

    pose.cursor_spin_phase = static_cast<int>(
        (input.tick60 / 2u) % 16u);
    const int entry_age = modern_menu_clamp_age(
        input.tick60, state.first_tick, kModernMenuMotionEntranceFrames);
    pose.entrance_distance_px = state.intro_suppressed ? 0 :
        modern_menu_entrance_remaining(entry_age);

    const int age = modern_menu_clamp_age(
        input.tick60, state.selection_tick,
        kModernMenuMotionSelectionFrames);
    const int previous = static_cast<int>(state.previous_selection);
    const int current = static_cast<int>(state.selection);
    // Focus semantics are immediate; only the last rendered marker location
    // eases to the new row. Interrupting mid-travel does not jump backwards.
    const int cursor_age =
        state.cursor_origin_y != current * row_pitch &&
        age < kModernMenuMotionSelectionFrames ? age + 1 : age;
    pose.cursor_remainder_px = modern_menu_cursor_remaining_offset(
        state.cursor_origin_y - current * row_pitch, cursor_age);

    // A low-amplitude preview transform, never a new semantic rider pose.
    // Source racer artwork is a separate, approval-gated input; this model
    // cannot conjure new stock sprites, especially vetoed procedural 4x art.
    constexpr std::array<int, 16> kIdleBob{{
        0, 0, 0, -1, -1, -1, -2, -2,
        -2, -1, -1, -1, 0, 0, 0, 0
    }};
    const auto bob = static_cast<std::size_t>((input.tick60 / 4u) % 16u);
    pose.hero_bob_px = kIdleBob[bob];
    // On new root entry or any semantic selection change, use the source's
    // one distinct Original guest pose per 60Hz frame for eight frames,
    // then HOLD the last pose. There is no evidence 1213..1220 loops:
    // cycling it would invent a jump from source frame 1220 to 1213.
    // Source sprite admission is separately required by the hero compositor.
    pose.hero_frame_ordinal = state.hero_hold_pose ?
        kModernMenuStockHeroMaxCycle - 1 :
        (age >= kModernMenuStockHeroMaxCycle
            ? kModernMenuStockHeroMaxCycle - 1 : age);
    pose.hero_lean_px = (age < 4 && previous != current)
        ? (previous < current ? 1 : -1) : 0;
    return pose;
}

// Selection ornament for the actual native root framebuffer. A source-
// measured moving arrow *accent*, not an assertion that the stock OBJ arrow
// tiles have been extracted. The screen owner supplies its row anchors.
// UI focus/highlighting and route authority remain in ModernRootMenu.
struct ModernMenuMotionAnchors {
    int first_row_y = 57;
    int row_pitch = 21;
    int left_x = 5;
};

template <typename Painter>
inline bool paint_modern_menu_selection_motion(
    const Painter& paint, std::uint32_t* pixels,
    int stride, int height, int scale, HostOverlayRect rect,
    const ModernMenuMotionPose& pose,
    ModernMenuMotionAnchors anchors = {}) {
    if (!pose.visible || !paint.valid() || !pixels ||
        stride <= 0 || height <= 0 || scale < 1 || scale > 4 ||
        rect.x < 0 || rect.y < 0 || rect.width <= 0 || rect.height <= 0 ||
        rect.x > stride || rect.y > height ||
        rect.width > stride - rect.x || rect.height > height - rect.y ||
        anchors.row_pitch <= 0 || anchors.left_x < 0 ||
        pose.selection >= kModernMenuMotionRows)
        return false;
    // Do all layout arithmetic in 64 bits. Synthetic test/host callers must
    // not trigger signed 32-bit overflow with malformed anchors or offsets.
    const std::int64_t px64 = static_cast<std::int64_t>(rect.x) +
        static_cast<std::int64_t>(anchors.left_x) * scale;
    const std::int64_t py64 = static_cast<std::int64_t>(rect.y) +
        (static_cast<std::int64_t>(anchors.first_row_y) +
         static_cast<std::int64_t>(pose.selection) * anchors.row_pitch +
         static_cast<std::int64_t>(pose.cursor_remainder_px)) * scale;
    // Narrow enough to leave the existing selected text, panel and modal
    // completely intact; 4:3 and 16:9 both use the same semantic anchor.
    const int marker_height = 12 * scale;
    if (px64 < rect.x ||
        px64 + 2 * scale > static_cast<std::int64_t>(rect.x) + rect.width ||
        py64 < rect.y ||
        py64 + marker_height >
            static_cast<std::int64_t>(rect.y) + rect.height)
        return false;
    const int px = static_cast<int>(px64);
    const int py = static_cast<int>(py64);
    const auto& palette = kModernStockMenuPalette;
    // Original cursor OBJ is blue. Avoid fabricated rapid yellow/blue
    // flashing until the genuine 32x32 spinning source sprite is extracted.
    // A one-pixel height/inset breath twice per 32-tick source cycle offers
    // modest idle feedback while retaining a constant readable blue focus.
    const int inset = !pose.reduced_motion &&
                      pose.cursor_spin_phase >= 4 &&
                      pose.cursor_spin_phase < 12 ? scale : 0;
    paint.fill_rect(pixels, stride, height,
        px, py + inset, 2 * scale, marker_height - 2 * inset,
        palette.cursor_blue);
    return true;
}

}  // namespace ur::product

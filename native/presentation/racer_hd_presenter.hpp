#pragma once

#include <cstddef>
#include <cstdint>

#include "racer_oam_placement.hpp"
#include "racer_replacement_selector.hpp"

namespace ur::presentation {

inline constexpr int kRacerHdDensityScale = 4;
inline constexpr int kRacerHdLogicalSize = 64;
inline constexpr int kRacerHdAssetSize = kRacerHdLogicalSize * kRacerHdDensityScale;

constexpr bool valid_racer_hd_internal_render_scale(int scale) noexcept {
    return scale >= 1 && scale <= kRacerHdDensityScale;
}

constexpr int racer_hd_scaled_sample_coordinate(
    int output_coordinate,
    int scale
) noexcept {
    if (output_coordinate < 0 ||
        !valid_racer_hd_internal_render_scale(scale)) {
        return -1;
    }
    return ((output_coordinate * 2 + 1) * kRacerHdDensityScale) /
           (scale * 2);
}

constexpr bool racer_hd_asset_available(std::uint16_t semantic_frame_id) noexcept {
    return semantic_frame_id == 0x0541 || semantic_frame_id == 0x0540 ||
           semantic_frame_id == 0x057D || semantic_frame_id == 0x0542 ||
           semantic_frame_id == 0x0543 || semantic_frame_id == 0x057E ||
           semantic_frame_id == 0x057F || semantic_frame_id == 0x0544;
}

// The generic candidate remains a deterministic contract-only fallback for
// registered states that do not yet have authored Remastered art.
constexpr std::uint32_t sample_racer_hd_contract_candidate(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    const int cx = 128;
    const int cy = 142;
    const int dx = x - cx;
    const int dy = y - cy;
    const int r2 = dx * dx + dy * dy;

    const bool tire = r2 <= 88 * 88 && r2 >= 61 * 61;
    const bool rim = r2 < 61 * 61 && r2 >= 54 * 54;
    const bool hub = r2 <= 13 * 13;
    const bool fork = x >= 118 && x <= 130 && y >= 38 && y <= 115;
    const bool seat = x >= 96 && x <= 151 && y >= 24 && y <= 43;
    const bool marker = x >= 137 && x <= 151 && y >= 49 && y <= 69;

    if (marker) return 0xFFFFD84Au;
    if (seat || fork) return 0xFF25A8E0u;
    if (hub) return 0xFFF2F5F7u;
    if (rim) return 0xFFB8CDD8u;
    if (tire) return 0xFF1A2024u;
    return 0;
}

constexpr bool is_first_authored_remastered_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x0541 &&
           s.p1_primary == 0x0541 &&
           s.p2_primary == 0x0540 &&
           s.p1_companion == 0x0D0D &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0541_p1_companion_0d2d_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x0541 &&
           s.p1_primary == 0x0541 &&
           s.p2_primary == 0x0540 &&
           s.p1_companion == 0x0D2D &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0540_p1_predecessor_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x0540 &&
           s.p1_primary == 0x0540 &&
           s.p2_primary == 0x0541 &&
           s.p1_companion == 0x0D2C &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0540_p1_companion_0d2c_with_p2_0542_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x0540 &&
           s.p1_primary == 0x0540 &&
           s.p2_primary == 0x0542 &&
           s.p1_companion == 0x0D2C &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_057f_p1_companion_0d4a_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x057F &&
           s.p1_primary == 0x057F &&
           s.p2_primary == 0x0542 &&
           s.p1_companion == 0x0D4A &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_057e_p1_with_p2_0543_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x057E &&
           s.p1_primary == 0x057E &&
           s.p2_primary == 0x0543 &&
           s.p1_companion == 0x0D49 &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_057d_p1_with_p2_0543_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 1 &&
           registration.semantic_frame_id == 0x057D &&
           s.p1_primary == 0x057D &&
           s.p2_primary == 0x0543 &&
           s.p1_companion == 0x0D48 &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0543_p2_057d_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0543 &&
           s.p1_primary == 0x057D &&
           s.p2_primary == 0x0543 &&
           s.p1_companion == 0x0D48 &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0543_p2_057e_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0543 &&
           s.p1_primary == 0x057E &&
           s.p2_primary == 0x0543 &&
           s.p1_companion == 0x0D49 &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0542_p2_companion_0d2c_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0542 &&
           s.p1_primary == 0x0540 &&
           s.p2_primary == 0x0542 &&
           s.p1_companion == 0x0D2C &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0542_p2_companion_0d4a_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0542 &&
           s.p1_primary == 0x057F &&
           s.p2_primary == 0x0542 &&
           s.p1_companion == 0x0D4A &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0541_p2_predecessor_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0541 &&
           s.p1_primary == 0x0540 &&
           s.p2_primary == 0x0541 &&
           s.p1_companion == 0x0D2C &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0540_p2_companion_0d2d_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0540 &&
           s.p1_primary == 0x0541 &&
           s.p2_primary == 0x0540 &&
           s.p1_companion == 0x0D2D &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr bool is_authored_0540_p2_baseline_registration(
    const RacerRegistration& registration
) noexcept {
    const auto& s = registration.composition;
    return registration.player == 2 &&
           registration.semantic_frame_id == 0x0540 &&
           s.p1_primary == 0x0541 &&
           s.p2_primary == 0x0540 &&
           s.p1_companion == 0x0D0D &&
           s.p2_companion == 0x0000 &&
           s.p1_selector == 0 &&
           s.p2_selector == 0 &&
           s.p1_companion_gate_word == 0x0001 &&
           s.p2_companion_gate_word == 0x0000;
}

constexpr std::uint32_t authored_red_frame_color(
    int x,
    int y
) noexcept {
    // Broad object-local highlight from upper-left. The brightest red is
    // intentionally a small accent rather than the dominant fill.
    const int light = (255 - x) + (255 - y);
    if (light > 335) return 0xFF5353E8u;
    if (light > 300) return 0xFF3434C9u;
    if (light > 260) return 0xFF2525A3u;
    return 0xFF181878u;
}

constexpr std::uint32_t authored_blue_frame_color(
    int x,
    int y
) noexcept {
    const int light = (255 - x) + (255 - y);
    if (light > 335) return 0xFFE87353u;
    if (light > 300) return 0xFFC94D34u;
    if (light > 260) return 0xFFA33A25u;
    return 0xFF782818u;
}

constexpr std::uint32_t authored_metal_color(
    int x,
    int y
) noexcept {
    const int light = (255 - x) + (255 - y);
    if (light > 305) return 0xFFF2F4F6u;
    if (light > 275) return 0xFFD0D5D9u;
    return 0xFF8E999Fu;
}

constexpr std::uint32_t authored_rim_hardware_color(
    int x,
    int y,
    int wheel_cx,
    int wheel_cy
) noexcept {
    const int dx = x - wheel_cx;
    const int dy = y - wheel_cy;
    const int directional = (wheel_cx - x) + (wheel_cy - y);
    const int facet = (dx * 3 - dy * 2) & 0x0F;
    if (directional > 24 && facet < 9) return 0xFFF7F8F9u;
    if (directional > -4) return 0xFFD8DDE0u;
    return 0xFF8A969Cu;
}

constexpr std::uint32_t authored_hub_hardware_color(
    int x,
    int y,
    int wheel_cx,
    int wheel_cy
) noexcept {
    // Compact radial depth cue for the hub. This changes material only, never
    // occupancy, so wheel contact and the recovered pose envelope stay fixed.
    const int directional = (wheel_cx - x) + (wheel_cy - y);
    if (directional > 2) return 0xFFF7F8F9u;
    if (directional < -2) return 0xFF8A969Cu;
    return 0xFFD8DDE0u;
}

constexpr std::uint32_t authored_drivetrain_hardware_color(
    int y,
    int wheel_cy
) noexcept {
    // A stable upper highlight and lower occlusion give the crank/pedal stack
    // depth without introducing tiny alternating detail that would shimmer.
    if (y <= wheel_cy - 3) return 0xFFF7F8F9u;
    if (y >= wheel_cy + 1) return 0xFF8A969Cu;
    return 0xFFD8DDE0u;
}

constexpr std::uint32_t authored_rubber_color(
    int x,
    int y,
    int wheel_cx,
    int wheel_cy
) noexcept {
    const int dx = x - wheel_cx;
    const int dy = y - wheel_cy;
    const int directional = -(dx + dy);
    if (directional > 34) return 0xFF343C40u;
    if (directional < -36) return 0xFF151A1Du;
    return 0xFF20272Au;
}

constexpr std::uint32_t authored_saddle_color(
    int x,
    int y,
    int seat_cx,
    int seat_cy,
    int radius_y
) noexcept {
    const int dx = x - seat_cx;
    const int dy = y - seat_cy;
    const int directional = -(dx + dy);
    const int upper_shell = -(radius_y / 4);
    const int underside_start = radius_y / 4;
    const int lower_lip = radius_y / 2;

    // Model a stable layered seat volume inside the existing silhouette:
    // softly lit upper shell, darker sidewall, recessed underside and a
    // narrow lower lip. No occupied pixels are added or removed.
    if (dy <= upper_shell && directional > 18) return 0xFF454D52u;
    if (dy >= lower_lip) return 0xFF111719u;
    if (dy >= underside_start) return 0xFF1D2529u;
    if (directional > 28) return 0xFF384045u;
    return 0xFF262D31u;
}

constexpr std::uint32_t authored_frame_junction_color(
    int x,
    int y,
    int crown_x,
    int crown_y,
    bool blue_frame,
    bool member_overlap
) noexcept {
    // Model the crown as one forged transition rather than a round collar
    // sitting on top of separate members. The upper-left shoulder catches the
    // object-local key light, the centre stays on the frame body value, and
    // the lower/right throat compresses into shadow where fork and brace
    // visually merge. This changes material only, never the recovered alpha
    // envelope, contact anchor, or member geometry.
    const int dx = x - crown_x;
    const int dy = y - crown_y;
    const int radial2 = dx * dx + dy * dy;
    const bool shoulder_highlight =
        dy <= -1 && dx <= 2 && radial2 >= 12;
    const bool integrated_throat =
        dy >= 1 && (dx >= -2 || radial2 <= 20);
    const bool outer_shadow =
        dx >= 4 || dy >= 5;

    // Where the known neck/fork/brace geometry crosses the crown, let the
    // member's own baked frame shading continue through the joint. This
    // removes the remaining "round collar pasted over members" read while
    // preserving the crown's exact occupied silhouette.
    if (member_overlap) {
        return blue_frame
            ? authored_blue_frame_color(x, y)
            : authored_red_frame_color(x, y);
    }
    if (blue_frame) {
        if (shoulder_highlight) return 0xFFE87353u;
        if (outer_shadow) return 0xFF782818u;
        if (integrated_throat) return 0xFF963323u;
        return 0xFFC94D34u;
    }
    if (shoulder_highlight) return 0xFF5353E8u;
    if (outer_shadow) return 0xFF181878u;
    if (integrated_throat) return 0xFF232396u;
    return 0xFF3434C9u;
}

constexpr bool authored_segment_contains(
    int x,
    int y,
    int x1,
    int y1,
    int x2,
    int y2,
    int half_width
) noexcept {
    const int dx = x2 - x1;
    const int dy = y2 - y1;
    const int px = x - x1;
    const int py = y - y1;
    const int length2 = dx * dx + dy * dy;
    const int dot = px * dx + py * dy;
    if (dot < 0 || dot > length2) return false;
    const int cross = dx * py - dy * px;
    return cross * cross <= half_width * half_width * length2;
}

constexpr bool authored_crank_contains(
    int x,
    int y,
    int wheel_cx,
    int wheel_cy,
    int pedal_root_x
) noexcept {
    return authored_segment_contains(
        x, y, wheel_cx, wheel_cy, pedal_root_x, 116, 2
    );
}

constexpr bool authored_pedal_contains(
    int x,
    int y,
    int pedal_min_x,
    int pedal_max_x
) noexcept {
    return authored_segment_contains(
        x, y, pedal_min_x, 116, pedal_max_x, 116, 2
    );
}

constexpr bool authored_saddle_contains(
    int x,
    int y,
    int seat_cx,
    int seat_cy,
    int radius_x,
    int radius_y,
    int min_y,
    int max_y
) noexcept {
    if (y < min_y || y > max_y) return false;
    const int dx = x - seat_cx;
    const int dy = y - seat_cy;
    const int lhs =
        dx * dx * radius_y * radius_y +
        dy * dy * radius_x * radius_x;
    const int rhs =
        radius_x * radius_x * radius_y * radius_y;
    if (lhs > rhs) return false;

    // Keep a broad rear cushion but taper the forward third into a saddle
    // nose. This detail exists at true 4x density and survives runtime flips.
    const int nose_start = radius_x / 3;
    if (dx > nose_start) {
        const int run = radius_x - nose_start;
        const int remaining = radius_x - dx;
        const int nose_half_height =
            (radius_y / 4) + (remaining * radius_y * 3) / (4 * run);
        if (dy < -nose_half_height || dy > nose_half_height) return false;
    }
    return true;
}

constexpr bool authored_saddle_mount_contains(
    int x,
    int y,
    int neck_min_x,
    int neck_max_x,
    int mount_y
) noexcept {
    // A compact clamp is carved entirely from already-occupied saddle/neck
    // pixels by callers. Keep it deliberately narrower than the saddle mass
    // so it reads as attachment hardware rather than a cutout in the seat.
    const int mount_cx = (neck_min_x + neck_max_x) / 2;
    const int radius_x = ((neck_max_x - neck_min_x) / 2) + 1;
    const int dx = x - mount_cx;
    const int dy = y - mount_y;
    return dx * dx * 4 + dy * dy * radius_x * radius_x <=
           radius_x * radius_x * 4;
}

constexpr std::uint32_t authored_saddle_mount_color(
    int y,
    int mount_y
) noexcept {
    // Restraint matters here: bright neutral hardware looked like a hole in
    // the dark saddle at gameplay scale. Use a mid-metal upper lip and a
    // darker underside instead.
    if (y < mount_y) return 0xFFD0D5D9u;
    return 0xFF8E999Fu;
}

constexpr bool authored_wheel_spokes(
    int x,
    int y,
    int wheel_cx,
    int wheel_cy
) noexcept {
    return authored_segment_contains(
               x, y, wheel_cx - 22, wheel_cy, wheel_cx + 22, wheel_cy, 1
           ) ||
           authored_segment_contains(
               x, y, wheel_cx - 11, wheel_cy - 19,
               wheel_cx + 11, wheel_cy + 19, 1
           ) ||
           authored_segment_contains(
               x, y, wheel_cx + 11, wheel_cy - 19,
               wheel_cx - 11, wheel_cy + 19, 1
           );
}

constexpr bool authored_frame_brace(
    int x,
    int y,
    int crown_x,
    int crown_y,
    int wheel_cx,
    int wheel_cy
) noexcept {
    return authored_segment_contains(
               x, y, crown_x, crown_y, wheel_cx - 18, wheel_cy - 5, 3
           ) ||
           authored_segment_contains(
               x, y, crown_x, crown_y, wheel_cx + 18, wheel_cy - 5, 3
           );
}

constexpr bool authored_0541_p1_frame_brace(int x, int y) noexcept {
    return authored_segment_contains(x, y, 132, 60, 100, 116, 3) ||
           authored_segment_contains(x, y, 132, 60, 150, 116, 3);
}

constexpr bool authored_0541_p1_wheel_spokes(int x, int y) noexcept {
    return authored_wheel_spokes(x, y, 123, 122);
}

constexpr bool authored_p2_frame_brace(
    int x,
    int y,
    int wheel_cx,
    int crown_x
) noexcept {
    return authored_segment_contains(
        x, y, crown_x, 60, wheel_cx + 20, 116, 3
    );
}

constexpr bool authored_p2_wheel_spokes(
    int x,
    int y,
    int wheel_cx
) noexcept {
    return authored_wheel_spokes(x, y, wheel_cx, 120);
}

// First real authored Remastered candidate.
//
// This is intentionally representation-specific and still review-only. It
// follows the closed first-family visual-language baseline: smooth geometry,
// object-local baked lighting, dark rubber/vinyl masses, glossy colored metal,
// brighter neutral hardware, no host-space drop shadow and no sparkle glints.
//
// The candidate is authored at 4x density but remains registered to the same
// 64x64 guest object canvas. Runtime H/V is applied after representation
// selection, so the baked light travels with the sprite exactly as required.
constexpr std::uint32_t sample_racer_hd_authored_0541_p1(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Review-tuned wheel/contact geometry. Sampling this 4x asset at the
    // native presenter's logical pixel centres reproduces the stock 22..39 x
    // 3..38 occupied envelope and the recovered contact anchor x2/y2=61/76.
    // Keeping the envelope stable matters more in motion than preserving the
    // first pilot's oversized wheel mass.
    const int wheel_cx = 123;
    const int wheel_cy = 122;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 33 * 33 && wr2 >= 27 * 27;
    const bool rim = wr2 < 27 * 27 && wr2 >= 24 * 24;
    const bool hub = wr2 <= 6 * 6;

    // Slender fork with the same object-local lighting, now fitted to the
    // recovered gameplay-scale silhouette rather than the 64x64 OBJ canvas.
    const int fork_center = 131 - (y - 60) / 14;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 4 && x <= fork_center + 4;

    // Short crank and pedal. Neutral hardware may carry the brightest values.
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 138
    );
    const bool pedal = authored_pedal_contains(
        x, y, 138, 150
    );

    // The saddle is restored to the stock top-of-silhouette band. The original
    // pilot started five logical pixels too low when sampled for gameplay.
    const bool seat = authored_saddle_contains(
        x, y, 128, 22, 30, 18, 12, 32
    );

    // Colored upper frame/neck. Geometry is still smooth and authored, but its
    // sampled footprint follows the stock representation's scale and posture.
    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 128, 136, 29
        );
    const int crown_dx = x - 132;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10;
    const bool frame_brace = authored_0541_p1_frame_brace(x, y);
    const bool wheel_spokes = authored_0541_p1_wheel_spokes(x, y);

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 29);
    }
    if (seat) {
        return authored_saddle_color(x, y, 128, 22, 18);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 132, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0541_p1_companion_0d2d(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frame 1219 differs from the reviewed 1220 reference by only seven stock
    // logical pixels, all in the upper silhouette. Preserve the accepted lower
    // geometry/contact and vary only the saddle profile.
    const int wheel_cx = 123;
    const int wheel_cy = 122;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 33 * 33 && wr2 >= 27 * 27;
    const bool rim = wr2 < 27 * 27 && wr2 >= 24 * 24;
    const bool hub = wr2 <= 6 * 6;

    const int fork_center = 131 - (y - 60) / 14;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 4 && x <= fork_center + 4;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 138
    );
    const bool pedal = authored_pedal_contains(
        x, y, 138, 150
    );
    const bool seat = authored_saddle_contains(
        x, y, 130, 23, 32, 13, 8, 34
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 128, 136, 30
        );
    const int crown_dx = x - 132;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10;
    const bool frame_brace = authored_0541_p1_frame_brace(x, y);
    const bool wheel_spokes = authored_0541_p1_wheel_spokes(x, y);

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 30);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 23, 13);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 132, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0540_p1_predecessor(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frame 1218 is a larger pose transition than 1219->1220. Retained stock
    // evidence requires a one-logical-pixel rightward envelope/contact shift
    // plus local wheel/frame/saddle deformation. Material and lighting rules
    // remain identical to the two already-reviewed authored poses.
    const int wheel_cx = 128;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 126 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 141
    );
    const bool pedal = authored_pedal_contains(
        x, y, 141, 145
    );
    const bool seat = authored_saddle_contains(
        x, y, 130, 22, 35, 12, 8, 36
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 124 && x <= 132;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 124, 132, 29
        );
    const int crown_dx = x - 134;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 134, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 29);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 22, 12);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 134, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_057f_p1_companion_0d4a(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frames 1215-1216 are the next actual silhouette change before the
    // reviewed 1217/1218 pose. Preserve the established material and baked
    // object-local lighting language while fitting the recovered wider stock
    // envelope and right-shifted contact anchor.
    const int wheel_cx = 132;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 130 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 145
    );
    const bool pedal = authored_pedal_contains(
        x, y, 145, 149
    );

    // The repeated pose leans farther across the object-local canvas than the
    // 1217/1218 pose. Its saddle supplies the stock left envelope while the
    // wheel supplies the recovered right envelope/contact.
    // True-density mismatch review showed a small right-heavy saddle block
    // in this bridge pose. Shift/narrow it without touching envelope/contact.
    const bool seat = authored_saddle_contains(
        x, y, 120, 22, 32, 14, 8, 36
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 128, 136, 29
        );
    const int crown_dx = x - 136;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 136, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 29);
    }
    if (seat) {
        return authored_saddle_color(x, y, 120, 22, 14);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 136, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_057e_p1_with_p2_0543(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frames 1213-1214 are the next retained visual change before the accepted
    // 1215-1216 057F pose. The stock silhouette widens one logical pixel on
    // both sides and shifts wheel contact one pixel right; preserve the
    // established first-family materials and object-local baked lighting.
    const int wheel_cx = 136;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 134 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 149
    );
    const bool pedal = authored_pedal_contains(
        x, y, 149, 153
    );

    // Widen only the upper silhouette enough to recover the stock x=21 edge.
    // The wheel supplies x=42 and the recovered [67,76] contact anchor.
    // True-density review showed the old saddle carrying excess mass on
    // the right. Preserve the pose envelope/contact while shifting/narrowing
    // the same smooth object-local form.
    const bool seat = authored_saddle_contains(
        x, y, 116, 22, 32, 14, 8, 36
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 132 && x <= 140;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 132, 140, 29
        );
    const int crown_dx = x - 140;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 140, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 29);
    }
    if (seat) {
        return authored_saddle_color(x, y, 116, 22, 14);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 140, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_057d_p1_with_p2_0543(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frames 1207-1212 form the repeated 057D pose immediately before the
    // reviewed 057E state. Preserve the same first-family materials and
    // object-local lighting while fitting the stock one-pixel-right contact
    // advance and slightly lower top silhouette.
    const int wheel_cx = 140;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 134 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 153
    );
    const bool pedal = authored_pedal_contains(
        x, y, 153, 157
    );

    // The 057D mismatch map shows the same right-heavy saddle mass as
    // 057E. Shift left and narrow it while the wheel continues to own the
    // exact recovered contact anchor.
    const bool seat = authored_saddle_contains(
        x, y, 112, 26, 28, 14, 12, 40
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 136 && x <= 144;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 136, 144, 33
        );
    const int crown_dx = x - 144;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 144, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 33);
    }
    if (seat) {
        return authored_saddle_color(x, y, 112, 26, 14);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 144, 60, false, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0540_p2_baseline(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) return 0;
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    const int wheel_cx = 128;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 126 - (y - 60) / 11;
    const bool fork = y >= 60 && y <= 117 && x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 141
    );
    const bool pedal = authored_pedal_contains(
        x, y, 141, 145
    );
    const bool seat = authored_saddle_contains(
        x, y, 130, 22, 35, 12, 12, 36
    );

    const bool neck = y >= 30 && y <= 60 && x >= 124 && x <= 132;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 124, 132, 29
        );
    const int crown_dx = x - 134;
    const int crown_dy = y - 60;
    const bool crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 134, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    if (crank || pedal) return authored_drivetrain_hardware_color(y, wheel_cy);
    if (rim || wheel_spokes) return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 29);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 22, 12);
    }
    if (crown) return authored_frame_junction_color(x, y, 134, 60, true, fork || frame_brace || neck);
    if (fork || frame_brace || neck) return authored_blue_frame_color(x, y);
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0541_p2_predecessor(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // Frame 1218 P2 advances one logical pixel left from the reviewed 0540
    // baseline while keeping the same vertical posture. Preserve the accepted
    // P2 materials/lighting and express that stock-measured contact shift as a
    // four-source-pixel object-local translation.
    const int wheel_cx = 124;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 122 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 137
    );
    const bool pedal = authored_pedal_contains(
        x, y, 137, 141
    );

    // The P2 0541 transition pose is over-broad on the left/top at true
    // density. Shift right/down and narrow the saddle while preserving the
    // stock-derived envelope/contact through the wheel/fork structure.
    const bool seat = authored_saddle_contains(
        x, y, 130, 26, 30, 12, 12, 40
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 120 && x <= 128;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 120, 128, 33
        );
    const int crown_dx = x - 130;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_frame_brace(
        x, y, 130, 60, wheel_cx, wheel_cy
    );
    const bool wheel_spokes = authored_wheel_spokes(
        x, y, wheel_cx, wheel_cy
    );

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 33);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 26, 12);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 130, 60, true, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_blue_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0542_p2(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    // The two registered 0542 P2 contexts are byte-identical stock art.
    // Fit one authored pose to the shared stock envelope/contact and reuse it
    // under both exact synchronized guards.
    const int wheel_cx = 120;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 35 * 35 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 118 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 133
    );
    const bool pedal = authored_pedal_contains(
        x, y, 133, 137
    );
    const bool seat = authored_saddle_contains(
        x, y, 130, 26, 35, 14, 16, 40
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 116 && x <= 124;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 116, 124, 33
        );
    const int crown_dx = x - 126;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_p2_frame_brace(x, y, 120, 126);
    const bool wheel_spokes = authored_p2_wheel_spokes(x, y, 120);

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 33);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 26, 14);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 126, 60, true, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_blue_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_authored_0543_p2(
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (x < 0 || y < 0 || x >= kRacerHdAssetSize || y >= kRacerHdAssetSize) {
        return 0;
    }
    if (hflip) x = kRacerHdAssetSize - 1 - x;
    if (vflip) y = kRacerHdAssetSize - 1 - y;

    const int wheel_cx = 116;
    const int wheel_cy = 120;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 36 * 36 && wr2 >= 25 * 25;
    const bool rim = wr2 < 25 * 25 && wr2 >= 22 * 22;
    const bool hub = wr2 <= 5 * 5;

    const int fork_center = 116 - (y - 60) / 11;
    const bool fork =
        y >= 60 && y <= 117 &&
        x >= fork_center - 5 && x <= fork_center + 5;
    const bool crank = authored_crank_contains(
        x, y, wheel_cx, wheel_cy, 131
    );
    const bool pedal = authored_pedal_contains(
        x, y, 131, 135
    );
    const bool seat = authored_saddle_contains(
        x, y, 130, 30, 35, 12, 16, 40
    );

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 114 && x <= 122;
    const bool saddle_mount =
        (seat || neck) &&
        authored_saddle_mount_contains(
            x, y, 114, 122, 37
        );
    const int crown_dx = x - 124;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;
    const bool frame_brace = authored_p2_frame_brace(x, y, 116, 124);
    const bool wheel_spokes = authored_p2_wheel_spokes(x, y, 116);

    if (hub) {
        return authored_hub_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (crank || pedal) {
        return authored_drivetrain_hardware_color(y, wheel_cy);
    }
    if (rim || wheel_spokes) {
        return authored_rim_hardware_color(x, y, wheel_cx, wheel_cy);
    }
    if (saddle_mount) {
        return authored_saddle_mount_color(y, 37);
    }
    if (seat) {
        return authored_saddle_color(x, y, 130, 30, 12);
    }
    if (crown) {
        return authored_frame_junction_color(x, y, 124, 60, true, fork || frame_brace || neck);
    }
    if (fork || frame_brace || neck) {
        return authored_blue_frame_color(x, y);
    }
    if (tire) {
        return authored_rubber_color(x, y, wheel_cx, wheel_cy);
    }
    return 0;
}

constexpr std::uint32_t sample_racer_hd_asset(
    const RacerRegistration& registration,
    int x,
    int y,
    bool hflip,
    bool vflip
) noexcept {
    if (is_first_authored_remastered_registration(registration)) {
        return sample_racer_hd_authored_0541_p1(x, y, hflip, vflip);
    }
    if (is_authored_0540_p2_baseline_registration(registration)) {
        return sample_racer_hd_authored_0540_p2_baseline(x, y, hflip, vflip);
    }
    if (is_authored_0540_p2_companion_0d2d_registration(registration)) {
        // Frame 1219 P2 is byte-identical to the reviewed frame-1220 P2
        // raster. Preserve its exact synchronized identity while reusing the
        // same authored blue-player representation.
        return sample_racer_hd_authored_0540_p2_baseline(x, y, hflip, vflip);
    }
    if (is_authored_0541_p2_predecessor_registration(registration)) {
        return sample_racer_hd_authored_0541_p2_predecessor(
            x, y, hflip, vflip
        );
    }
    if (
        is_authored_0542_p2_companion_0d2c_registration(registration) ||
        is_authored_0542_p2_companion_0d4a_registration(registration)
    ) {
        return sample_racer_hd_authored_0542_p2(x, y, hflip, vflip);
    }
    if (
        is_authored_0543_p2_057d_registration(registration) ||
        is_authored_0543_p2_057e_registration(registration)
    ) {
        return sample_racer_hd_authored_0543_p2(x, y, hflip, vflip);
    }
    if (is_authored_0541_p1_companion_0d2d_registration(registration)) {
        return sample_racer_hd_authored_0541_p1_companion_0d2d(
            x, y, hflip, vflip
        );
    }
    if (is_authored_057f_p1_companion_0d4a_registration(registration)) {
        return sample_racer_hd_authored_057f_p1_companion_0d4a(
            x, y, hflip, vflip
        );
    }
    if (is_authored_057e_p1_with_p2_0543_registration(registration)) {
        return sample_racer_hd_authored_057e_p1_with_p2_0543(
            x, y, hflip, vflip
        );
    }
    if (is_authored_057d_p1_with_p2_0543_registration(registration)) {
        return sample_racer_hd_authored_057d_p1_with_p2_0543(
            x, y, hflip, vflip
        );
    }
    if (is_authored_0540_p1_predecessor_registration(registration) ||
        is_authored_0540_p1_companion_0d2c_with_p2_0542_registration(
            registration
        )) {
        // The two exact synchronized contexts have byte-identical stock P1
        // rasters, so they intentionally share one reviewed authored asset.
        return sample_racer_hd_authored_0540_p1_predecessor(
            x, y, hflip, vflip
        );
    }
    return sample_racer_hd_contract_candidate(x, y, hflip, vflip);
}

constexpr std::uint32_t sample_racer_hd_scaled_asset(
    const RacerRegistration& registration,
    int output_x,
    int output_y,
    int scale,
    bool hflip,
    bool vflip
) noexcept {
    if (!valid_racer_hd_internal_render_scale(scale) ||
        output_x < 0 || output_y < 0 ||
        output_x >= kRacerHdLogicalSize * scale ||
        output_y >= kRacerHdLogicalSize * scale) {
        return 0;
    }
    const int sx = racer_hd_scaled_sample_coordinate(output_x, scale);
    const int sy = racer_hd_scaled_sample_coordinate(output_y, scale);
    return sample_racer_hd_asset(registration, sx, sy, hflip, vflip);
}

constexpr std::uint32_t sample_racer_hd_presented_pixel(
    const RacerRegistration& registration,
    const RacerOamPlacement& placement,
    int screen_x,
    int screen_y
) noexcept {
    const int lx = screen_x - static_cast<int>(placement.x_signed);
    const int ly = screen_y - static_cast<int>(placement.y_raw_8bit);
    if (lx < 0 || ly < 0 ||
        lx >= kRacerHdLogicalSize || ly >= kRacerHdLogicalSize) {
        return 0;
    }
    const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
    const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
    return sample_racer_hd_asset(registration, sx, sy, placement.hflip, placement.vflip);
}

// Host callbacks. They are inert unless UR_RACER_HD is enabled.
void racer_hd_prepare_frame(
    int drawable_w,
    int drawable_h,
    int* frame_w,
    int* frame_h
) noexcept;

bool racer_hd_set_internal_render_scale(int scale) noexcept;
int racer_hd_internal_render_scale() noexcept;
int racer_hd_presentation_scale() noexcept;

void racer_hd_begin_sim_frame(unsigned number) noexcept;

int racer_hd_draw_frame(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int frame_w,
    int frame_h,
    double alpha
) noexcept;

}  // namespace ur::presentation

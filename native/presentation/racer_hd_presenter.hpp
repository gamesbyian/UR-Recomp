#pragma once

#include <cstddef>
#include <cstdint>

#include "racer_oam_placement.hpp"
#include "racer_replacement_selector.hpp"

namespace ur::presentation {

inline constexpr int kRacerHdDensityScale = 4;
inline constexpr int kRacerHdLogicalSize = 64;
inline constexpr int kRacerHdAssetSize = kRacerHdLogicalSize * kRacerHdDensityScale;

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

constexpr bool authored_0541_p1_frame_brace(int x, int y) noexcept {
    return authored_segment_contains(x, y, 132, 60, 100, 116, 3) ||
           authored_segment_contains(x, y, 132, 60, 150, 116, 3);
}

constexpr bool authored_0541_p1_wheel_spokes(int x, int y) noexcept {
    return authored_segment_contains(x, y, 101, 122, 145, 122, 2) ||
           authored_segment_contains(x, y, 112, 103, 134, 141, 2) ||
           authored_segment_contains(x, y, 134, 103, 112, 141, 2);
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 112 && x <= 138;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 138 && x <= 150;

    // The saddle is restored to the stock top-of-silhouette band. The original
    // pilot started five logical pixels too low when sampled for gameplay.
    const int seat_dx = x - 128;
    const int seat_dy = y - 22;
    const bool seat =
        ((seat_dx * seat_dx) * 11 + (seat_dy * seat_dy) * 30 <= 30 * 30 * 11) &&
        y >= 12 && y <= 32;

    // Colored upper frame/neck. Geometry is still smooth and authored, but its
    // sampled footprint follows the stock representation's scale and posture.
    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const int crown_dx = x - 132;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10;
    const bool frame_brace = authored_0541_p1_frame_brace(x, y);
    const bool wheel_spokes = authored_0541_p1_wheel_spokes(x, y);

    if (hub || rim || crank || pedal || wheel_spokes) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || frame_brace || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 112 && x <= 138;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 138 && x <= 150;

    const int seat_dx = x - 130;
    const int seat_dy = y - 23;
    const bool seat =
        (seat_dx * seat_dx) * 13 * 13 +
            (seat_dy * seat_dy) * 32 * 32 <=
            32 * 32 * 13 * 13 &&
        y >= 8 && y <= 34;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const int crown_dx = x - 132;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10;
    const bool frame_brace = authored_0541_p1_frame_brace(x, y);
    const bool wheel_spokes = authored_0541_p1_wheel_spokes(x, y);

    if (hub || rim || crank || pedal || wheel_spokes) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || frame_brace || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 111 && x <= 140;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 141 && x <= 145;

    const int seat_dx = x - 130;
    const int seat_dy = y - 22;
    const bool seat =
        (seat_dx * seat_dx) * 12 * 12 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 12 * 12 &&
        y >= 8 && y <= 36;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 124 && x <= 132;
    const int crown_dx = x - 134;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 115 && x <= 144;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 145 && x <= 149;

    // The repeated pose leans farther across the object-local canvas than the
    // 1217/1218 pose. Its saddle supplies the stock left envelope while the
    // wheel supplies the recovered right envelope/contact.
    const int seat_dx = x - 124;
    const int seat_dy = y - 22;
    const bool seat =
        (seat_dx * seat_dx) * 14 * 14 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 14 * 14 &&
        y >= 8 && y <= 36;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 128 && x <= 136;
    const int crown_dx = x - 136;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 119 && x <= 148;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 149 && x <= 153;

    // Widen only the upper silhouette enough to recover the stock x=21 edge.
    // The wheel supplies x=42 and the recovered [67,76] contact anchor.
    const int seat_dx = x - 124;
    const int seat_dy = y - 22;
    const bool seat =
        (seat_dx * seat_dx) * 14 * 14 +
            (seat_dy * seat_dy) * 39 * 39 <=
            39 * 39 * 14 * 14 &&
        y >= 8 && y <= 36;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 132 && x <= 140;
    const int crown_dx = x - 140;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 123 && x <= 152;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 153 && x <= 157;

    const int seat_dx = x - 120;
    const int seat_dy = y - 26;
    const bool seat =
        (seat_dx * seat_dx) * 14 * 14 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 14 * 14 &&
        y >= 12 && y <= 40;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 136 && x <= 144;
    const int crown_dx = x - 144;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_red_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank = y >= 116 && y <= 123 && x >= 111 && x <= 140;
    const bool pedal = y >= 113 && y <= 118 && x >= 141 && x <= 145;

    const int seat_dx = x - 130;
    const int seat_dy = y - 22;
    const bool seat =
        (seat_dx * seat_dx) * 12 * 12 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 12 * 12 &&
        y >= 12 && y <= 36;

    const bool neck = y >= 30 && y <= 60 && x >= 124 && x <= 132;
    const int crown_dx = x - 134;
    const int crown_dy = y - 60;
    const bool crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) return authored_metal_color(x, y);
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) return authored_blue_frame_color(x, y);
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 107 && x <= 136;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 137 && x <= 141;

    const int seat_dx = x - 126;
    const int seat_dy = y - 22;
    const bool seat =
        (seat_dx * seat_dx) * 12 * 12 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 12 * 12 &&
        y >= 12 && y <= 36;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 120 && x <= 128;
    const int crown_dx = x - 130;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_blue_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 103 && x <= 132;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 133 && x <= 137;

    const int seat_dx = x - 130;
    const int seat_dy = y - 26;
    const bool seat =
        (seat_dx * seat_dx) * 14 * 14 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 14 * 14 &&
        y >= 16 && y <= 40;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 116 && x <= 124;
    const int crown_dx = x - 126;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) {
        return authored_metal_color(x, y);
    }
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) {
        return authored_blue_frame_color(x, y);
    }
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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
    const bool crank =
        y >= 116 && y <= 123 &&
        x >= 101 && x <= 130;
    const bool pedal =
        y >= 113 && y <= 118 &&
        x >= 131 && x <= 135;

    const int seat_dx = x - 130;
    const int seat_dy = y - 30;
    const bool seat =
        (seat_dx * seat_dx) * 12 * 12 +
            (seat_dy * seat_dy) * 35 * 35 <=
            35 * 35 * 12 * 12 &&
        y >= 16 && y <= 40;

    const bool neck =
        y >= 30 && y <= 60 &&
        x >= 114 && x <= 122;
    const int crown_dx = x - 124;
    const int crown_dy = y - 60;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8;

    if (hub || rim || crank || pedal) return authored_metal_color(x, y);
    if (seat) {
        const int seat_light = (255 - x) + (255 - y);
        return seat_light > 350 ? 0xFF41474Bu : 0xFF20272Bu;
    }
    if (fork || neck || crown) return authored_blue_frame_color(x, y);
    if (tire) {
        const int tire_light = (255 - x) + (255 - y);
        return tire_light > 310 ? 0xFF353C40u : 0xFF171D20u;
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

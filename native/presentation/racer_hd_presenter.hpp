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

constexpr std::uint32_t authored_metal_color(
    int x,
    int y
) noexcept {
    const int light = (255 - x) + (255 - y);
    if (light > 305) return 0xFFF2F4F6u;
    if (light > 275) return 0xFFD0D5D9u;
    return 0xFF8E999Fu;
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

    // Wheel/contact geometry. Bottom point is y=155 (logical centre 38.5),
    // matching the recovered contact target y2=76 after 4x sampling.
    const int wheel_cx = 124;
    const int wheel_cy = 116;
    const int wx = x - wheel_cx;
    const int wy = y - wheel_cy;
    const int wr2 = wx * wx + wy * wy;
    const bool tire = wr2 <= 39 * 39 && wr2 >= 31 * 31;
    const bool rim = wr2 < 31 * 31 && wr2 >= 28 * 28;
    const bool hub = wr2 <= 7 * 7;

    // Slender fork with a slight authored lean. This is the smooth high-density
    // form that the contract placeholder could not express.
    const int fork_center = 122 + (112 - y) / 18;
    const bool fork =
        y >= 54 && y <= 111 &&
        x >= fork_center - 4 && x <= fork_center + 4;

    // Short crank and pedal. Neutral hardware may carry the brightest values.
    const bool crank =
        y >= 108 && y <= 115 &&
        x >= 111 && x <= 137;
    const bool pedal =
        y >= 105 && y <= 110 &&
        x >= 137 && x <= 149;

    // Dark saddle, intentionally broad and low-detail at gameplay scale.
    const int seat_dx = x - 116;
    const int seat_dy = y - 43;
    const bool seat =
        ((seat_dx * seat_dx) * 9 + (seat_dy * seat_dy) * 64 <= 30 * 30 * 9) &&
        y >= 34 && y <= 50;

    // Colored upper frame/neck. Its silhouette is separate from the dark saddle
    // and neutral hardware so the material hierarchy survives downscaling.
    const bool neck =
        y >= 47 && y <= 70 &&
        x >= 115 && x <= 130;
    const int crown_dx = x - 123;
    const int crown_dy = y - 67;
    const bool crown =
        crown_dx * crown_dx + crown_dy * crown_dy <= 12 * 12;

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

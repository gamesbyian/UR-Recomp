#pragma once

#include <cstddef>
#include <cstdint>

#include "racer_oam_placement.hpp"

namespace ur::presentation {

inline constexpr int kRacerHdDensityScale = 4;
inline constexpr int kRacerHdLogicalSize = 64;
inline constexpr int kRacerHdAssetSize = kRacerHdLogicalSize * kRacerHdDensityScale;

constexpr bool racer_hd_asset_available(std::uint16_t semantic_frame_id) noexcept {
    return semantic_frame_id == 0x0541 || semantic_frame_id == 0x0540;
}

// Deterministic contract-only art. Returning 0 means transparent.
// H/V orientation is deliberately applied here, after semantic selection.
constexpr std::uint32_t sample_racer_hd_asset(
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

    // A simple HD unicycle-like placeholder with a deliberately asymmetric
    // fork/marker so orientation tests cannot pass accidentally.
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

constexpr std::uint32_t sample_racer_hd_presented_pixel(
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
    return sample_racer_hd_asset(sx, sy, placement.hflip, placement.vflip);
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

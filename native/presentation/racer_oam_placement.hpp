#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::presentation {

enum class RacerViewport : std::uint8_t {
    Top = 0,
    Bottom = 1,
};

// The host decides the logical frame dimensions before begin_sim_frame.
// OBJ RemoveFromGame must never be activated for a geometry that the HD
// draw_frame callback will decline: the underlying stock sprites would
// already be absent from the captured framebuffer.
constexpr bool racer_hd_can_capture_frame_geometry(
    int logical_width,
    int logical_height
) noexcept {
    return logical_width == 256 && logical_height == 224;
}


// The $2104 HDMA split switches visible OBJ pairs on scanline 112.
// Clip host-owned replacements to the same physical half-frame so a large
// racer at the seam cannot leak into the other viewport. Scaling changes
// raster density only; it must never move the original scanline boundary.
// Within one SNES OBJ priority level, smaller OAM slots win sprite-to-
// sprite overlap. Back-to-front host painting must therefore visit the
// larger slot first (the slot's palette/priority bits do not change this).
// SNES sprite line selection compares (scanline - OAM Y) modulo 256.
// A 64px OBJ starting at Y=250 therefore reappears at display row zero
// after six asset rows. Keep the 256-line hardware wrap independent of the
// 224-line visible field and the scanline-112 split-screen ownership.
constexpr int racer_obj_wrapped_output_row(
    std::uint8_t raw_y,
    int asset_output_row,
    int output_scale
) noexcept {
    if (output_scale < 1 || output_scale > 4 || asset_output_row < 0 ||
        asset_output_row >= 64 * output_scale) return -1;
    const int row =
        (static_cast<int>(raw_y) * output_scale + asset_output_row) %
        (256 * output_scale);
    return row < 224 * output_scale ? row : -1;
}

constexpr bool racer_obj_paints_behind(
    std::uint8_t first_slot,
    std::uint8_t second_slot
) noexcept {
    return first_slot > second_slot;
}

constexpr bool racer_split_viewport_contains_row(
    RacerViewport viewport,
    int output_row,
    int output_scale
) noexcept {
    if (output_row < 0 || output_scale <= 0) return false;
    const int logical_row = output_row / output_scale;
    if (logical_row >= 224) return false;
    return viewport == RacerViewport::Top
        ? logical_row < 112
        : logical_row >= 112;
}

struct RacerOamPlacement {
    std::uint8_t slot;
    std::uint16_t x_raw_9bit;
    std::int16_t x_signed;
    std::uint8_t y_raw_8bit;
    std::uint8_t tile;
    std::uint8_t attr;
    bool hflip;
    bool vflip;
    bool large;
    std::uint8_t width_pixels;
    std::uint8_t height_pixels;
};

// P1 owns contiguous OAM slots 97 (bottom) and 98 (top). The current
// extractor can capture exactly these two slots and leave P2 stock. The
// bottom viewport is the hard case: stock P2 slot 96 is in front of P1 97,
// so a host-drawn P1 cannot cover it. Without a separate stock-P2 overlay
// plane, admit P1-only replacements only if their *visible* OBJ rectangles
// cannot overlap there. Y is compared modulo the hardware's 256 lines.
// An ambiguous or malformed placement is unsafe, never a green light.
constexpr bool racer_p1_only_no_stock_p2_occlusion(
    const RacerOamPlacement& p1_top,
    const RacerOamPlacement& p1_bottom,
    const RacerOamPlacement& p2_top,
    const RacerOamPlacement& p2_bottom
) noexcept {
    if (p1_top.slot != 98 || p1_bottom.slot != 97 ||
        p2_top.slot != 99 || p2_bottom.slot != 96 ||
        !p1_top.large || !p1_bottom.large ||
        p1_top.width_pixels != 64 || p1_top.height_pixels != 64 ||
        p1_bottom.width_pixels != 64 || p1_bottom.height_pixels != 64 ||
        !p2_top.large || !p2_bottom.large ||
        p2_top.width_pixels != 64 || p2_top.height_pixels != 64 ||
        p2_bottom.width_pixels != 64 || p2_bottom.height_pixels != 64 ||
        // Exact title-owned P1/P2 racer graphic bank tile families,
        // recovered from the race-init VRAM $0000/$1000 OBJ payloads.
        (p1_top.tile != 0x00 && p1_top.tile != 0x08) ||
        (p1_bottom.tile != 0x00 && p1_bottom.tile != 0x08) ||
        (p2_top.tile != 0x80 && p2_top.tile != 0x88) ||
        (p2_bottom.tile != 0x80 && p2_bottom.tile != 0x88) ||
        // P1 top slot 98 wins over stock P2 slot 99 only within the same
        // SNES OBJ priority level. Different OBJ levels are not modeled.
        (p1_top.attr & 0x30) != (p2_top.attr & 0x30)) {
        return false;
    }
    // In this title's proven OBSEL=$83 mode, the other split pair is
    // reduced to a 16x16 OBJ, not hidden by the PPU. Capturing both P1
    // slots removes even an out-of-viewport *small* copy. Refuse the
    // exceptional raw Y values where that small copy would be visible
    // in the opposite half without an HD replacement there.
    for (int y = 0; y < 112; ++y) {
        if (((y - p1_bottom.y_raw_8bit) & 0xFF) < 16) return false;
    }
    for (int y = 112; y < 224; ++y) {
        if (((y - p1_top.y_raw_8bit) & 0xFF) < 16) return false;
    }
    // Reject only a *provably impossible* horizontal intersection. X is
    // already decoded from the nine-bit signed OAM coordinate.
    const int p1_left = static_cast<int>(p1_bottom.x_signed);
    const int p2_left = static_cast<int>(p2_bottom.x_signed);
    const int left = p1_left > p2_left ? p1_left : p2_left;
    const int p1_right = p1_left + p1_bottom.width_pixels;
    const int p2_right = p2_left + p2_bottom.width_pixels;
    const int right = p1_right < p2_right ? p1_right : p2_right;
    if (left >= right || right <= 0 || left >= 256) return true;

    // The rasterized bottom viewport is exactly scanlines 112..223.
    // Sprite rows at raw Y 250..255 can wrap to Y 0..57.
    for (int y = 112; y < 224; ++y) {
        const int p1_row = (y - p1_bottom.y_raw_8bit) & 0xFF;
        const int p2_row = (y - p2_bottom.y_raw_8bit) & 0xFF;
        if (p1_row < p1_bottom.height_pixels &&
            p2_row < p2_bottom.height_pixels) return false;
    }
    return true;
}

std::optional<RacerOamPlacement> decode_racer_oam_placement(
    const std::uint8_t* oam,
    std::size_t oam_size,
    std::uint8_t obsel,
    std::uint8_t player
) noexcept;

std::optional<RacerOamPlacement> decode_racer_ppu_placement(
    const std::uint16_t* oam_words,
    std::size_t oam_word_count,
    const std::uint8_t* high_oam,
    std::size_t high_oam_size,
    std::uint8_t obsel,
    std::uint8_t player
) noexcept;

std::optional<RacerOamPlacement> decode_racer_split_ppu_placement(
    const std::uint16_t* oam_words,
    std::size_t oam_word_count,
    std::uint8_t obsel,
    std::uint8_t player,
    RacerViewport viewport
) noexcept;

}  // namespace ur::presentation

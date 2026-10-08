#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::presentation {

enum class RacerViewport : std::uint8_t {
    Top = 0,
    Bottom = 1,
};

// The $2104 HDMA split switches visible OBJ pairs on scanline 112.
// Clip host-owned replacements to the same physical half-frame so a large
// racer at the seam cannot leak into the other viewport. Scaling changes
// raster density only; it must never move the original scanline boundary.
// Within one SNES OBJ priority level, smaller OAM slots win sprite-to-
// sprite overlap. Back-to-front host painting must therefore visit the
// larger slot first (the slot's palette/priority bits do not change this).
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

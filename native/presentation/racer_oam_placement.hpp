#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::presentation {

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

}  // namespace ur::presentation

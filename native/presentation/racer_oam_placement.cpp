#include "racer_oam_placement.hpp"

namespace ur::presentation {
namespace {

constexpr std::size_t kOamBytes = 544;
constexpr std::uint8_t kP1Slot = 98;
constexpr std::uint8_t kP2Slot = 99;

struct SizePair {
    std::uint8_t small_w;
    std::uint8_t small_h;
    std::uint8_t large_w;
    std::uint8_t large_h;
};

constexpr SizePair kSizePairs[8] = {
    {8, 8, 16, 16},
    {8, 8, 32, 32},
    {8, 8, 64, 64},
    {16, 16, 32, 32},
    {16, 16, 64, 64},
    {32, 32, 64, 64},
    {16, 32, 32, 64},
    {16, 32, 32, 32},
};

}  // namespace

std::optional<RacerOamPlacement> build_placement(
    std::uint8_t slot,
    std::uint8_t xlo,
    std::uint8_t y,
    std::uint8_t tile,
    std::uint8_t attr,
    std::uint8_t pair,
    std::uint8_t obsel
) noexcept {
    const std::uint16_t x =
        static_cast<std::uint16_t>(
            xlo | ((pair & 0x01) != 0 ? 0x100 : 0x000)
        );
    const bool large = (pair & 0x02) != 0;
    const SizePair sizes = kSizePairs[(obsel >> 5) & 0x07];

    RacerOamPlacement out{};
    out.slot = slot;
    out.x_raw_9bit = x;
    out.x_signed = static_cast<std::int16_t>(x >= 256 ? x - 512 : x);
    out.y_raw_8bit = y;
    out.tile = tile;
    out.attr = attr;
    out.hflip = (attr & 0x40) != 0;
    out.vflip = (attr & 0x80) != 0;
    out.large = large;
    out.width_pixels = large ? sizes.large_w : sizes.small_w;
    out.height_pixels = large ? sizes.large_h : sizes.small_h;
    return out;
}

std::optional<RacerOamPlacement> decode_racer_ppu_placement(
    const std::uint16_t* oam_words,
    std::size_t oam_word_count,
    const std::uint8_t* high_oam,
    std::size_t high_oam_size,
    std::uint8_t obsel,
    std::uint8_t player
) noexcept {
    if (oam_words == nullptr || high_oam == nullptr ||
        oam_word_count < 256 || high_oam_size < 32 ||
        (player != 1 && player != 2)) {
        return std::nullopt;
    }

    const std::uint8_t slot = player == 1 ? kP1Slot : kP2Slot;
    const std::uint16_t pos = oam_words[static_cast<std::size_t>(slot) * 2];
    const std::uint16_t chr = oam_words[static_cast<std::size_t>(slot) * 2 + 1];
    const std::uint8_t xlo = static_cast<std::uint8_t>(pos & 0xFF);
    const std::uint8_t y = static_cast<std::uint8_t>(pos >> 8);
    const std::uint8_t tile = static_cast<std::uint8_t>(chr & 0xFF);
    const std::uint8_t attr = static_cast<std::uint8_t>(chr >> 8);
    const std::uint8_t pair =
        static_cast<std::uint8_t>(
            (high_oam[slot / 4] >> ((slot % 4) * 2)) & 0x03
        );

    return build_placement(slot, xlo, y, tile, attr, pair, obsel);
}

std::optional<RacerOamPlacement> decode_racer_oam_placement(
    const std::uint8_t* oam,
    std::size_t oam_size,
    std::uint8_t obsel,
    std::uint8_t player
) noexcept {
    if (oam == nullptr || oam_size < kOamBytes || (player != 1 && player != 2)) {
        return std::nullopt;
    }

    const std::uint8_t slot = player == 1 ? kP1Slot : kP2Slot;
    const std::size_t q = static_cast<std::size_t>(slot) * 4;
    const std::uint8_t xlo = oam[q + 0];
    const std::uint8_t y = oam[q + 1];
    const std::uint8_t tile = oam[q + 2];
    const std::uint8_t attr = oam[q + 3];

    const std::uint8_t pair =
        static_cast<std::uint8_t>(
            (oam[0x200 + slot / 4] >> ((slot % 4) * 2)) & 0x03
        );
    return build_placement(slot, xlo, y, tile, attr, pair, obsel);
}

}  // namespace ur::presentation

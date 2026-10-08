#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::title {

// Read-only projection of the stock per-rider tour-unlock tier.
//
// Stock SRAM 0x10D3..0x10E2 stores one tier per rider (0: first four,
// 1: first six, 2: all eight ordinary tours, 3: includes secret Hunter).
// The host deliberately does not expose Hunter through Quick Practice: its
// separate discovery/product policy remains closed. No SRAM is written here.
//
// Returned bits are stock TOUR_SELECT option IDs (not catalog block indexes).
constexpr std::optional<std::uint16_t> stock_practice_tour_option_mask(
    const std::uint8_t* sram,
    std::size_t sram_size,
    std::uint8_t rider_index
) noexcept {
    constexpr std::size_t kStockSramBytes = 8192;
    constexpr std::size_t kRiderIndexOffset = 0x0748;
    constexpr std::size_t kTourUnlockTierBase = 0x10D3;
    if (!sram || sram_size != kStockSramBytes || rider_index >= 16 ||
        sram[kRiderIndexOffset] != rider_index) {
        return std::nullopt;
    }
    const auto tier = sram[kTourUnlockTierBase + rider_index];
    if (tier > 3) return std::nullopt;

    constexpr std::uint16_t kInitial =
        (1u << 0) | (1u << 2) | (1u << 4) | (1u << 6);
    constexpr std::uint16_t kBronze =
        (1u << 1) | (1u << 3);
    constexpr std::uint16_t kSilver =
        (1u << 5) | (1u << 7);

    std::uint16_t allowed = kInitial;
    if (tier >= 1) allowed |= kBronze;
    if (tier >= 2) allowed |= kSilver;
    // Tier 3 does not opt the Modern Practice picker into Hunter.
    return allowed;
}

}  // namespace ur::title

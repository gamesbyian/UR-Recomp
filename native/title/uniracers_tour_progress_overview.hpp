#pragma once

#include "uniracers_practice_tour_unlock.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::title {

// Eight ordinary stock tours only. Hunter remains a discovery reward and
// must never be inferred from its medal cell by an administrative overlay.
struct StockTourProgressOverview {
    bool valid = false;
    std::uint8_t rider_index = 0;
    std::uint16_t visible_tour_options = 0;
    std::array<std::uint8_t, 8> medal_tiers{};
    unsigned bronze_or_better = 0;
    unsigned silver_or_better = 0;
    unsigned gold = 0;
};

constexpr StockTourProgressOverview observe_stock_tour_progress_overview(
    const std::uint8_t* sram,
    std::size_t sram_size,
    std::uint8_t rider_index
) noexcept {
    StockTourProgressOverview out{};
    const auto visibility = stock_practice_tour_option_mask(
        sram, sram_size, rider_index);
    if (!visibility) return out;

    constexpr std::size_t kMedalBase = 0x069C;
    constexpr std::size_t kRidersPerTour = 16;
    out.rider_index = rider_index;
    out.visible_tour_options = *visibility;
    for (std::size_t tour_option = 0; tour_option < 8; ++tour_option) {
        const auto medal = sram[kMedalBase +
            tour_option * kRidersPerTour + rider_index];
        if (medal > 3) return {};
        out.medal_tiers[tour_option] = medal;
        if (medal >= 1) ++out.bronze_or_better;
        if (medal >= 2) ++out.silver_or_better;
        if (medal >= 3) ++out.gold;
    }
    out.valid = true;
    return out;
}

constexpr bool stock_tour_progress_visible(
    const StockTourProgressOverview& overview,
    std::uint8_t tour_option
) noexcept {
    return overview.valid && tour_option < 8 &&
        (overview.visible_tour_options &
            (std::uint16_t{1} << tour_option)) != 0;
}

constexpr const char* stock_tour_progress_medal_name(
    const StockTourProgressOverview& overview,
    std::uint8_t tour_option
) noexcept {
    if (!stock_tour_progress_visible(overview, tour_option)) return "LOCKED";
    switch (overview.medal_tiers[tour_option]) {
    case 0: return "NOT STARTED";
    case 1: return "BRONZE";
    case 2: return "SILVER";
    case 3: return "GOLD";
    default: return "UNAVAILABLE";
    }
}

}  // namespace ur::title

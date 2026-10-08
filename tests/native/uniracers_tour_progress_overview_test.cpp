#include "uniracers_tour_progress_overview.hpp"
#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::title;

int main() {
    std::array<std::uint8_t, 8192> sram{};
    sram[0x0748] = 0x48; // retained clean-save rider sentinel
    auto start = observe_stock_tour_progress_overview(sram.data(), sram.size(), 0);
    assert(start.valid);
    assert(start.bronze_or_better == 0 && start.silver_or_better == 0 && start.gold == 0);
    for (const auto option : {0u, 2u, 4u, 6u}) {
        assert(stock_tour_progress_visible(start, static_cast<std::uint8_t>(option)));
    }
    for (const auto option : {1u, 3u, 5u, 7u}) {
        assert(!stock_tour_progress_visible(start, static_cast<std::uint8_t>(option)));
    }
    assert(!stock_tour_progress_visible(start, 8));
    assert(stock_tour_progress_medal_name(start, 1)[0] == 'L');

    sram[0x0748] = 3;
    const std::size_t rider = 3;
    sram[0x10D3 + rider] = 1;
    sram[0x069C + 16*0 + rider] = 1;
    sram[0x069C + 16*2 + rider] = 2;
    sram[0x069C + 16*4 + rider] = 3;
    auto progress = observe_stock_tour_progress_overview(sram.data(), sram.size(), rider);
    assert(progress.valid);
    assert(progress.bronze_or_better == 3 && progress.silver_or_better == 2 && progress.gold == 1);
    assert(stock_tour_progress_visible(progress, 1));
    assert(!stock_tour_progress_visible(progress, 5));
    assert(stock_tour_progress_medal_name(progress, 0)[0] == 'B');
    assert(stock_tour_progress_medal_name(progress, 2)[0] == 'S');
    assert(stock_tour_progress_medal_name(progress, 4)[0] == 'G');
    assert(stock_tour_progress_medal_name(progress, 5)[0] == 'L');

    sram[0x10D3 + rider] = 3;
    progress = observe_stock_tour_progress_overview(sram.data(), sram.size(), rider);
    assert(progress.valid);
    for (std::uint8_t option = 0; option < 8; ++option) {
        assert(stock_tour_progress_visible(progress, option));
    }
    assert(!stock_tour_progress_visible(progress, 8));

    sram[0x069C + 16*5 + rider] = 0xFF;
    assert(!observe_stock_tour_progress_overview(sram.data(), sram.size(), rider).valid);
    sram[0x069C + 16*5 + rider] = 0;
    assert(!observe_stock_tour_progress_overview(sram.data(), sram.size(), 2).valid);
    assert(!observe_stock_tour_progress_overview(sram.data(), sram.size() - 1, rider).valid);
    assert(!observe_stock_tour_progress_overview(nullptr, sram.size(), rider).valid);
}

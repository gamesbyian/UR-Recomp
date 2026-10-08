#include "uniracers_practice_tour_unlock.hpp"
#include "quick_practice_availability.hpp"

#include <array>
#include <cassert>
#include <cstdint>

int main() {
    std::array<std::uint8_t, 8192> sram{};
    sram[0x0748] = 4;
    constexpr int kRider = 4;
    constexpr std::size_t kUnlock = 0x10D3 + kRider;
    using ur::title::stock_practice_tour_option_mask;
    using ur::product::quick_practice_availability_from_tour_options;
    using ur::product::quick_practice_available_count;
    using ur::product::quick_practice_track_available;

    auto options = stock_practice_tour_option_mask(sram.data(), sram.size(), kRider);
    assert(options.has_value());
    auto tracks = quick_practice_availability_from_tour_options(*options);
    assert(quick_practice_available_count(tracks) == 20);
    for (const int id : {0, 10, 20, 30}) {
        assert(quick_practice_track_available(tracks, static_cast<std::uint8_t>(id)));
    }
    for (const int id : {5, 15, 25, 35, 40}) {
        assert(!quick_practice_track_available(tracks, static_cast<std::uint8_t>(id)));
    }

    sram[kUnlock] = 1;  // four Bronze tour medals: six ordinary tours
    options = stock_practice_tour_option_mask(sram.data(), sram.size(), kRider);
    assert(options.has_value());
    tracks = quick_practice_availability_from_tour_options(*options);
    assert(quick_practice_available_count(tracks) == 30);
    assert(quick_practice_track_available(tracks, 5));
    assert(quick_practice_track_available(tracks, 15));
    assert(!quick_practice_track_available(tracks, 25));

    sram[kUnlock] = 2;  // six Silver tour medals: all eight ordinary tours
    options = stock_practice_tour_option_mask(sram.data(), sram.size(), kRider);
    assert(options.has_value());
    tracks = quick_practice_availability_from_tour_options(*options);
    assert(quick_practice_available_count(tracks) == 40);
    assert(quick_practice_track_available(tracks, 25));
    assert(quick_practice_track_available(tracks, 35));
    assert(!quick_practice_track_available(tracks, 40));

    sram[kUnlock] = 3;  // stock Hunter unlock, withheld by Modern Practice policy
    options = stock_practice_tour_option_mask(sram.data(), sram.size(), kRider);
    assert(options.has_value());
    tracks = quick_practice_availability_from_tour_options(*options);
    assert(quick_practice_available_count(tracks) == 40);
    assert(!quick_practice_track_available(tracks, 44));

    // A never-selected clean stock SRAM contains uninitialized rider data.
    // Only an entirely clean unlock matrix permits the first-four fallback.
    sram[0x0748] = 0x48;
    for (std::size_t index = 0; index < 16; ++index) {
        sram[0x10D3 + index] = 0;
    }
    options = stock_practice_tour_option_mask(sram.data(), sram.size(), 0);
    assert(options.has_value());
    tracks = quick_practice_availability_from_tour_options(*options);
    assert(quick_practice_available_count(tracks) == 20);
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size(), 4));
    sram[0x10D3 + 6] = 1;
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size(), 0));
    sram[0x10D3 + 6] = 0;
    sram[0x0748] = 4;
    sram[kUnlock] = 3;

    // Do not infer a per-rider unlock tier from a different or invalid rider,
    // short stock image, null buffer or malformed unlock value.
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size(), 3));
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size() - 1, kRider));
    assert(!stock_practice_tour_option_mask(nullptr, sram.size(), kRider));
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size(), 16));
    sram[kUnlock] = 255;
    assert(!stock_practice_tour_option_mask(sram.data(), sram.size(), kRider));
}

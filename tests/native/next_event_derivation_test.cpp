#include "next_event_derivation.hpp"
#include "quick_practice_route.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <optional>

using namespace ur::product;

int main() {
    assert(unique_remaining_tour_slot({1, 1, 1, 1, 0}) ==
           std::optional<std::uint8_t>{4});
    assert(unique_remaining_tour_slot({1, 0, 1, 1, 1}) ==
           std::optional<std::uint8_t>{1});
    assert(!unique_remaining_tour_slot({1, 1, 0, 0, 1}));
    assert(!unique_remaining_tour_slot({1, 1, 1, 1, 1}));
    assert(!unique_remaining_tour_slot({0, 0, 0, 0, 0}));
    assert(!unique_remaining_tour_slot({1, 1, 1, 1, 2}));

    assert(unique_next_track_id(0, {1, 1, 1, 1, 0}) ==
           std::optional<std::uint8_t>{4});
    assert(unique_next_track_id(8, {1, 1, 1, 1, 0}) ==
           std::optional<std::uint8_t>{44});
    assert(!unique_next_track_id(9, {1, 1, 1, 1, 0}));
    assert(!unique_next_track_id(2, {1, 1, 0, 0, 1}));

    // The derived global id shares the canonical nine-by-five namespace used
    // by the validated stock-menu router, including Hunter's non-contiguous
    // frontend option 9.
    for (std::uint8_t tour = 0; tour < 9; ++tour) {
        for (std::uint8_t remaining = 0; remaining < 5; ++remaining) {
            std::array<std::uint8_t, 5> qualified{1, 1, 1, 1, 1};
            qualified[remaining] = 0;
            const auto track = unique_next_track_id(tour, qualified);
            assert(track);
            const auto target = quick_practice_target_for_track(*track);
            assert(target.valid);
            assert(target.track_slot == remaining);
            assert(target.tour_option == kQuickPracticeTourOptions[tour]);
        }
    }

    return 0;
}

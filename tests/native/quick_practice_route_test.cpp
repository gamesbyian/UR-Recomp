#include "quick_practice_route.hpp"

#include <cassert>
#include <cstdint>

using namespace ur::product;

int main() {
    for (std::uint8_t track = 0; track < 45; ++track) {
        const auto target = quick_practice_target_for_track(track);
        assert(target.valid);
        assert(target.track_id == track);
        assert(target.track_slot == track % 5);
        assert(quick_practice_track_id_for_target(
            target.tour_option, target.track_slot) == track);
    }

    assert(!quick_practice_target_for_track(45).valid);
    assert(quick_practice_track_id_for_target(8, 0) == -1);
    assert(quick_practice_track_id_for_target(0, 5) == -1);

    auto target = quick_practice_target_for_track(0);
    assert(target.tour_option == 0 && target.track_slot == 0);
    target = quick_practice_target_for_track(4);
    assert(target.tour_option == 0 && target.track_slot == 4);
    target = quick_practice_target_for_track(12);
    assert(target.tour_option == 2 && target.track_slot == 2);
    target = quick_practice_target_for_track(40);
    assert(target.tour_option == 9 && target.track_slot == 0);
    target = quick_practice_target_for_track(44);
    assert(target.tour_option == 9 && target.track_slot == 4);

    assert(quick_practice_tour_input(2, 0) == QuickPracticeMenuInput::Down);
    assert(quick_practice_tour_input(2, 2) == QuickPracticeMenuInput::Accept);
    assert(quick_practice_tour_input(1, 0) == QuickPracticeMenuInput::Right);
    assert(quick_practice_tour_input(0, 1) == QuickPracticeMenuInput::Left);
    assert(quick_practice_tour_input(9, 7) == QuickPracticeMenuInput::Down);
    assert(quick_practice_tour_input(9, 9) == QuickPracticeMenuInput::Accept);
    assert(quick_practice_tour_input(8, 0) == QuickPracticeMenuInput::None);

    assert(quick_practice_track_input(4, 0) == QuickPracticeMenuInput::Down);
    assert(quick_practice_track_input(2, 4) == QuickPracticeMenuInput::Up);
    assert(quick_practice_track_input(3, 3) == QuickPracticeMenuInput::Accept);
    assert(quick_practice_track_input(5, 0) == QuickPracticeMenuInput::None);

    return 0;
}

#include "quick_practice_availability.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto normal = quick_practice_normal_tours_only();
    assert(quick_practice_available_count(normal) == 40);
    assert(quick_practice_track_available(normal, 0));
    assert(quick_practice_track_available(normal, 39));
    assert(!quick_practice_track_available(normal, 40));
    assert(!quick_practice_track_available(normal, 44));

    auto crawler_only = quick_practice_availability_from_tour_options(1u << 0);
    assert(quick_practice_available_count(crawler_only) == 5);
    for (std::uint8_t track = 0; track < 5; ++track) {
        assert(quick_practice_track_available(crawler_only, track));
    }
    assert(!quick_practice_track_available(crawler_only, 5));

    auto crawler_and_shuffler =
        quick_practice_availability_from_tour_options((1u << 0) | (1u << 2));
    assert(quick_practice_available_count(crawler_and_shuffler) == 10);
    assert(quick_practice_track_available(crawler_and_shuffler, 0));
    assert(quick_practice_track_available(crawler_and_shuffler, 10));
    assert(!quick_practice_track_available(crawler_and_shuffler, 5));

    // Stock option 8 is not a shipping tour. Setting it must expose nothing.
    auto reserved_only = quick_practice_availability_from_tour_options(1u << 8);
    assert(quick_practice_available_count(reserved_only) == 0);

    auto hunter_only = quick_practice_availability_from_tour_options(1u << 9);
    assert(quick_practice_available_count(hunter_only) == 5);
    assert(quick_practice_track_available(hunter_only, 40));
    assert(quick_practice_track_available(hunter_only, 44));
    assert(!quick_practice_track_available(hunter_only, 39));

    auto all = quick_practice_all_tracks();
    assert(quick_practice_available_count(all) == 45);
    assert(quick_practice_track_available(all, 44));

    auto none = quick_practice_no_tracks();
    assert(quick_practice_available_count(none) == 0);
    assert(!quick_practice_picker_launchable({0}, none));

    // A caller can expose Hunter deliberately after its own progression/policy
    // decision without changing the canonical course catalog.
    normal = quick_practice_set_track_available(normal, 42, true);
    assert(quick_practice_track_available(normal, 42));
    assert(quick_practice_available_count(normal) == 41);
    normal = quick_practice_set_track_available(normal, 42, false);
    assert(!quick_practice_track_available(normal, 42));

    // Sparse availability skips unavailable courses and wraps cleanly.
    auto sparse = quick_practice_no_tracks();
    sparse = quick_practice_set_track_available(sparse, 2, true);
    sparse = quick_practice_set_track_available(sparse, 12, true);
    sparse = quick_practice_set_track_available(sparse, 30, true);

    QuickPracticePickerState state{2};
    state = quick_practice_available_course_step(state, sparse, +1);
    assert(state.track_id == 12);
    state = quick_practice_available_course_step(state, sparse, +1);
    assert(state.track_id == 30);
    state = quick_practice_available_course_step(state, sparse, +1);
    assert(state.track_id == 2);
    state = quick_practice_available_course_step(state, sparse, -1);
    assert(state.track_id == 30);

    state.track_id = 44;
    state = quick_practice_normalize_available_picker(state, sparse);
    assert(state.track_id == 2);
    assert(quick_practice_picker_launchable(state, sparse));

    return 0;
}

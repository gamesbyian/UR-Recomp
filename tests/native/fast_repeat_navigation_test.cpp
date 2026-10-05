#include "fast_repeat_navigation.hpp"
#include "quick_practice_route.hpp"

#include <cassert>

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

    // The progression-derived global track id must use the same canonical
    // nine-by-five namespace as the validated stock-menu course router.
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

    FastNavigationContext ctx{};
    ctx.modern_mode = true;

    assert(resolve_fast_navigation(
        FastNavigationCommand::RepeatAttempt, ctx) ==
        FastNavigationAction::None);

    ctx.restart_surface = true;
    ctx.restart_available = true;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RepeatAttempt, ctx) ==
        FastNavigationAction::RestartAttempt);

    ctx.modern_mode = false;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RepeatAttempt, ctx) ==
        FastNavigationAction::None);

    ctx = {};
    ctx.modern_mode = true;
    // Next Event is deliberately represented but unavailable until one
    // authoritative stock event can be derived without guessing.
    assert(resolve_fast_navigation(
        FastNavigationCommand::NextEvent, ctx) ==
        FastNavigationAction::None);

    ctx.settled_main_menu = true;
    ctx.recent_course_valid = true;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::None);

    ctx.recent_course_profile_matches = true;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::LaunchRecentPractice);

    ctx.practice_active = true;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::None);

    ctx.practice_active = false;
    ctx.recent_course_valid = false;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::None);

    ctx.recent_course_valid = true;
    ctx.recent_course_profile_matches = false;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::None);

    ctx.recent_course_profile_matches = true;
    ctx.settled_main_menu = false;
    assert(resolve_fast_navigation(
        FastNavigationCommand::RecentCourse, ctx) ==
        FastNavigationAction::None);

    return 0;
}

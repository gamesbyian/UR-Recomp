#include "fast_repeat_navigation.hpp"

#include <cassert>

using namespace ur::product;

int main() {
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

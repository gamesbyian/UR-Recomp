#pragma once

#include <cstdint>

namespace ur::product {

enum class FastNavigationCommand {
    RepeatAttempt,
    RecentCourse,
    NextEvent,
};

enum class FastNavigationAction {
    None,
    RestartAttempt,
    LaunchRecentPractice,
};

struct FastNavigationContext {
    bool modern_mode = false;
    bool restart_surface = false;
    bool restart_available = false;
    bool settled_main_menu = false;
    bool practice_active = false;
    bool recent_course_valid = false;
    bool recent_course_profile_matches = false;
};

constexpr FastNavigationAction resolve_fast_navigation(
    FastNavigationCommand command,
    FastNavigationContext context
) noexcept {
    if (!context.modern_mode) return FastNavigationAction::None;

    switch (command) {
    case FastNavigationCommand::RepeatAttempt:
        return context.restart_surface && context.restart_available
            ? FastNavigationAction::RestartAttempt
            : FastNavigationAction::None;
    case FastNavigationCommand::RecentCourse:
        return context.settled_main_menu && !context.practice_active &&
                context.recent_course_valid &&
                context.recent_course_profile_matches
            ? FastNavigationAction::LaunchRecentPractice
            : FastNavigationAction::None;
    case FastNavigationCommand::NextEvent:
        // Next Event is owned by the Modern Tour surface, which routes it
        // through the tour-continuation authority (ModernTourEntryIntent::
        // NextEvent). This shortcut policy has no separate route for it.
        return FastNavigationAction::None;
    }
    return FastNavigationAction::None;
}

}  // namespace ur::product

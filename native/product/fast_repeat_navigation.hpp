#pragma once

#include <array>
#include <cstdint>
#include <optional>

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

constexpr std::optional<std::uint8_t> unique_remaining_tour_slot(
    const std::array<std::uint8_t, 5>& qualified
) noexcept {
    std::optional<std::uint8_t> remaining;
    unsigned qualified_count = 0;
    for (std::uint8_t slot = 0; slot < qualified.size(); ++slot) {
        if (qualified[slot] > 1) return std::nullopt;
        if (qualified[slot] == 1) {
            ++qualified_count;
            continue;
        }
        if (remaining) return std::nullopt;
        remaining = slot;
    }
    return qualified_count == 4 ? remaining : std::nullopt;
}

constexpr std::optional<std::uint8_t> unique_next_track_id(
    std::uint8_t tour_row,
    const std::array<std::uint8_t, 5>& qualified
) noexcept {
    if (tour_row >= 9) return std::nullopt;
    const auto slot = unique_remaining_tour_slot(qualified);
    if (!slot) return std::nullopt;
    return static_cast<std::uint8_t>(tour_row * 5u + *slot);
}

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
        // Routing a uniquely derived event remains a separate progression
        // concern. This policy command stays inert until the caller supplies
        // an accepted stock-menu route; unique_next_track_id() is the sole
        // derivation primitive and fails closed outside the four-of-five case.
        return FastNavigationAction::None;
    }
    return FastNavigationAction::None;
}

}  // namespace ur::product

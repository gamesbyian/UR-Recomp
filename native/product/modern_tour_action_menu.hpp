#pragma once

#include "modern_host_navigation.h"
#include "modern_tour_entry_policy.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

enum class ModernTourActionRow : std::uint8_t {
    ResumeTour = 0,
    RestartTour = 1,
    Back = 2,
    NextEvent = 3,
};

struct ModernTourActionMenu {
    std::array<ModernTourActionRow, 4> rows{};
    std::size_t row_count = 0;
    std::size_t selected = 0;
    bool confirming_restart = false;
};

constexpr ModernTourActionMenu make_modern_tour_action_menu(
    ModernTourEntryContext context) noexcept {
    ModernTourActionMenu menu;
    const auto actions = modern_tour_entry_actions(context);
    // Tour play emphasizes Next Event when it is unambiguous, so it leads and
    // is preselected. Without it the historical row order is unchanged.
    if (actions.next_event_available) {
        menu.rows[menu.row_count++] = ModernTourActionRow::NextEvent;
    }
    if (actions.resume_available) {
        menu.rows[menu.row_count++] = ModernTourActionRow::ResumeTour;
    }
    if (actions.restart_available) {
        menu.rows[menu.row_count++] = ModernTourActionRow::RestartTour;
    }
    menu.rows[menu.row_count++] = ModernTourActionRow::Back;
    return menu;
}

constexpr ModernTourActionRow selected_modern_tour_action(
    const ModernTourActionMenu& menu) noexcept {
    return menu.rows[
        menu.selected < menu.row_count ? menu.selected : 0u];
}

inline ModernTourActionMenu navigate_modern_tour_action_menu(
    ModernTourActionMenu menu,
    UrModernHostNavigationAction action) noexcept {
    if (menu.row_count == 0) return menu;

    if (menu.confirming_restart) {
        if (ur_modern_host_navigation_is_back(action)) {
            menu.confirming_restart = false;
        }
        return menu;
    }

    const int delta = ur_modern_host_navigation_vertical_delta(action);
    if (delta < 0) {
        menu.selected =
            menu.selected == 0 ? menu.row_count - 1 : menu.selected - 1;
    } else if (delta > 0) {
        menu.selected = (menu.selected + 1) % menu.row_count;
    }
    return menu;
}

struct ModernTourActionMenuResult {
    ModernTourActionMenu menu{};
    ModernTourEntryIntent intent = ModernTourEntryIntent::None;
    bool close_menu = false;
};

inline ModernTourActionMenuResult activate_modern_tour_action_menu(
    ModernTourActionMenu menu,
    ModernTourEntryContext context,
    UrModernHostNavigationAction action) noexcept {
    ModernTourActionMenuResult out{menu, ModernTourEntryIntent::None, false};

    if (menu.confirming_restart) {
        if (ur_modern_host_navigation_is_back(action)) {
            out.menu.confirming_restart = false;
            return out;
        }
        if (ur_modern_host_navigation_is_confirm(action)) {
            const auto decision = resolve_modern_tour_entry(
                context, ModernTourEntryIntent::Restart, true);
            if (decision.intent == ModernTourEntryIntent::Restart) {
                out.intent = decision.intent;
                out.close_menu = true;
            } else {
                // Context can become stale while confirmation is open.
                // Return to the action menu instead of trapping the player
                // in a confirmation that can no longer succeed.
                out.menu.confirming_restart = false;
            }
        }
        return out;
    }

    if (ur_modern_host_navigation_is_back(action)) {
        out.close_menu = true;
        return out;
    }
    if (!ur_modern_host_navigation_is_confirm(action) ||
        menu.row_count == 0) {
        return out;
    }

    switch (selected_modern_tour_action(menu)) {
    case ModernTourActionRow::NextEvent: {
        const auto decision = resolve_modern_tour_entry(
            context, ModernTourEntryIntent::NextEvent);
        if (decision.intent == ModernTourEntryIntent::NextEvent) {
            out.intent = decision.intent;
            out.close_menu = true;
        }
        break;
    }
    case ModernTourActionRow::ResumeTour: {
        const auto decision = resolve_modern_tour_entry(
            context, ModernTourEntryIntent::Resume);
        if (decision.intent == ModernTourEntryIntent::Resume) {
            out.intent = decision.intent;
            out.close_menu = true;
        }
        break;
    }
    case ModernTourActionRow::RestartTour:
        out.menu.confirming_restart = true;
        break;
    case ModernTourActionRow::Back:
        out.close_menu = true;
        break;
    }
    return out;
}

}  // namespace ur::product

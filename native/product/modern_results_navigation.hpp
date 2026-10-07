#pragma once

#include "host_product_state.hpp"
#include "modern_host_navigation.h"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

enum class ModernResultsAction : std::uint8_t {
    None = 0,
    NextEvent,
    Retry,
    TrackSelect,
    TourSelect,
    Records,
    RepeatPractice,
};

struct ModernResultsNavigationContext {
    ExecutionMode mode = ExecutionMode::Authentic;
    bool results_surface = false;
    bool practice_active = false;
    bool ordinary_tour_result = false;
    bool authoritative_profile = false;
    bool result_profile_matches = false;
    bool router_available = false;
    bool restart_available = false;
    bool next_event_unique = false;
};

struct ModernResultsNavigationMenu {
    std::array<ModernResultsAction, 5> rows{};
    std::size_t row_count = 0;
    std::size_t selected = 0;
};

constexpr ModernResultsNavigationMenu make_modern_results_navigation_menu(
    ModernResultsNavigationContext context) noexcept {
    ModernResultsNavigationMenu menu;
    if (context.mode != ExecutionMode::Modern || !context.results_surface) {
        return menu;
    }

    if (context.practice_active) {
        if (context.restart_available) {
            menu.rows[menu.row_count++] = ModernResultsAction::RepeatPractice;
        }
        menu.rows[menu.row_count++] = ModernResultsAction::Records;
        return menu;
    }

    const bool progression =
        context.ordinary_tour_result &&
        context.authoritative_profile &&
        context.result_profile_matches &&
        context.router_available;
    if (progression && context.next_event_unique) {
        menu.rows[menu.row_count++] = ModernResultsAction::NextEvent;
    }
    if (context.restart_available) {
        menu.rows[menu.row_count++] = ModernResultsAction::Retry;
    }
    if (progression) {
        menu.rows[menu.row_count++] = ModernResultsAction::TrackSelect;
        menu.rows[menu.row_count++] = ModernResultsAction::TourSelect;
    }
    menu.rows[menu.row_count++] = ModernResultsAction::Records;
    return menu;
}

constexpr ModernResultsAction selected_modern_results_action(
    const ModernResultsNavigationMenu& menu) noexcept {
    return menu.row_count == 0
        ? ModernResultsAction::None
        : menu.rows[menu.selected < menu.row_count ? menu.selected : 0u];
}

inline ModernResultsNavigationMenu navigate_modern_results_navigation_menu(
    ModernResultsNavigationMenu menu,
    UrModernHostNavigationAction action) noexcept {
    if (menu.row_count == 0) return menu;
    const int delta = ur_modern_host_navigation_vertical_delta(action);
    if (delta < 0) {
        menu.selected =
            menu.selected == 0 ? menu.row_count - 1 : menu.selected - 1;
    } else if (delta > 0) {
        menu.selected = (menu.selected + 1) % menu.row_count;
    }
    return menu;
}

constexpr bool modern_results_action_available(
    ModernResultsAction action,
    ModernResultsNavigationContext context) noexcept {
    const auto menu = make_modern_results_navigation_menu(context);
    for (std::size_t i = 0; i < menu.row_count; ++i) {
        if (menu.rows[i] == action) return true;
    }
    return false;
}

inline ModernResultsAction activate_modern_results_navigation_menu(
    const ModernResultsNavigationMenu& menu,
    ModernResultsNavigationContext context,
    UrModernHostNavigationAction action) noexcept {
    if (!ur_modern_host_navigation_is_confirm(action)) {
        return ModernResultsAction::None;
    }
    const auto selected = selected_modern_results_action(menu);
    return modern_results_action_available(selected, context)
        ? selected
        : ModernResultsAction::None;
}

}  // namespace ur::product

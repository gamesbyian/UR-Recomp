#include "modern_results_navigation.hpp"

#include <cassert>

using namespace ur::product;

static ModernResultsNavigationContext ordinary() {
    return {
        ExecutionMode::Modern,
        true,
        false,
        true,
        true,
        true,
        true,
        true,
        true,
    };
}

int main() {
    {
        auto menu = make_modern_results_navigation_menu(ordinary());
        assert(menu.row_count == 5);
        assert(menu.rows[0] == ModernResultsAction::NextEvent);
        assert(menu.rows[1] == ModernResultsAction::Retry);
        assert(menu.rows[2] == ModernResultsAction::TrackSelect);
        assert(menu.rows[3] == ModernResultsAction::TourSelect);
        assert(menu.rows[4] == ModernResultsAction::Records);

        menu = navigate_modern_results_navigation_menu(
            menu, UR_MODERN_HOST_NAV_DOWN);
        assert(selected_modern_results_action(menu) ==
               ModernResultsAction::Retry);
        assert(activate_modern_results_navigation_menu(
                   menu, ordinary(), UR_MODERN_HOST_NAV_CONFIRM) ==
               ModernResultsAction::Retry);
    }

    {
        auto ambiguous = ordinary();
        ambiguous.next_event_unique = false;
        const auto menu =
            make_modern_results_navigation_menu(ambiguous);
        assert(menu.row_count == 4);
        assert(menu.rows[0] == ModernResultsAction::Retry);
        assert(menu.rows[1] == ModernResultsAction::TrackSelect);
        assert(menu.rows[2] == ModernResultsAction::TourSelect);
        assert(menu.rows[3] == ModernResultsAction::Records);
    }

    {
        auto stale = ordinary();
        stale.result_profile_matches = false;
        const auto menu = make_modern_results_navigation_menu(stale);
        assert(menu.row_count == 2);
        assert(menu.rows[0] == ModernResultsAction::Retry);
        assert(menu.rows[1] == ModernResultsAction::Records);
        ModernResultsNavigationMenu forged{};
        forged.rows[0] = ModernResultsAction::TrackSelect;
        forged.row_count = 1;
        assert(activate_modern_results_navigation_menu(
                   forged, stale, UR_MODERN_HOST_NAV_CONFIRM) ==
               ModernResultsAction::None);
    }

    {
        auto owned = ordinary();
        owned.router_available = false;
        const auto menu = make_modern_results_navigation_menu(owned);
        assert(menu.row_count == 2);
        assert(!modern_results_action_available(
            ModernResultsAction::NextEvent, owned));
        assert(!modern_results_action_available(
            ModernResultsAction::TrackSelect, owned));
        assert(!modern_results_action_available(
            ModernResultsAction::TourSelect, owned));
    }

    {
        auto practice = ordinary();
        practice.practice_active = true;
        const auto menu = make_modern_results_navigation_menu(practice);
        assert(menu.row_count == 2);
        assert(menu.rows[0] == ModernResultsAction::RepeatPractice);
        assert(menu.rows[1] == ModernResultsAction::Records);
    }

    {
        auto authentic = ordinary();
        authentic.mode = ExecutionMode::Authentic;
        assert(make_modern_results_navigation_menu(authentic).row_count == 0);
    }

    return 0;
}

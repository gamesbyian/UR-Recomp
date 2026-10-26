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
        true,  // canonical Practice target still available
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

        // The old selected index can remain in range while rows shift.
        // RETRY remains available but row 1 now displays TRACK SELECT:
        // confirming an old row must not execute a different visible action.
        auto stale = make_modern_results_navigation_menu(ordinary());
        stale.selected = 1;
        assert(modern_results_action_available(
            ModernResultsAction::Retry, ambiguous));
        assert(activate_modern_results_navigation_menu(
            stale, ambiguous, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::None);
        stale.selected = 2;  // TRACK SELECT moved from row 2 to row 1.
        assert(activate_modern_results_navigation_menu(
            stale, ambiguous, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::None);
        stale.selected = 4;  // RECORDS moved from row 4 to row 3.
        assert(activate_modern_results_navigation_menu(
            stale, ambiguous, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::None);
        auto fresh = menu;
        fresh.selected = 1;
        assert(activate_modern_results_navigation_menu(
            fresh, ambiguous, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::TrackSelect);
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
        auto unsupported = ordinary();
        unsupported.ordinary_tour_result = false;
        const auto menu = make_modern_results_navigation_menu(unsupported);
        assert(menu.row_count == 2);
        assert(menu.rows[0] == ModernResultsAction::Retry);
        assert(menu.rows[1] == ModernResultsAction::Records);
        assert(!modern_results_action_available(
            ModernResultsAction::NextEvent, unsupported));
        assert(!modern_results_action_available(
            ModernResultsAction::TrackSelect, unsupported));
        assert(!modern_results_action_available(
            ModernResultsAction::TourSelect, unsupported));
    }

    {
        auto practice = ordinary();
        practice.practice_active = true;
        const auto menu = make_modern_results_navigation_menu(practice);
        assert(menu.row_count == 2);
        assert(menu.rows[0] == ModernResultsAction::RepeatPractice);
        assert(menu.rows[1] == ModernResultsAction::Records);

        // A busy results router must not advertise a Practice repeat or
        // confirm a row that was displayed before routing became busy.
        practice.router_available = false;
        const auto busy = make_modern_results_navigation_menu(practice);
        assert(busy.row_count == 1);
        assert(busy.rows[0] == ModernResultsAction::Records);
        assert(!modern_results_action_available(
            ModernResultsAction::RepeatPractice, practice));
        assert(activate_modern_results_navigation_menu(
            menu, practice, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::None);
        practice.router_available = true;

        // If the retained target is lost or corrupted after results, do not
        // advertise a Restart that cannot safely repeat the same course.
        practice.practice_target_ready = false;
        const auto invalid = make_modern_results_navigation_menu(practice);
        assert(invalid.row_count == 1);
        assert(invalid.rows[0] == ModernResultsAction::Records);
        assert(!modern_results_action_available(
            ModernResultsAction::RepeatPractice, practice));
        ModernResultsNavigationMenu stale_repeat{};
        stale_repeat.rows[0] = ModernResultsAction::RepeatPractice;
        stale_repeat.row_count = 1;
        assert(activate_modern_results_navigation_menu(
            stale_repeat, practice, UR_MODERN_HOST_NAV_CONFIRM) ==
            ModernResultsAction::None);
    }

    {
        auto authentic = ordinary();
        authentic.mode = ExecutionMode::Authentic;
        assert(make_modern_results_navigation_menu(authentic).row_count == 0);
    }

    {
        // A stale selected index must never confirm row zero implicitly.
        // Row zero may be NEXT EVENT and would change guest progression.
        auto stale = make_modern_results_navigation_menu(ordinary());
        stale.selected = stale.row_count;
        assert(selected_modern_results_action(stale) == ModernResultsAction::None);
        assert(activate_modern_results_navigation_menu(
                   stale, ordinary(), UR_MODERN_HOST_NAV_CONFIRM) ==
               ModernResultsAction::None);
        assert(navigate_modern_results_navigation_menu(
                   stale, UR_MODERN_HOST_NAV_CONFIRM).selected == stale.selected);
        stale = navigate_modern_results_navigation_menu(
            stale, UR_MODERN_HOST_NAV_DOWN);
        assert(stale.selected == 0);
        assert(selected_modern_results_action(stale) ==
               ModernResultsAction::NextEvent);

        // An impossible row count is rejected before indexing the fixed array.
        stale.row_count = stale.rows.size() + 1;
        assert(selected_modern_results_action(stale) == ModernResultsAction::None);
        assert(activate_modern_results_navigation_menu(
                   stale, ordinary(), UR_MODERN_HOST_NAV_CONFIRM) ==
               ModernResultsAction::None);
        assert(navigate_modern_results_navigation_menu(
                   stale, UR_MODERN_HOST_NAV_UP).row_count == stale.row_count);
    }


    // Exhaustive 1024-context matrix: no displayed row may be unactionable.
    for (unsigned mode = 0; mode < 2u; ++mode) {
        for (unsigned mask = 0; mask < 512u; ++mask) {
            auto ctx = ordinary();
            ctx.mode = mode ? ExecutionMode::Modern : ExecutionMode::Authentic;
            ctx.results_surface = (mask & 1u) != 0;
            ctx.practice_active = (mask & 2u) != 0;
            ctx.ordinary_tour_result = (mask & 4u) != 0;
            ctx.authoritative_profile = (mask & 8u) != 0;
            ctx.result_profile_matches = (mask & 16u) != 0;
            ctx.router_available = (mask & 32u) != 0;
            ctx.restart_available = (mask & 64u) != 0;
            ctx.next_event_unique = (mask & 128u) != 0;
            ctx.practice_target_ready = (mask & 256u) != 0;
            auto menu = make_modern_results_navigation_menu(ctx);
            assert(menu.row_count <= menu.rows.size());
            for (std::size_t row = 0; row < menu.row_count; ++row) {
                auto chosen = menu;
                chosen.selected = row;
                assert(selected_modern_results_action(chosen) == menu.rows[row]);
                assert(modern_results_action_available(menu.rows[row], ctx));
                assert(activate_modern_results_navigation_menu(
                    chosen, ctx, UR_MODERN_HOST_NAV_CONFIRM) == menu.rows[row]);
                assert(activate_modern_results_navigation_menu(
                    chosen, ctx, UR_MODERN_HOST_NAV_BACK) == ModernResultsAction::None);
            }
            for (std::size_t invalid : {menu.row_count,
                                        static_cast<std::size_t>(-1)}) {
                auto stale = menu;
                stale.selected = invalid;
                assert(selected_modern_results_action(stale) == ModernResultsAction::None);
                assert(activate_modern_results_navigation_menu(
                    stale, ctx, UR_MODERN_HOST_NAV_CONFIRM) ==
                    ModernResultsAction::None);
            }
            auto corrupt = menu;
            corrupt.row_count = corrupt.rows.size() + 1;
            assert(selected_modern_results_action(corrupt) == ModernResultsAction::None);
            assert(activate_modern_results_navigation_menu(
                corrupt, ctx, UR_MODERN_HOST_NAV_CONFIRM) ==
                ModernResultsAction::None);
        }
    }

    return 0;
}

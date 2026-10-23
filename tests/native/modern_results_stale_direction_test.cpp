#include "modern_results_navigation.hpp"

#include <cassert>
#include <cstddef>
#include <cstdio>

using namespace ur::product;

int main() {
    unsigned checked = 0;
    // Every Modern results context has at least a Records row. A stale
    // index may follow an asynchronous row refresh, but Up must restore
    // focus at the bottom (Records), never jump to Next Event at the top.
    for (unsigned mask = 0; mask != 256; ++mask) {
        ModernResultsNavigationContext ctx{};
        ctx.mode = ExecutionMode::Modern;
        ctx.results_surface = (mask & 1u) != 0;
        ctx.practice_active = (mask & 2u) != 0;
        ctx.ordinary_tour_result = (mask & 4u) != 0;
        ctx.authoritative_profile = (mask & 8u) != 0;
        ctx.result_profile_matches = (mask & 16u) != 0;
        ctx.router_available = (mask & 32u) != 0;
        ctx.restart_available = (mask & 64u) != 0;
        ctx.next_event_unique = (mask & 128u) != 0;
        auto menu = make_modern_results_navigation_menu(ctx);
        if (!menu.row_count) continue;
        for (std::size_t invalid : {menu.row_count, menu.rows.size() + 1u,
                                    static_cast<std::size_t>(-1)}) {
            auto stale = menu;
            stale.selected = invalid;
            assert(activate_modern_results_navigation_menu(
                stale, ctx, UR_MODERN_HOST_NAV_CONFIRM) ==
                ModernResultsAction::None);
            assert(navigate_modern_results_navigation_menu(
                stale, UR_MODERN_HOST_NAV_CONFIRM).selected == invalid);
            assert(navigate_modern_results_navigation_menu(
                stale, UR_MODERN_HOST_NAV_BACK).selected == invalid);
            const auto up = navigate_modern_results_navigation_menu(
                stale, UR_MODERN_HOST_NAV_UP);
            assert(up.selected == menu.row_count - 1);
            assert(selected_modern_results_action(up) ==
                ModernResultsAction::Records);
            const auto down = navigate_modern_results_navigation_menu(
                stale, UR_MODERN_HOST_NAV_DOWN);
            assert(down.selected == 0);
            assert(selected_modern_results_action(down) == menu.rows[0]);
            ++checked;
        }
        auto corrupt = menu;
        corrupt.row_count = corrupt.rows.size() + 1;
        corrupt.selected = corrupt.row_count;
        assert(navigate_modern_results_navigation_menu(
            corrupt, UR_MODERN_HOST_NAV_UP).selected == corrupt.selected);
    }
    assert(checked == 384);
    std::puts("PASS: stale results Up restores Records, Down restores first row across 128 contexts");
}

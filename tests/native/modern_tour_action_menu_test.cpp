#include "modern_tour_action_menu.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const ModernTourEntryContext valid{
        ExecutionMode::Modern,
        true,
        true,
        true,
    };

    auto menu = make_modern_tour_action_menu(valid);
    assert(menu.row_count == 3);
    assert(selected_modern_tour_action(menu) ==
           ModernTourActionRow::ResumeTour);

    menu = navigate_modern_tour_action_menu(
        menu, UR_MODERN_HOST_NAV_DOWN);
    assert(selected_modern_tour_action(menu) ==
           ModernTourActionRow::RestartTour);

    auto activated = activate_modern_tour_action_menu(
        menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    assert(activated.intent == ModernTourEntryIntent::None);
    assert(!activated.close_menu);
    assert(activated.menu.confirming_restart);

    // Back cancels confirmation without losing the underlying menu.
    activated = activate_modern_tour_action_menu(
        activated.menu, valid, UR_MODERN_HOST_NAV_BACK);
    assert(!activated.menu.confirming_restart);
    assert(!activated.close_menu);

    // Restart needs the second explicit confirm.
    activated = activate_modern_tour_action_menu(
        menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    activated = activate_modern_tour_action_menu(
        activated.menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    assert(activated.intent == ModernTourEntryIntent::Restart);
    assert(activated.close_menu);

    menu = make_modern_tour_action_menu(valid);
    activated = activate_modern_tour_action_menu(
        menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    assert(activated.intent == ModernTourEntryIntent::Resume);
    assert(activated.close_menu);

    // Navigation wraps and Back is always available.
    menu = make_modern_tour_action_menu(valid);
    menu = navigate_modern_tour_action_menu(
        menu, UR_MODERN_HOST_NAV_UP);
    assert(selected_modern_tour_action(menu) == ModernTourActionRow::Back);
    activated = activate_modern_tour_action_menu(
        menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    assert(activated.close_menu);
    assert(activated.intent == ModernTourEntryIntent::None);

    // Without a valid continuation there is no fake Resume/Restart surface.
    ModernTourEntryContext absent = valid;
    absent.unfinished_tour = false;
    menu = make_modern_tour_action_menu(absent);
    assert(menu.row_count == 1);
    assert(selected_modern_tour_action(menu) == ModernTourActionRow::Back);

    ModernTourEntryContext authentic = valid;
    authentic.mode = ExecutionMode::Authentic;
    menu = make_modern_tour_action_menu(authentic);
    assert(menu.row_count == 1);
    assert(selected_modern_tour_action(menu) == ModernTourActionRow::Back);

    // Context becoming stale during confirmation fails closed.
    menu = make_modern_tour_action_menu(valid);
    menu = navigate_modern_tour_action_menu(
        menu, UR_MODERN_HOST_NAV_DOWN);
    activated = activate_modern_tour_action_menu(
        menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
    ModernTourEntryContext stale = valid;
    stale.continuation_source_matches = false;
    activated = activate_modern_tour_action_menu(
        activated.menu, stale, UR_MODERN_HOST_NAV_CONFIRM);
    assert(activated.intent == ModernTourEntryIntent::None);
    assert(!activated.close_menu);
    assert(!activated.menu.confirming_restart);
    assert(selected_modern_tour_action(activated.menu) ==
           ModernTourActionRow::RestartTour);

    return 0;
}

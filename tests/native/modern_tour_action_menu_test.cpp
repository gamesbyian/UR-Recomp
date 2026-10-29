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

    {
        ModernTourEntryContext next = valid;
        next.next_event_unique = true;
        auto next_menu = make_modern_tour_action_menu(next);
        assert(next_menu.row_count == 4);
        assert(selected_modern_tour_action(next_menu) ==
               ModernTourActionRow::NextEvent);
        assert(next_menu.rows[1] == ModernTourActionRow::ResumeTour);
        assert(next_menu.rows[2] == ModernTourActionRow::RestartTour);
        assert(next_menu.rows[3] == ModernTourActionRow::Back);

        auto chosen = activate_modern_tour_action_menu(
            next_menu, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(chosen.intent == ModernTourEntryIntent::NextEvent);
        assert(chosen.close_menu);

        // Context can lose uniqueness while the menu is open (stale row):
        // activation then fails closed instead of guessing an event.
        chosen = activate_modern_tour_action_menu(
            next_menu, valid, UR_MODERN_HOST_NAV_CONFIRM);
        assert(chosen.intent == ModernTourEntryIntent::None);
        assert(!chosen.close_menu);

        // Authentic never exposes it.
        ModernTourEntryContext authentic_next = next;
        authentic_next.mode = ExecutionMode::Authentic;
        const auto authentic_menu =
            make_modern_tour_action_menu(authentic_next);
        assert(authentic_menu.row_count == 1);
        assert(selected_modern_tour_action(authentic_menu) ==
               ModernTourActionRow::Back);
    }


    // A source qualification update can add or remove Next Event while
    // focus is held. Confirm must never silently activate a different row.
    {
        ModernTourEntryContext next = valid;
        next.next_event_unique = true;
        auto four = make_modern_tour_action_menu(next);
        auto three = make_modern_tour_action_menu(valid);

        // Selected Resume at row 1 becomes Restart when Next Event vanishes.
        four.selected = 1;
        auto ignored = activate_modern_tour_action_menu(
            four, valid, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);
        assert(!ignored.menu.confirming_restart);

        // Selected Resume at row 0 becomes Next Event when it appears.
        three.selected = 0;
        ignored = activate_modern_tour_action_menu(
            three, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);
        assert(!ignored.menu.confirming_restart);

        // A formerly selected Back must not start a Restart confirmation.
        three.selected = 2;
        ignored = activate_modern_tour_action_menu(
            three, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);
        assert(!ignored.menu.confirming_restart);

        // A removed continuation leaves only Back, not an implicit Resume.
        three.selected = 0;
        ignored = activate_modern_tour_action_menu(
            three, absent, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);

        // A malformed menu cannot trick either selector or Confirm into
        // routing Next Event, even when the current context qualifies it.
        auto invalid = make_modern_tour_action_menu(next);
        invalid.selected = 99;
        assert(selected_modern_tour_action(invalid) ==
               ModernTourActionRow::None);
        ignored = activate_modern_tour_action_menu(
            invalid, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);
        invalid = navigate_modern_tour_action_menu(
            invalid, UR_MODERN_HOST_NAV_UP);
        assert(selected_modern_tour_action(invalid) ==
               ModernTourActionRow::Back);
        invalid.selected = 99;
        invalid = navigate_modern_tour_action_menu(
            invalid, UR_MODERN_HOST_NAV_DOWN);
        assert(selected_modern_tour_action(invalid) ==
               ModernTourActionRow::NextEvent);

        invalid.row_count = invalid.rows.size() + 1;
        assert(selected_modern_tour_action(invalid) ==
               ModernTourActionRow::None);
        ignored = activate_modern_tour_action_menu(
            invalid, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);
        invalid.row_count = 0;
        assert(selected_modern_tour_action(invalid) ==
               ModernTourActionRow::None);
        ignored = activate_modern_tour_action_menu(
            invalid, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(ignored.intent == ModernTourEntryIntent::None);
        assert(!ignored.close_menu);

        // Legitimate current Next Event still routes, and explicit Back
        // remains available even when source authority is withdrawn.
        auto fresh = make_modern_tour_action_menu(next);
        auto chosen = activate_modern_tour_action_menu(
            fresh, next, UR_MODERN_HOST_NAV_CONFIRM);
        assert(chosen.intent == ModernTourEntryIntent::NextEvent);
        assert(chosen.close_menu);
        auto backing = make_modern_tour_action_menu(absent);
        chosen = activate_modern_tour_action_menu(
            backing, absent, UR_MODERN_HOST_NAV_CONFIRM);
        assert(chosen.intent == ModernTourEntryIntent::None);
        assert(chosen.close_menu);
    }

    return 0;
}

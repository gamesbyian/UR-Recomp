#include "modern_tour_continue.hpp"

#include <cassert>

using namespace ur::product;

static ModernTourContinueStep advance_until_action(
    ModernTourContinueState state,
    ModernTourContinueObservation observation) {
    ModernTourContinueStep step;
    for (std::uint16_t i = 0;
         i <= kQuickPracticeMenuSettleObservations;
         ++i) {
        step = advance_modern_tour_continue(state, observation);
        state = step.state;
        if (step.input != QuickPracticeMenuInput::None ||
            step.track_select_ready || step.tour_select_ready || step.timed_out ||
            step.state.stage == ModernTourContinueStage::Idle) {
            return step;
        }
    }
    return step;
}

static void prove_restart_uses_same_stock_route_without_restore() {
    const ModernTourEntryContext context{
        ExecutionMode::Modern,
        true,
        true,
        true,
    };
    const auto restart = resolve_modern_tour_entry(
        context, ModernTourEntryIntent::Restart, true);
    assert(restart.intent == ModernTourEntryIntent::Restart);
    assert(restart.route_stock_frontend);
    assert(!restart.restore_continuation_at_track_select);
    assert(restart.retire_continuation_after_stock_wipe);

    for (std::uint8_t tour = 0; tour < 9; ++tour) {
        auto state = begin_modern_tour_entry(tour, restart);
        assert(state.intent == ModernTourEntryIntent::Restart);
        assert(!state.restore_continuation_at_track_select);
        assert(state.retire_continuation_after_stock_wipe);

        ModernTourContinueObservation observation{0xD7, 0, false};
        bool reached = false;
        for (int guard = 0; guard < 320 && !reached; ++guard) {
            const auto step =
                advance_until_action(state, observation);
            state = step.state;

            switch (step.input) {
            case QuickPracticeMenuInput::Up:
                if (observation.selected_option >= 2) {
                    observation.selected_option =
                        static_cast<std::uint8_t>(
                            observation.selected_option - 2);
                }
                break;
            case QuickPracticeMenuInput::Down:
                observation.selected_option =
                    static_cast<std::uint8_t>(
                        observation.selected_option + 2);
                break;
            case QuickPracticeMenuInput::Left:
                if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeMenuInput::Right:
                ++observation.selected_option;
                break;
            case QuickPracticeMenuInput::Accept:
                switch (state.stage) {
                case ModernTourContinueStage::AwaitRider:
                    observation = {0x3C, 0, false};
                    break;
                case ModernTourContinueStage::AwaitTour:
                    observation = {0x6D, 0, false};
                    break;
                case ModernTourContinueStage::AwaitTrack:
                    observation = {0xF6, 0, false};
                    break;
                default:
                    break;
                }
                break;
            case QuickPracticeMenuInput::None:
                break;
            }

            reached = step.track_select_ready ||
                      state.stage == ModernTourContinueStage::Ready;
        }

        assert(reached);
        assert(state.stage == ModernTourContinueStage::Ready);
        assert(state.intent == ModernTourEntryIntent::Restart);
        assert(!state.restore_continuation_at_track_select);
        assert(state.retire_continuation_after_stock_wipe);
    }
}

static void prove_all_tours_reach_track_select() {
    for (std::uint8_t tour = 0; tour < 9; ++tour) {
        auto state = begin_modern_tour_continue(tour);
        ModernTourContinueObservation observation{0xD7, 0, false};

        bool reached = false;
        for (int guard = 0; guard < 320 && !reached; ++guard) {
            const auto step =
                advance_until_action(state, observation);
            state = step.state;

            switch (step.input) {
            case QuickPracticeMenuInput::Up:
                if (observation.selected_option >= 2) {
                    observation.selected_option =
                        static_cast<std::uint8_t>(
                            observation.selected_option - 2);
                }
                break;
            case QuickPracticeMenuInput::Down:
                observation.selected_option =
                    static_cast<std::uint8_t>(
                        observation.selected_option + 2);
                break;
            case QuickPracticeMenuInput::Left:
                if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeMenuInput::Right:
                ++observation.selected_option;
                break;
            case QuickPracticeMenuInput::Accept:
                switch (state.stage) {
                case ModernTourContinueStage::AwaitRider:
                    observation = {0x3C, 0, false};
                    break;
                case ModernTourContinueStage::AwaitTour:
                    observation = {0x6D, 0, false};
                    break;
                case ModernTourContinueStage::AwaitTrack:
                    observation = {0xF6, 0, false};
                    break;
                default:
                    break;
                }
                break;
            case QuickPracticeMenuInput::None:
                break;
            }

            if (step.track_select_ready ||
                state.stage == ModernTourContinueStage::Ready) {
                reached = true;
            }
        }

        assert(reached);
        assert(state.stage == ModernTourContinueStage::Ready);
        assert(observation.menu_id == 0xF6);
    }
}

static void prove_results_route_can_stop_at_stock_tour_select() {
    for (std::uint8_t tour = 0; tour < 9; ++tour) {
        auto state = begin_modern_tour_results_route(tour, true, true);
        assert(state.stage == ModernTourContinueStage::AwaitMain);
        assert(state.stop_at_tour_select);
        assert(state.restore_continuation_at_track_select);

        auto step = advance_until_action(state, {0xD7, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        step = advance_until_action(step.state, {0x3C, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        step = advance_until_action(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::None);
        assert(step.tour_select_ready);
        assert(step.state.stage == ModernTourContinueStage::Ready);
    }

    auto completed = begin_modern_tour_results_route(3, false, false);
    assert(!completed.stop_at_tour_select);
    assert(!completed.restore_continuation_at_track_select);
    auto step = advance_until_action(completed, {0xD7, 0, false});
    step = advance_until_action(step.state, {0x3C, 0, false});
    step = advance_until_action(step.state, {0x6D, 0, false});
    while (step.input != QuickPracticeMenuInput::Accept) {
        auto observation = ModernTourContinueObservation{
            0x6D,
            step.state.tour_option,
            false,
        };
        step = advance_until_action(step.state, observation);
    }
    step = advance_until_action(step.state, {0xF6, 0, false});
    assert(step.track_select_ready);
}

static void prove_next_event_selects_derived_slot_then_confirms() {
    ModernTourEntryContext context{
        ExecutionMode::Modern,
        true,
        true,
        true,
    };
    // Without a unique remaining event, Next Event is never authorized.
    assert(resolve_modern_tour_entry(
               context, ModernTourEntryIntent::NextEvent).intent ==
           ModernTourEntryIntent::None);

    context.next_event_unique = true;
    const auto decision = resolve_modern_tour_entry(
        context, ModernTourEntryIntent::NextEvent);
    assert(decision.intent == ModernTourEntryIntent::NextEvent);
    assert(decision.route_stock_frontend);
    assert(decision.restore_continuation_at_track_select);
    assert(!decision.retire_continuation_after_stock_wipe);

    assert(begin_modern_tour_next_event(0, decision, 5).stage ==
           ModernTourContinueStage::Idle);
    const auto resume = resolve_modern_tour_entry(
        context, ModernTourEntryIntent::Resume);
    assert(begin_modern_tour_next_event(0, resume, 3).stage ==
           ModernTourContinueStage::Idle);

    for (std::uint8_t slot = 0; slot < 5; ++slot) {
        auto state = begin_modern_tour_next_event(1, decision, slot);
        assert(state.stage == ModernTourContinueStage::AwaitMain);
        assert(state.next_event_slot == slot);

        // Selection cannot begin before the Resume restore reaches Ready.
        assert(enter_modern_tour_next_event_selection(state).stage ==
               ModernTourContinueStage::AwaitMain);

        auto step = advance_until_action(state, {0xD7, 0, false});
        step = advance_until_action(step.state, {0x3C, 0, false});
        step = advance_until_action(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::Right);
        step = advance_until_action(step.state, {0x6D, 1, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        step = advance_until_action(step.state, {0xF6, 0, false});
        assert(step.track_select_ready);
        assert(step.state.stage == ModernTourContinueStage::Ready);

        state = enter_modern_tour_next_event_selection(step.state);
        assert(state.stage == ModernTourContinueStage::SelectNextEvent);

        ModernTourContinueObservation observation{0xF6, 0, false};
        for (std::uint8_t row = 0; row < slot; ++row) {
            step = advance_modern_tour_continue(state, observation);
            assert(step.input == QuickPracticeMenuInput::Down);
            state = step.state;
            // Wait for stock to move the cursor before another edge.
            step = advance_modern_tour_continue(state, observation);
            assert(step.input == QuickPracticeMenuInput::None);
            state = step.state;
            ++observation.selected_option;
            // The first observed cursor movement consumes an observation;
            // a new direction cannot be queued on that same guest frame.
            step = advance_modern_tour_continue(state, observation);
            assert(step.input == QuickPracticeMenuInput::None);
            state = step.state;
            // Then wait for the entire physical-style release interval.
            for (std::uint8_t gap = 0;
                 gap < kModernTourNextEventReleaseObservations;
                 ++gap) {
                step = advance_modern_tour_continue(state, observation);
                assert(step.input == QuickPracticeMenuInput::None);
                state = step.state;
            }
        }
        step = advance_modern_tour_continue(state, observation);
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage ==
               ModernTourContinueStage::AwaitNextEventNowPlaying);

        // NOW_PLAYING gets the same settle window before its confirm.
        step = advance_until_action(step.state, {0x16, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage ==
               ModernTourContinueStage::AwaitNextEventRace);

        step = advance_modern_tour_continue(step.state, {0x16, 0, false});
        assert(step.input == QuickPracticeMenuInput::None);
        step = advance_modern_tour_continue(step.state, {0x16, 0, true});
        assert(step.next_event_race_entered);
        assert(step.state.stage == ModernTourContinueStage::Idle);
    }

    // The cursor is moved upward too, and never confirmed off TRACK_SELECT.
    {
        auto state = begin_modern_tour_next_event(0, decision, 1);
        state.stage = ModernTourContinueStage::Ready;
        state = enter_modern_tour_next_event_selection(state);
        auto step = advance_modern_tour_continue(state, {0xF6, 4, false});
        assert(step.input == QuickPracticeMenuInput::Up);
        step = advance_modern_tour_continue(step.state, {0x6D, 3, false});
        assert(step.input == QuickPracticeMenuInput::None);
        assert(step.state.stage == ModernTourContinueStage::SelectNextEvent);
    }

    // A race reached before the Next Event confirm is not Next Event.
    {
        auto state = begin_modern_tour_next_event(0, decision, 2);
        state.stage = ModernTourContinueStage::Ready;
        state = enter_modern_tour_next_event_selection(state);
        const auto early = advance_modern_tour_continue(
            state, {0xF6, 0, true});
        assert(!early.next_event_race_entered);
        assert(early.state.stage == ModernTourContinueStage::Idle);
    }

    // Ordinary Resume never acquires the Next Event selection stages.
    {
        auto state = begin_modern_tour_continue(0);
        state.stage = ModernTourContinueStage::Ready;
        assert(enter_modern_tour_next_event_selection(state).stage ==
               ModernTourContinueStage::Ready);
    }
}

// A resumable tour may be entered while the stock MAIN_MENU cursor rests on
// another row; the route must return it to 1P before confirming.
static void prove_main_cursor_does_not_duplicate_held_up() {
    // A multi-step stock MAIN cursor route must not re-arm UP on the
    // frame that reports the first movement. The real original UI's
    // 2-frame press plus inter-edge gap is independent of tour unlocks.
    auto state = begin_modern_tour_continue(0);
    auto step = advance_until_action(state, {0xD7, 4, false});
    assert(step.input == QuickPracticeMenuInput::Up);
    assert(step.state.waiting_for_selection_change);
    step = advance_modern_tour_continue(step.state, {0xD7, 4, false});
    assert(step.input == QuickPracticeMenuInput::None);
    step = advance_modern_tour_continue(step.state, {0xD7, 3, false});
    assert(step.input == QuickPracticeMenuInput::None);
    assert(!step.state.waiting_for_selection_change);
    for (unsigned release = 0;
         release < kModernTourMenuReleaseObservations; ++release) {
        step = advance_modern_tour_continue(step.state, {0xD7, 3, false});
        assert(step.input == QuickPracticeMenuInput::None);
    }
    step = advance_modern_tour_continue(step.state, {0xD7, 3, false});
    assert(step.input == QuickPracticeMenuInput::Up);
}

// A resumable tour may be entered while the stock MAIN_MENU cursor rests on
// another row; the route must return it to 1P before confirming.
static void prove_main_menu_cursor_returns_to_one_player() {
    auto state = begin_modern_tour_continue(0);
    ModernTourContinueObservation observation{};
    observation.menu_id = 0xD7;
    observation.selected_option = 2;
    auto step = advance_until_action(state, observation);
    assert(step.input == QuickPracticeMenuInput::Up);
    state = step.state;
    observation.selected_option = 1;
    step = advance_until_action(state, observation);
    assert(step.input == QuickPracticeMenuInput::Up);
    state = step.state;
    observation.selected_option = 0;
    step = advance_until_action(state, observation);
    assert(step.input == QuickPracticeMenuInput::Accept);
    assert(step.state.stage == ModernTourContinueStage::AwaitRider);
}

// The stock menu byte is scratch during scene transitions. Its cursor can
// differ without acknowledging a queued direction. Reappearing MAIN or TRACK
// must settle for 60 new source frames, not inherit the earlier settled flag.
static void prove_unexpected_stock_scene_forces_fresh_settle() {
    {
        auto state = begin_modern_tour_continue(0);
        auto first = advance_until_action(state, {0xD7, 4, false});
        assert(first.input == QuickPracticeMenuInput::Up);
        assert(first.state.menu_settled);
        assert(first.state.waiting_for_selection_change);

        // A different menu's cursor value must not be interpreted as
        // a successful UP movement in MAIN.
        auto crossed = advance_modern_tour_continue(
            first.state, {0x6D, 3, false});
        assert(crossed.input == QuickPracticeMenuInput::None);
        assert(!crossed.state.menu_settled);
        assert(!crossed.state.waiting_for_selection_change);
        assert(crossed.state.menu_settle_observations == 0);

        state = crossed.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto settling = advance_modern_tour_continue(
                state, {0xD7, 0, false});
            assert(settling.input == QuickPracticeMenuInput::None);
            state = settling.state;
        }
        auto ready = advance_modern_tour_continue(
            state, {0xD7, 0, false});
        assert(ready.input == QuickPracticeMenuInput::Accept);
        assert(ready.state.stage == ModernTourContinueStage::AwaitRider);
    }

    {
        ModernTourEntryContext context{
            ExecutionMode::Modern, true, true, true, true
        };
        const auto decision = resolve_modern_tour_entry(
            context, ModernTourEntryIntent::NextEvent);
        auto state = begin_modern_tour_next_event(1, decision, 2);
        state.stage = ModernTourContinueStage::Ready;
        state = enter_modern_tour_next_event_selection(state);
        assert(state.menu_settled);

        // A non-TRACK menu cannot lend its cursor or prior settled state to
        // the pending Next Event course selection.
        auto crossed = advance_modern_tour_continue(
            state, {0x16, 2, false});
        assert(crossed.input == QuickPracticeMenuInput::None);
        assert(!crossed.state.menu_settled);
        assert(crossed.state.menu_settle_observations == 0);

        state = crossed.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto settling = advance_modern_tour_continue(
                state, {0xF6, 0, false});
            assert(settling.input == QuickPracticeMenuInput::None);
            state = settling.state;
        }
        auto ready = advance_modern_tour_continue(
            state, {0xF6, 0, false});
        assert(ready.input == QuickPracticeMenuInput::Down);
        assert(ready.state.stage ==
               ModernTourContinueStage::SelectNextEvent);
    }

    // A single mismatched source observation interrupts even a partially
    // completed settle. It cannot be accumulated across an alien scene.
    {
        auto state = begin_modern_tour_continue(0);
        for (unsigned i = 0; i < 40; ++i) {
            auto step = advance_modern_tour_continue(
                state, {0xD7, 0, false});
            assert(step.input == QuickPracticeMenuInput::None);
            state = step.state;
        }
        assert(state.menu_settle_observations == 40);
        auto crossed = advance_modern_tour_continue(
            state, {0x84, 0, false});
        assert(crossed.state.menu_settle_observations == 0);
        state = crossed.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto step = advance_modern_tour_continue(
                state, {0xD7, 0, false});
            assert(step.input == QuickPracticeMenuInput::None);
            state = step.state;
        }
        auto ready = advance_modern_tour_continue(
            state, {0xD7, 0, false});
        assert(ready.input == QuickPracticeMenuInput::Accept);
    }
}

int main() {
    prove_unexpected_stock_scene_forces_fresh_settle();
    prove_main_cursor_does_not_duplicate_held_up();
    prove_main_menu_cursor_returns_to_one_player();
    prove_all_tours_reach_track_select();
    prove_restart_uses_same_stock_route_without_restore();
    prove_results_route_can_stop_at_stock_tour_select();
    prove_next_event_selects_derived_slot_then_confirms();

    {
        auto state = begin_modern_tour_continue(0);
        assert(state.stage == ModernTourContinueStage::AwaitMain);
        assert(state.tour_option == 0);

        auto early = advance_modern_tour_continue(
            state, {0xD7, 0, false});
        assert(early.input == QuickPracticeMenuInput::None);
        assert(!early.state.menu_settled);
        assert(early.state.menu_settle_observations == 1);

        auto step = advance_until_action(state, {0xD7, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitRider);

        step = advance_until_action(step.state, {0x3C, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitTour);

        step = advance_until_action(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitTrack);

        step = advance_until_action(step.state, {0xF6, 0, false});
        assert(step.input == QuickPracticeMenuInput::None);
        assert(step.track_select_ready);
        assert(step.state.stage == ModernTourContinueStage::Ready);
    }

    {
        auto state = begin_modern_tour_continue(8);
        assert(state.tour_option == 9);

        auto step = advance_until_action(state, {0xD7, 0, false});
        step = advance_until_action(step.state, {0x3C, 0, false});

        // From tour option 0, Hunter requires ordinary stock directional
        // navigation rather than any direct menu-state write.
        step = advance_until_action(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::Down);
        assert(step.state.waiting_for_selection_change);

        const auto held = advance_modern_tour_continue(
            step.state, {0x6D, 0, false});
        assert(held.input == QuickPracticeMenuInput::None);
        assert(held.state.waiting_for_selection_change);

        auto advanced = advance_modern_tour_continue(
            held.state, {0x6D, 2, false});
        assert(advanced.input == QuickPracticeMenuInput::None);
        assert(!advanced.state.waiting_for_selection_change);
        for (unsigned release = 0;
             release < kModernTourMenuReleaseObservations; ++release) {
            advanced = advance_modern_tour_continue(
                advanced.state, {0x6D, 2, false});
            assert(advanced.input == QuickPracticeMenuInput::None);
        }
        advanced = advance_modern_tour_continue(
            advanced.state, {0x6D, 2, false});
        assert(advanced.input == QuickPracticeMenuInput::Down);
    }

    assert(begin_modern_tour_continue(9).stage ==
           ModernTourContinueStage::Idle);

    auto state = begin_modern_tour_continue(2);
    const auto failed = advance_modern_tour_continue(
        state, {0xD7, 0, true});
    assert(failed.state.stage == ModernTourContinueStage::Idle);
    assert(failed.input == QuickPracticeMenuInput::None);

    state = begin_modern_tour_continue(2);
    for (std::uint32_t i = 0; i < kModernTourContinueMaxObservations; ++i) {
        const auto waiting = advance_modern_tour_continue(
            state, {0x00, 0, false});
        assert(!waiting.timed_out);
        state = waiting.state;
    }
    const auto timed_out = advance_modern_tour_continue(
        state, {0x00, 0, false});
    assert(timed_out.timed_out);
    assert(timed_out.state.stage == ModernTourContinueStage::Idle);
    assert(timed_out.input == QuickPracticeMenuInput::None);

    return 0;
}

#include "modern_tour_continue.hpp"

#include <cassert>

using namespace ur::product;

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
        for (int guard = 0; guard < 48 && !reached; ++guard) {
            const auto step =
                advance_modern_tour_continue(state, observation);
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
        for (int guard = 0; guard < 48 && !reached; ++guard) {
            const auto step =
                advance_modern_tour_continue(state, observation);
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

int main() {
    prove_all_tours_reach_track_select();
    prove_restart_uses_same_stock_route_without_restore();

    {
        auto state = begin_modern_tour_continue(0);
        assert(state.stage == ModernTourContinueStage::AwaitMain);
        assert(state.tour_option == 0);

        auto step = advance_modern_tour_continue(state, {0xD7, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitRider);

        step = advance_modern_tour_continue(step.state, {0x3C, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitTour);

        step = advance_modern_tour_continue(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::Accept);
        assert(step.state.stage == ModernTourContinueStage::AwaitTrack);

        step = advance_modern_tour_continue(step.state, {0xF6, 0, false});
        assert(step.input == QuickPracticeMenuInput::None);
        assert(step.track_select_ready);
        assert(step.state.stage == ModernTourContinueStage::Ready);
    }

    {
        auto state = begin_modern_tour_continue(8);
        assert(state.tour_option == 9);

        auto step = advance_modern_tour_continue(state, {0xD7, 0, false});
        step = advance_modern_tour_continue(step.state, {0x3C, 0, false});

        // From tour option 0, Hunter requires ordinary stock directional
        // navigation rather than any direct menu-state write.
        step = advance_modern_tour_continue(step.state, {0x6D, 0, false});
        assert(step.input == QuickPracticeMenuInput::Down);
        assert(step.state.waiting_for_selection_change);

        const auto held = advance_modern_tour_continue(
            step.state, {0x6D, 0, false});
        assert(held.input == QuickPracticeMenuInput::None);
        assert(held.state.waiting_for_selection_change);

        const auto advanced = advance_modern_tour_continue(
            held.state, {0x6D, 2, false});
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

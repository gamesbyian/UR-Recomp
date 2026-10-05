#include "quick_practice_launch.hpp"

#include <cassert>

using namespace ur::product;

static QuickPracticeLaunchStep settle_menu(
    QuickPracticeLaunchState state,
    QuickPracticeLaunchObservation observation
) {
    QuickPracticeLaunchStep step{};
    for (std::uint16_t i = 0; i < kQuickPracticeMenuSettleObservations; ++i) {
        step = advance_quick_practice_launch(state, observation);
        state = step.state;
        if (i + 1 < kQuickPracticeMenuSettleObservations) {
            assert(step.input == QuickPracticeLaunchInput::None);
            assert(!step.race_ready);
            assert(!step.course_mismatch);
            assert(!step.route_violation);
        }
    }
    return step;
}

static void prove_all_tracks_reach_race() {
    for (std::uint8_t track = 0; track < 45; ++track) {
        auto state = begin_quick_practice_launch(
            quick_practice_target_for_track(track));
        QuickPracticeLaunchObservation observation{0xD7, 0, false, -1};

        bool reached = false;
        for (int guard = 0; guard < 2500 && !reached; ++guard) {
            const auto step = advance_quick_practice_launch(state, observation);
            state = step.state;

            switch (step.input) {
            case QuickPracticeLaunchInput::Up:
                if (observation.menu_id == 0x6D) {
                    if (observation.selected_option >= 2) {
                        observation.selected_option =
                            static_cast<std::uint8_t>(
                                observation.selected_option - 2);
                    }
                } else if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeLaunchInput::Down:
                observation.selected_option = static_cast<std::uint8_t>(
                    observation.selected_option +
                    (observation.menu_id == 0x6D ? 2 : 1));
                break;
            case QuickPracticeLaunchInput::Left:
                if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeLaunchInput::Right:
                ++observation.selected_option;
                break;
            case QuickPracticeLaunchInput::Accept:
                switch (state.stage) {
                case QuickPracticeLaunchStage::AwaitRider:
                    observation = {0x3C, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitTour:
                    observation = {0x6D, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitTrack:
                    observation = {0xF6, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitNowPlaying:
                    observation = {
                        0x16, observation.selected_option, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitRace:
                    observation = {0x00, 0, true, track};
                    break;
                default:
                    break;
                }
                break;
            case QuickPracticeLaunchInput::None:
                break;
            }

            assert(!step.course_mismatch);
            assert(!step.route_violation);
            if (state.stage == QuickPracticeLaunchStage::Active ||
                step.race_ready) {
                reached = true;
            }
        }

        assert(reached);
        assert(state.stage == QuickPracticeLaunchStage::Active);
    }
}

int main() {
    prove_all_tracks_reach_race();

    const auto target =
        quick_practice_target_for_track(12);  // Shuffler / slot 3.
    auto state = begin_quick_practice_launch(target);
    assert(state.stage == QuickPracticeLaunchStage::AwaitMain);

    auto step = settle_menu(state, {0xD7, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRider);
    state = step.state;

    step = settle_menu(state, {0x3C, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTour);
    state = step.state;

    step = settle_menu(state, {0x6D, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    auto held = advance_quick_practice_launch(
        step.state, {0x6D, 0, false, -1});
    assert(held.input == QuickPracticeLaunchInput::None);
    assert(held.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(
        held.state, {0x6D, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTrack);
    state = step.state;

    step = settle_menu(state, {0xF6, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    held = advance_quick_practice_launch(
        step.state, {0xF6, 0, false, -1});
    assert(held.input == QuickPracticeLaunchInput::None);

    step = advance_quick_practice_launch(
        held.state, {0xF6, 1, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(
        step.state, {0xF6, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitNowPlaying);
    state = step.state;

    step = settle_menu(state, {0x16, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRace);

    // Race-active without decoded-course identity waits rather than guessing.
    step = advance_quick_practice_launch(
        step.state, {0x00, 0, true, -1});
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRace);
    assert(!step.race_ready);
    assert(!step.course_mismatch);
    assert(!step.route_violation);

    step = advance_quick_practice_launch(
        step.state, {0x00, 0, true, target.track_id});
    assert(step.input == QuickPracticeLaunchInput::None);
    assert(step.state.stage == QuickPracticeLaunchStage::Active);
    assert(step.race_ready);

    // A race reached before the router has completed Now Playing is not a
    // successful Practice launch, even if its course happens to match.
    state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    step = advance_quick_practice_launch(
        state, {0x00, 0, true, 0});
    assert(step.state.stage == QuickPracticeLaunchStage::Idle);
    assert(!step.race_ready);
    assert(step.route_violation);

    // A different authoritative course after the correct frontend route also
    // fails closed.
    state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    state.stage = QuickPracticeLaunchStage::AwaitRace;
    step = advance_quick_practice_launch(
        state, {0x00, 0, true, 1});
    assert(step.state.stage == QuickPracticeLaunchStage::Idle);
    assert(!step.race_ready);
    assert(step.course_mismatch);
    assert(!step.route_violation);

    // Invalid targets fail closed.
    state = begin_quick_practice_launch({});
    assert(state.stage == QuickPracticeLaunchStage::Idle);
    step = advance_quick_practice_launch(
        state, {0xD7, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::None);

    return 0;
}

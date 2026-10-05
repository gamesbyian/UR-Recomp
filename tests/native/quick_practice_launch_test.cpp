#include "quick_practice_launch.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto target = quick_practice_target_for_track(12); // Shuffler / slot 3.
    auto state = begin_quick_practice_launch(target);
    assert(state.stage == QuickPracticeLaunchStage::AwaitMain);

    auto step = advance_quick_practice_launch(state, {0xD7, 0, false});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRider);

    step = advance_quick_practice_launch(step.state, {0x3C, 0, false});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTour);

    step = advance_quick_practice_launch(step.state, {0x6D, 0, false});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);
    assert(step.state.selection_before_input == 0);

    // The menu can remain on the same option for several host frames. Do not
    // enqueue repeated Down pulses while the first stock input is settling.
    auto held = advance_quick_practice_launch(step.state, {0x6D, 0, false});
    assert(held.input == QuickPracticeLaunchInput::None);
    assert(held.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(held.state, {0x6D, 2, false});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTrack);
    assert(!step.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(step.state, {0xF6, 0, false});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    held = advance_quick_practice_launch(step.state, {0xF6, 0, false});
    assert(held.input == QuickPracticeLaunchInput::None);

    step = advance_quick_practice_launch(held.state, {0xF6, 1, false});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(step.state, {0xF6, 2, false});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitNowPlaying);

    step = advance_quick_practice_launch(step.state, {0x16, 2, false});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRace);

    step = advance_quick_practice_launch(step.state, {0x00, 0, true});
    assert(step.input == QuickPracticeLaunchInput::None);
    assert(step.state.stage == QuickPracticeLaunchStage::Active);
    assert(step.race_ready);

    // Active-race detection is authoritative even if an intermediate frontend
    // state was too brief to sample.
    state = begin_quick_practice_launch(quick_practice_target_for_track(0));
    step = advance_quick_practice_launch(state, {0x00, 0, true});
    assert(step.state.stage == QuickPracticeLaunchStage::Active);
    assert(step.race_ready);

    // Invalid targets fail closed.
    state = begin_quick_practice_launch({});
    assert(state.stage == QuickPracticeLaunchStage::Idle);
    step = advance_quick_practice_launch(state, {0xD7, 0, false});
    assert(step.input == QuickPracticeLaunchInput::None);

    // Track cursor can move upward without repeating while the guest settles.
    state = begin_quick_practice_launch(quick_practice_target_for_track(1));
    state.stage = QuickPracticeLaunchStage::AwaitTrack;
    step = advance_quick_practice_launch(state, {0xF6, 4, false});
    assert(step.input == QuickPracticeLaunchInput::Up);
    held = advance_quick_practice_launch(step.state, {0xF6, 4, false});
    assert(held.input == QuickPracticeLaunchInput::None);
    step = advance_quick_practice_launch(held.state, {0xF6, 3, false});
    assert(step.input == QuickPracticeLaunchInput::Up);

    return 0;
}

#include "modern_tour_continue.hpp"

#include <cassert>

using namespace ur::product;

int main() {
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

    return 0;
}

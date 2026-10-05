#include "quick_practice_available_selection.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto normal = quick_practice_normal_tours_only();

    auto state = open_available_quick_practice_selection(44, normal);
    assert(state.visible);
    assert(state.picker.track_id == 0);

    state.picker.track_id = 39;
    auto out = quick_practice_available_selection_apply(
        state, QuickPracticeSelectionCommand::NextCourse, normal);
    assert(out.result == QuickPracticeSelectionResult::Updated);
    assert(out.state.picker.track_id == 0);

    // Hunter is skipped by tour navigation when it is not available.
    state.picker.track_id = 37;  // Sprinter slot 3.
    out = quick_practice_available_selection_apply(
        state, QuickPracticeSelectionCommand::NextTour, normal);
    assert(out.state.picker.track_id == 2);  // Crawler slot 3.

    // Sparse tours preserve the selected slot where possible.
    auto sparse = quick_practice_no_tracks();
    for (std::uint8_t slot = 0; slot < 5; ++slot) {
        sparse = quick_practice_set_track_available(sparse, slot, true);
        sparse = quick_practice_set_track_available(
            sparse, static_cast<std::uint8_t>(10 + slot), true);
    }
    state = open_available_quick_practice_selection(2, sparse);
    out = quick_practice_available_selection_apply(
        state, QuickPracticeSelectionCommand::NextTour, sparse);
    assert(out.state.picker.track_id == 12);
    out = quick_practice_available_selection_apply(
        out.state, QuickPracticeSelectionCommand::PreviousTour, sparse);
    assert(out.state.picker.track_id == 2);

    // If the preferred slot is unavailable in the next visible tour, choose
    // that tour's first available course rather than exposing a hidden one.
    auto uneven = quick_practice_no_tracks();
    uneven = quick_practice_set_track_available(uneven, 4, true);
    uneven = quick_practice_set_track_available(uneven, 11, true);
    state = open_available_quick_practice_selection(4, uneven);
    out = quick_practice_available_selection_apply(
        state, QuickPracticeSelectionCommand::NextTour, uneven);
    assert(out.state.picker.track_id == 11);

    // Confirmation cannot launch a course outside the availability mask.
    state = open_quick_practice_selection(44);
    out = quick_practice_available_selection_apply(
        state, QuickPracticeSelectionCommand::Confirm, normal);
    assert(out.result == QuickPracticeSelectionResult::NoOp);
    assert(!out.target.valid);
    assert(out.state.visible);
    assert(out.state.picker.track_id == 0);

    out = quick_practice_available_selection_apply(
        out.state, QuickPracticeSelectionCommand::Confirm, normal);
    assert(out.result == QuickPracticeSelectionResult::Confirmed);
    assert(out.target.valid);
    assert(out.target.track_id == 0);
    assert(!out.state.visible);

    // No available tracks means no surface and no possible launch.
    state = open_available_quick_practice_selection(
        0, quick_practice_no_tracks());
    assert(!state.visible);
    out = quick_practice_available_selection_apply(
        state,
        QuickPracticeSelectionCommand::Confirm,
        quick_practice_no_tracks());
    assert(out.result == QuickPracticeSelectionResult::NoOp);
    assert(!out.target.valid);

    return 0;
}

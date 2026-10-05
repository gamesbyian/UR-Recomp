#include "quick_practice_selection.hpp"

#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    auto state = open_quick_practice_selection();
    assert(state.visible);
    assert(quick_practice_selection_course(state));
    assert(quick_practice_selection_course(state)->name == std::string_view("Dragster"));

    auto out = quick_practice_selection_apply(
        state, QuickPracticeSelectionCommand::NextCourse);
    assert(out.result == QuickPracticeSelectionResult::Updated);
    assert(out.state.visible);
    assert(out.state.picker.track_id == 1);

    out = quick_practice_selection_apply(
        out.state, QuickPracticeSelectionCommand::NextTour);
    assert(out.result == QuickPracticeSelectionResult::Updated);
    assert(out.state.picker.track_id == 6);
    assert(quick_practice_selection_course(out.state)->name == std::string_view("Twinpeak"));

    out = quick_practice_selection_apply(
        out.state, QuickPracticeSelectionCommand::Confirm);
    assert(out.result == QuickPracticeSelectionResult::Confirmed);
    assert(!out.state.visible);
    assert(out.target.valid);
    assert(out.target.track_id == 6);
    assert(out.target.tour_option == 1);
    assert(out.target.track_slot == 1);

    const auto closed_noop = quick_practice_selection_apply(
        out.state, QuickPracticeSelectionCommand::NextCourse);
    assert(closed_noop.result == QuickPracticeSelectionResult::NoOp);
    assert(!closed_noop.state.visible);

    state = open_quick_practice_selection(44);
    assert(quick_practice_selection_course(state)->name == std::string_view("To and Fro"));
    out = quick_practice_selection_apply(
        state, QuickPracticeSelectionCommand::NextCourse);
    assert(out.state.picker.track_id == 0);

    state = open_quick_practice_selection(255);
    assert(state.picker.track_id == 0);

    out = quick_practice_selection_apply(
        state, QuickPracticeSelectionCommand::Cancel);
    assert(out.result == QuickPracticeSelectionResult::Cancelled);
    assert(!out.state.visible);
    assert(!out.target.valid);

    return 0;
}

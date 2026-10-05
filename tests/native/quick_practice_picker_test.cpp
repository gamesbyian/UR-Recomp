#include "quick_practice_picker.hpp"

#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    QuickPracticePickerState state{};

    assert(quick_practice_picker_course(state)->name == std::string_view("Dragster"));

    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::NextCourse);
    assert(state.track_id == 1);
    assert(quick_practice_picker_course(state)->name == std::string_view("Zoom Zoo"));

    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::PreviousCourse);
    assert(state.track_id == 0);

    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::PreviousCourse);
    assert(state.track_id == 44);
    assert(quick_practice_picker_course(state)->name == std::string_view("To and Fro"));

    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::NextCourse);
    assert(state.track_id == 0);

    state.track_id = 2;  // Bowl, slot 3.
    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::NextTour);
    assert(state.track_id == 7);
    assert(quick_practice_picker_course(state)->name == std::string_view("Skier"));
    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::PreviousTour);
    assert(state.track_id == 2);

    state.track_id = 42;  // Hunter, slot 3.
    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::NextTour);
    assert(state.track_id == 2);  // Wrap to Crawler, preserve slot.

    state.track_id = 255;
    state = quick_practice_picker_apply(
        state, QuickPracticePickerAction::NextTour);
    assert(state.track_id == 5);  // Invalid normalizes to Dragster, then next tour.

    state.track_id = 12;
    const auto target = quick_practice_picker_target(state);
    assert(target.valid);
    assert(target.tour_option == 2);
    assert(target.track_slot == 2);

    return 0;
}

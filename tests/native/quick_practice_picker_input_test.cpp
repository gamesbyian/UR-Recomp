#include "quick_practice_picker_input.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto d = quick_practice_picker_input({QuickPracticePickerControl::Up, false});
    assert(d.handled && d.apply_selection_command);
    assert(d.command == QuickPracticeSelectionCommand::PreviousCourse);

    d = quick_practice_picker_input({QuickPracticePickerControl::Down, true});
    assert(d.handled && d.apply_selection_command);
    assert(d.command == QuickPracticeSelectionCommand::NextCourse);

    d = quick_practice_picker_input({QuickPracticePickerControl::Left, false});
    assert(d.command == QuickPracticeSelectionCommand::PreviousTour);

    d = quick_practice_picker_input({QuickPracticePickerControl::Right, true});
    assert(d.command == QuickPracticeSelectionCommand::NextTour);

    d = quick_practice_picker_input({QuickPracticePickerControl::Confirm, false});
    assert(d.handled && d.apply_selection_command);
    assert(d.command == QuickPracticeSelectionCommand::Confirm);

    d = quick_practice_picker_input({QuickPracticePickerControl::Confirm, true});
    assert(d.handled && !d.apply_selection_command);

    d = quick_practice_picker_input({QuickPracticePickerControl::Cancel, false});
    assert(d.handled && d.apply_selection_command);
    assert(d.command == QuickPracticeSelectionCommand::Cancel);

    d = quick_practice_picker_input({QuickPracticePickerControl::Cancel, true});
    assert(d.handled && !d.apply_selection_command);

    d = quick_practice_picker_input({QuickPracticePickerControl::None, false});
    assert(!d.handled && !d.apply_selection_command);

    return 0;
}

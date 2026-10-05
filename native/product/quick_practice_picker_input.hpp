#pragma once

#include "quick_practice_selection.hpp"

namespace ur::product {

enum class QuickPracticePickerControl {
    None,
    Up,
    Down,
    Left,
    Right,
    Confirm,
    Cancel,
};

struct QuickPracticePickerInput {
    QuickPracticePickerControl control = QuickPracticePickerControl::None;
    bool repeated = false;
};

struct QuickPracticePickerInputDecision {
    bool handled = false;
    bool apply_selection_command = false;
    QuickPracticeSelectionCommand command =
        QuickPracticeSelectionCommand::NextCourse;
};

constexpr QuickPracticePickerInputDecision quick_practice_picker_input(
    QuickPracticePickerInput input
) noexcept {
    switch (input.control) {
    case QuickPracticePickerControl::Up:
        return {true, true, QuickPracticeSelectionCommand::PreviousCourse};
    case QuickPracticePickerControl::Down:
        return {true, true, QuickPracticeSelectionCommand::NextCourse};
    case QuickPracticePickerControl::Left:
        return {true, true, QuickPracticeSelectionCommand::PreviousTour};
    case QuickPracticePickerControl::Right:
        return {true, true, QuickPracticeSelectionCommand::NextTour};
    case QuickPracticePickerControl::Confirm:
        if (input.repeated) return {true, false, QuickPracticeSelectionCommand::Confirm};
        return {true, true, QuickPracticeSelectionCommand::Confirm};
    case QuickPracticePickerControl::Cancel:
        if (input.repeated) return {true, false, QuickPracticeSelectionCommand::Cancel};
        return {true, true, QuickPracticeSelectionCommand::Cancel};
    case QuickPracticePickerControl::None:
        return {};
    }
    return {};
}

}  // namespace ur::product

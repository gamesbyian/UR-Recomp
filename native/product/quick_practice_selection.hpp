#pragma once

#include "quick_practice_picker.hpp"

#include <cstdint>

namespace ur::product {

enum class QuickPracticeSelectionCommand {
    PreviousCourse,
    NextCourse,
    PreviousTour,
    NextTour,
    Confirm,
    Cancel,
};

enum class QuickPracticeSelectionResult {
    NoOp,
    Updated,
    Confirmed,
    Cancelled,
};

struct QuickPracticeSelection {
    bool visible = false;
    QuickPracticePickerState picker{};
};

struct QuickPracticeSelectionOutcome {
    QuickPracticeSelectionResult result = QuickPracticeSelectionResult::NoOp;
    QuickPracticeSelection state{};
    QuickPracticeTarget target{};
};

constexpr QuickPracticeSelection open_quick_practice_selection(
    std::uint8_t initial_track_id = 0
) noexcept {
    QuickPracticeSelection state;
    state.visible = true;
    state.picker.track_id = quick_practice_course(initial_track_id)
        ? initial_track_id
        : 0;
    return state;
}

constexpr QuickPracticeSelectionOutcome quick_practice_selection_apply(
    QuickPracticeSelection state,
    QuickPracticeSelectionCommand command
) noexcept {
    QuickPracticeSelectionOutcome out;
    out.state = state;

    if (!state.visible) return out;

    switch (command) {
    case QuickPracticeSelectionCommand::PreviousCourse:
        out.state.picker = quick_practice_picker_apply(
            state.picker, QuickPracticePickerAction::PreviousCourse);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::NextCourse:
        out.state.picker = quick_practice_picker_apply(
            state.picker, QuickPracticePickerAction::NextCourse);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::PreviousTour:
        out.state.picker = quick_practice_picker_apply(
            state.picker, QuickPracticePickerAction::PreviousTour);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::NextTour:
        out.state.picker = quick_practice_picker_apply(
            state.picker, QuickPracticePickerAction::NextTour);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::Confirm:
        out.target = quick_practice_picker_target(state.picker);
        if (!out.target.valid) return out;
        out.state.visible = false;
        out.result = QuickPracticeSelectionResult::Confirmed;
        return out;
    case QuickPracticeSelectionCommand::Cancel:
        out.state.visible = false;
        out.result = QuickPracticeSelectionResult::Cancelled;
        return out;
    }

    return out;
}

constexpr const QuickPracticeCourse* quick_practice_selection_course(
    const QuickPracticeSelection& state
) noexcept {
    return state.visible ? quick_practice_picker_course(state.picker) : nullptr;
}

}  // namespace ur::product

#pragma once

#include "quick_practice_availability.hpp"
#include "quick_practice_selection.hpp"

namespace ur::product {

constexpr QuickPracticePickerState quick_practice_available_tour_step(
    QuickPracticePickerState state,
    QuickPracticeAvailability availability,
    int direction
) noexcept {
    state = quick_practice_normalize_available_picker(state, availability);
    if (quick_practice_available_count(availability) == 0 || direction == 0) {
        return state;
    }

    const int current_block = static_cast<int>(state.track_id / 5);
    const std::uint8_t preferred_slot =
        static_cast<std::uint8_t>(state.track_id % 5);
    const int delta = direction > 0 ? 1 : -1;

    for (int distance = 1; distance <= 9; ++distance) {
        int block = (current_block + delta * distance) % 9;
        if (block < 0) block += 9;

        const auto preferred = static_cast<std::uint8_t>(
            block * 5 + preferred_slot);
        if (quick_practice_track_available(availability, preferred)) {
            state.track_id = preferred;
            return state;
        }

        for (std::uint8_t slot = 0; slot < 5; ++slot) {
            const auto candidate = static_cast<std::uint8_t>(
                block * 5 + slot);
            if (quick_practice_track_available(availability, candidate)) {
                state.track_id = candidate;
                return state;
            }
        }
    }
    return state;
}

constexpr QuickPracticeSelection open_available_quick_practice_selection(
    std::uint8_t initial_track_id,
    QuickPracticeAvailability availability
) noexcept {
    QuickPracticeSelection state;
    if (quick_practice_available_count(availability) == 0) return state;

    state.visible = true;
    state.picker.track_id = initial_track_id;
    state.picker =
        quick_practice_normalize_available_picker(state.picker, availability);
    return state;
}

constexpr QuickPracticeSelectionOutcome
quick_practice_available_selection_apply(
    QuickPracticeSelection state,
    QuickPracticeSelectionCommand command,
    QuickPracticeAvailability availability
) noexcept {
    QuickPracticeSelectionOutcome out;
    out.state = state;

    if (!state.visible) return out;

    out.state.picker =
        quick_practice_normalize_available_picker(state.picker, availability);

    if (quick_practice_available_count(availability) == 0) {
        out.state.visible = false;
        return out;
    }

    switch (command) {
    case QuickPracticeSelectionCommand::PreviousCourse:
        out.state.picker = quick_practice_available_course_step(
            out.state.picker, availability, -1);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::NextCourse:
        out.state.picker = quick_practice_available_course_step(
            out.state.picker, availability, +1);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::PreviousTour:
        out.state.picker = quick_practice_available_tour_step(
            out.state.picker, availability, -1);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::NextTour:
        out.state.picker = quick_practice_available_tour_step(
            out.state.picker, availability, +1);
        out.result = QuickPracticeSelectionResult::Updated;
        return out;
    case QuickPracticeSelectionCommand::Confirm:
        if (!quick_practice_picker_launchable(out.state.picker, availability)) {
            return out;
        }
        out.target = quick_practice_picker_target(out.state.picker);
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

}  // namespace ur::product

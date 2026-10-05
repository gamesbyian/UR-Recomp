#pragma once

#include "quick_practice_catalog.hpp"

#include <cstdint>

namespace ur::product {

enum class QuickPracticePickerAction {
    PreviousCourse,
    NextCourse,
    PreviousTour,
    NextTour,
};

struct QuickPracticePickerState {
    std::uint8_t track_id = 0;
};

constexpr std::uint8_t quick_practice_wrap_track(int value) noexcept {
    constexpr int kCount = static_cast<int>(kQuickPracticeCourses.size());
    value %= kCount;
    if (value < 0) value += kCount;
    return static_cast<std::uint8_t>(value);
}

constexpr QuickPracticePickerState quick_practice_picker_apply(
    QuickPracticePickerState state,
    QuickPracticePickerAction action
) noexcept {
    const auto* course = quick_practice_course(state.track_id);
    if (!course) state.track_id = 0;
    const auto* normalized = quick_practice_course(state.track_id);
    const std::uint8_t slot = normalized ? normalized->tour_slot : 0;

    switch (action) {
    case QuickPracticePickerAction::PreviousCourse:
        state.track_id = quick_practice_wrap_track(
            static_cast<int>(state.track_id) - 1);
        break;
    case QuickPracticePickerAction::NextCourse:
        state.track_id = quick_practice_wrap_track(
            static_cast<int>(state.track_id) + 1);
        break;
    case QuickPracticePickerAction::PreviousTour: {
        int block = static_cast<int>(state.track_id / 5);
        block = (block + 8) % 9;
        state.track_id = static_cast<std::uint8_t>(block * 5 + slot);
        break;
    }
    case QuickPracticePickerAction::NextTour: {
        int block = static_cast<int>(state.track_id / 5);
        block = (block + 1) % 9;
        state.track_id = static_cast<std::uint8_t>(block * 5 + slot);
        break;
    }
    }
    return state;
}

constexpr const QuickPracticeCourse* quick_practice_picker_course(
    QuickPracticePickerState state
) noexcept {
    return quick_practice_course(state.track_id);
}

constexpr QuickPracticeTarget quick_practice_picker_target(
    QuickPracticePickerState state
) noexcept {
    return quick_practice_target_for_track(state.track_id);
}

}  // namespace ur::product

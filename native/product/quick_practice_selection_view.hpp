#pragma once

#include "quick_practice_selection.hpp"

#include <cstdint>
#include <string_view>

namespace ur::product {

struct QuickPracticeSelectionView {
    std::string_view course_name;
    std::string_view tour_name;
    std::string_view kind_label;
    std::uint8_t course_number = 0;
    std::uint8_t course_count = 45;
    std::uint8_t tour_number = 0;
    std::uint8_t tour_count = 9;
    std::uint8_t slot_number = 0;
    std::uint8_t slot_count = 5;
    bool valid = false;
};

constexpr QuickPracticeSelectionView quick_practice_selection_view(
    const QuickPracticeSelection& state
) noexcept {
    const auto* course = quick_practice_selection_course(state);
    if (!course) return {};

    return {
        course->name,
        course->tour_name,
        quick_practice_kind_label(course->kind),
        static_cast<std::uint8_t>(course->track_id + 1),
        45,
        course->tour_index,
        9,
        static_cast<std::uint8_t>(course->tour_slot + 1),
        5,
        true,
    };
}

}  // namespace ur::product

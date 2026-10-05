#pragma once

#include "quick_practice_selection_view.hpp"

#include <array>
#include <cstdio>
#include <string>

namespace ur::product {

struct QuickPracticeOverlayRows {
    std::array<std::string, 7> rows{};
    bool valid = false;
};

inline QuickPracticeOverlayRows quick_practice_overlay_rows(
    const QuickPracticeSelectionView& view
) {
    QuickPracticeOverlayRows out;
    if (!view.valid) return out;

    char course_index[32];
    char tour_index[32];
    char slot_index[32];
    std::snprintf(
        course_index, sizeof(course_index),
        "COURSE %u / %u",
        static_cast<unsigned>(view.course_number),
        static_cast<unsigned>(view.course_count));
    std::snprintf(
        tour_index, sizeof(tour_index),
        "TOUR %u / %u",
        static_cast<unsigned>(view.tour_number),
        static_cast<unsigned>(view.tour_count));
    std::snprintf(
        slot_index, sizeof(slot_index),
        "TRACK %u / %u",
        static_cast<unsigned>(view.slot_number),
        static_cast<unsigned>(view.slot_count));

    out.rows[0] = "QUICK PRACTICE";
    out.rows[1] = std::string(view.course_name);
    out.rows[2] = std::string(view.tour_name) + "  " +
        std::string(view.kind_label);
    out.rows[3] = course_index;
    out.rows[4] = std::string(tour_index) + "  " + slot_index;
    out.rows[5] = "UP/DOWN COURSE  LEFT/RIGHT TOUR";
    out.rows[6] = "ENTER/A PLAY  ESC/B CANCEL";
    out.valid = true;
    return out;
}

}  // namespace ur::product

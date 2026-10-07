#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

// The Modern main-menu "continue" strip: at most one Tour row and one Recent
// Course row, each naming its keyboard and controller input. It is
// presentation only; the actions behind the rows are the existing Tour surface
// and the existing Recent Course Quick Practice launch.
inline constexpr std::size_t kModernMainMenuStripMaxRows = 2;
// 8-pixel glyphs inside a 248-pixel strip with 6-pixel padding each side;
// sized so every shipping course and tour name fits untruncated.
inline constexpr std::size_t kModernMainMenuStripMaxChars = 29;

struct ModernMainMenuTourEntry {
    // Set when a unique Next Event exists; otherwise the tour summary shows.
    std::string_view next_event_course;
    std::string_view tour_name;
    std::uint8_t completed = 0;
};

struct ModernMainMenuStripInput {
    std::optional<ModernMainMenuTourEntry> tour;
    std::optional<std::string_view> recent_course;
};

struct ModernMainMenuStrip {
    std::array<std::string, kModernMainMenuStripMaxRows> rows{};
    std::size_t row_count = 0;
};

inline std::string modern_main_menu_strip_row(
    std::string_view prefix,
    std::string_view value) {
    std::string row(prefix);
    const std::size_t room =
        row.size() < kModernMainMenuStripMaxChars
            ? kModernMainMenuStripMaxChars - row.size()
            : 0;
    row.append(value.substr(0, room));
    return row;
}

inline ModernMainMenuStrip build_modern_main_menu_strip(
    const ModernMainMenuStripInput& input) {
    ModernMainMenuStrip strip;
    if (input.tour) {
        const auto& tour = *input.tour;
        std::string row;
        if (!tour.next_event_course.empty()) {
            row = modern_main_menu_strip_row(
                "F3/Y NEXT EVENT ", tour.next_event_course);
        } else {
            const unsigned completed = tour.completed > 5 ? 5u : tour.completed;
            std::string progress = " ";
            progress += static_cast<char>('0' + completed);
            progress += "/5";
            const std::string_view name =
                tour.tour_name.empty() ? std::string_view("TOUR")
                                       : tour.tour_name;
            // Keep the progress visible even when the name must shrink.
            const std::size_t prefix = std::string_view("F3/Y TOUR ").size();
            const std::size_t room =
                kModernMainMenuStripMaxChars - prefix - progress.size();
            row = std::string("F3/Y TOUR ") +
                  std::string(name.substr(0, room)) + progress;
        }
        strip.rows[strip.row_count++] = std::move(row);
    }
    if (input.recent_course && !input.recent_course->empty()) {
        strip.rows[strip.row_count++] = modern_main_menu_strip_row(
            "F6/R RECENT ", *input.recent_course);
    }
    return strip;
}

}  // namespace ur::product

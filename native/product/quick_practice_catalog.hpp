#pragma once

#include "quick_practice_route.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace ur::product {

enum class QuickPracticeCourseKind {
    Race,
    Circuit,
    Stunt,
};

struct QuickPracticeCourse {
    std::uint8_t track_id;
    std::string_view name;
    std::string_view tour_name;
    std::uint8_t tour_index;
    std::uint8_t tour_slot;
    QuickPracticeCourseKind kind;
};

constexpr std::array<QuickPracticeCourse, 45> kQuickPracticeCourses{{
    {0, "Dragster", "Crawler", 1, 0, QuickPracticeCourseKind::Race},
    {1, "Zoom Zoo", "Crawler", 1, 1, QuickPracticeCourseKind::Circuit},
    {2, "Bowl", "Crawler", 1, 2, QuickPracticeCourseKind::Stunt},
    {3, "Switcher", "Crawler", 1, 3, QuickPracticeCourseKind::Race},
    {4, "Monster", "Crawler", 1, 4, QuickPracticeCourseKind::Circuit},
    {5, "Wobble", "Jumper", 2, 0, QuickPracticeCourseKind::Race},
    {6, "Twinpeak", "Jumper", 2, 1, QuickPracticeCourseKind::Circuit},
    {7, "Skier", "Jumper", 2, 2, QuickPracticeCourseKind::Stunt},
    {8, "Loopback", "Jumper", 2, 3, QuickPracticeCourseKind::Race},
    {9, "Small Cut", "Jumper", 2, 4, QuickPracticeCourseKind::Circuit},
    {10, "Looper", "Shuffler", 3, 0, QuickPracticeCourseKind::Race},
    {11, "MegaJump", "Shuffler", 3, 1, QuickPracticeCourseKind::Circuit},
    {12, "Jumps", "Shuffler", 3, 2, QuickPracticeCourseKind::Stunt},
    {13, "Flat Fun", "Shuffler", 3, 3, QuickPracticeCourseKind::Race},
    {14, "Infinity", "Shuffler", 3, 4, QuickPracticeCourseKind::Circuit},
    {15, "Last One", "Bounder", 4, 0, QuickPracticeCourseKind::Race},
    {16, "Marathon", "Bounder", 4, 1, QuickPracticeCourseKind::Circuit},
    {17, "Circle", "Bounder", 4, 2, QuickPracticeCourseKind::Stunt},
    {18, "Plinkey", "Bounder", 4, 3, QuickPracticeCourseKind::Race},
    {19, "Jumpover", "Bounder", 4, 4, QuickPracticeCourseKind::Circuit},
    {20, "Dragrace", "Walker", 5, 0, QuickPracticeCourseKind::Race},
    {21, "Ping Pong", "Walker", 5, 1, QuickPracticeCourseKind::Circuit},
    {22, "Hill Climb", "Walker", 5, 2, QuickPracticeCourseKind::Stunt},
    {23, "Hybrid", "Walker", 5, 3, QuickPracticeCourseKind::Race},
    {24, "Short Cut", "Walker", 5, 4, QuickPracticeCourseKind::Circuit},
    {25, "Down+Up", "Runner", 6, 0, QuickPracticeCourseKind::Race},
    {26, "Highroad", "Runner", 6, 1, QuickPracticeCourseKind::Circuit},
    {27, "Spine", "Runner", 6, 2, QuickPracticeCourseKind::Stunt},
    {28, "Boo!", "Runner", 6, 3, QuickPracticeCourseKind::Race},
    {29, "Fire Escape", "Runner", 6, 4, QuickPracticeCourseKind::Circuit},
    {30, "Wario Paint", "Hopper", 7, 0, QuickPracticeCourseKind::Race},
    {31, "Crock", "Hopper", 7, 1, QuickPracticeCourseKind::Circuit},
    {32, "Downer", "Hopper", 7, 2, QuickPracticeCourseKind::Stunt},
    {33, "East", "Hopper", 7, 3, QuickPracticeCourseKind::Race},
    {34, "Hairpin Hill", "Hopper", 7, 4, QuickPracticeCourseKind::Circuit},
    {35, "Vertical", "Sprinter", 8, 0, QuickPracticeCourseKind::Race},
    {36, "Flash", "Sprinter", 8, 1, QuickPracticeCourseKind::Circuit},
    {37, "Little Dipper", "Sprinter", 8, 2, QuickPracticeCourseKind::Stunt},
    {38, "Fruitbat", "Sprinter", 8, 3, QuickPracticeCourseKind::Race},
    {39, "123 Jump", "Sprinter", 8, 4, QuickPracticeCourseKind::Circuit},
    {40, "Griller", "Hunter", 9, 0, QuickPracticeCourseKind::Race},
    {41, "Two Loops", "Hunter", 9, 1, QuickPracticeCourseKind::Circuit},
    {42, "Neon", "Hunter", 9, 2, QuickPracticeCourseKind::Stunt},
    {43, "Hamster", "Hunter", 9, 3, QuickPracticeCourseKind::Race},
    {44, "To and Fro", "Hunter", 9, 4, QuickPracticeCourseKind::Circuit},
}};

constexpr const QuickPracticeCourse* quick_practice_course(
    std::uint8_t track_id
) noexcept {
    return track_id < kQuickPracticeCourses.size()
        ? &kQuickPracticeCourses[track_id]
        : nullptr;
}

constexpr std::string_view quick_practice_kind_label(
    QuickPracticeCourseKind kind
) noexcept {
    switch (kind) {
    case QuickPracticeCourseKind::Race: return "RACE";
    case QuickPracticeCourseKind::Circuit: return "CIRCUIT";
    case QuickPracticeCourseKind::Stunt: return "STUNT";
    }
    return {};
}

constexpr bool quick_practice_catalog_consistent() noexcept {
    for (std::size_t i = 0; i < kQuickPracticeCourses.size(); ++i) {
        const auto& course = kQuickPracticeCourses[i];
        if (course.track_id != i || course.tour_slot >= 5 ||
            course.tour_index < 1 || course.tour_index > 9) {
            return false;
        }
        const auto target = quick_practice_target_for_track(course.track_id);
        if (!target.valid || target.track_slot != course.tour_slot) {
            return false;
        }
    }
    return true;
}

static_assert(quick_practice_catalog_consistent());

}  // namespace ur::product

#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

enum class QuickPracticeMenuInput {
    None,
    Up,
    Down,
    Left,
    Right,
    Accept,
};

struct QuickPracticeTarget {
    std::uint8_t track_id = 0;
    std::uint8_t tour_option = 0;
    std::uint8_t track_slot = 0;
    bool valid = false;
};

constexpr std::array<std::uint8_t, 9> kQuickPracticeTourOptions{
    0, 1, 2, 3, 4, 5, 6, 7, 9,
};

constexpr QuickPracticeTarget quick_practice_target_for_track(
    std::uint8_t track_id
) noexcept {
    if (track_id >= 45) return {};
    const std::uint8_t block = static_cast<std::uint8_t>(track_id / 5);
    return {
        track_id,
        kQuickPracticeTourOptions[block],
        static_cast<std::uint8_t>(track_id % 5),
        true,
    };
}

constexpr int quick_practice_track_id_for_target(
    std::uint8_t tour_option,
    std::uint8_t track_slot
) noexcept {
    if (track_slot >= 5) return -1;
    for (std::size_t block = 0; block < kQuickPracticeTourOptions.size(); ++block) {
        if (kQuickPracticeTourOptions[block] == tour_option) {
            return static_cast<int>(block * 5 + track_slot);
        }
    }
    return -1;
}

// Match the recovered stock TOUR_SELECT cursor policy. The menu is a two-column
// grid encoded in 7E:009B. Hunter is option 9; option 8 is not a shipping tour.
constexpr QuickPracticeMenuInput quick_practice_tour_input(
    std::uint8_t target_tour_option,
    std::uint8_t selected_option
) noexcept {
    bool supported = false;
    for (const auto option : kQuickPracticeTourOptions) {
        if (option == target_tour_option) {
            supported = true;
            break;
        }
    }
    if (!supported) return QuickPracticeMenuInput::None;

    const std::uint8_t target_col =
        static_cast<std::uint8_t>(target_tour_option % 2);
    const std::uint8_t target_row =
        static_cast<std::uint8_t>(target_tour_option - target_col);

    if (target_row + 1 < selected_option) {
        return QuickPracticeMenuInput::Up;
    }
    if (target_row > selected_option) {
        return QuickPracticeMenuInput::Down;
    }
    if ((target_tour_option % 2) == 0 && (selected_option % 2) == 1) {
        return QuickPracticeMenuInput::Left;
    }
    if ((target_tour_option % 2) == 1 && (selected_option % 2) == 0) {
        return QuickPracticeMenuInput::Right;
    }
    return QuickPracticeMenuInput::Accept;
}

// TRACK_SELECT is a five-row list. The native acceptance probe binds the same
// 7E:009B selection byte to rows 0..4 and proves Down advances one row.
constexpr QuickPracticeMenuInput quick_practice_track_input(
    std::uint8_t target_slot,
    std::uint8_t selected_option
) noexcept {
    if (target_slot >= 5 || selected_option >= 5) {
        return QuickPracticeMenuInput::None;
    }
    if (selected_option < target_slot) return QuickPracticeMenuInput::Down;
    if (selected_option > target_slot) return QuickPracticeMenuInput::Up;
    return QuickPracticeMenuInput::Accept;
}

}  // namespace ur::product

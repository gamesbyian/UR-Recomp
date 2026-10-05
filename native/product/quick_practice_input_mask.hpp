#pragma once

#include "quick_practice_launch.hpp"

#include <cstdint>

namespace ur::product {

constexpr std::uint16_t quick_practice_runner_mask(
    QuickPracticeLaunchInput input
) noexcept {
    switch (input) {
    case QuickPracticeLaunchInput::Up: return 0x0010u;
    case QuickPracticeLaunchInput::Down: return 0x0020u;
    case QuickPracticeLaunchInput::Left: return 0x0040u;
    case QuickPracticeLaunchInput::Right: return 0x0080u;
    case QuickPracticeLaunchInput::Accept: return 0x0100u;
    case QuickPracticeLaunchInput::None: return 0x0000u;
    }
    return 0x0000u;
}

constexpr bool quick_practice_runner_mask_is_discrete_menu_input(
    std::uint16_t mask
) noexcept {
    return mask == 0x0010u || mask == 0x0020u || mask == 0x0040u ||
           mask == 0x0080u || mask == 0x0100u;
}

static_assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Up) == 0x0010u);
static_assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Down) == 0x0020u);
static_assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Left) == 0x0040u);
static_assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Right) == 0x0080u);
static_assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Accept) == 0x0100u);

}  // namespace ur::product

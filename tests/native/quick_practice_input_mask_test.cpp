#include "quick_practice_input_mask.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::None) == 0);
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Up) == 0x10);
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Down) == 0x20);
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Left) == 0x40);
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Right) == 0x80);
    assert(quick_practice_runner_mask(QuickPracticeLaunchInput::Accept) == 0x100);

    assert(quick_practice_runner_mask_is_discrete_menu_input(0x10));
    assert(quick_practice_runner_mask_is_discrete_menu_input(0x20));
    assert(quick_practice_runner_mask_is_discrete_menu_input(0x40));
    assert(quick_practice_runner_mask_is_discrete_menu_input(0x80));
    assert(quick_practice_runner_mask_is_discrete_menu_input(0x100));
    assert(!quick_practice_runner_mask_is_discrete_menu_input(0));
    assert(!quick_practice_runner_mask_is_discrete_menu_input(0x200));
    return 0;
}

#include "modern_host_navigation.h"
#include "modern_pause_navigation.h"

#include <array>
#include <cassert>

int main() {
    constexpr std::array<UrModernHostNavigationAction, 6> actions = {
        UR_MODERN_HOST_NAV_UP,
        UR_MODERN_HOST_NAV_DOWN,
        UR_MODERN_HOST_NAV_LEFT,
        UR_MODERN_HOST_NAV_RIGHT,
        UR_MODERN_HOST_NAV_CONFIRM,
        UR_MODERN_HOST_NAV_BACK,
    };
    for (std::size_t i = 0; i < actions.size(); ++i) {
        assert(static_cast<std::size_t>(actions[i]) == i);
    }

    assert(ur_modern_host_navigation_vertical_delta(UR_MODERN_HOST_NAV_UP) == -1);
    assert(ur_modern_host_navigation_vertical_delta(UR_MODERN_HOST_NAV_DOWN) == 1);
    assert(ur_modern_host_navigation_vertical_delta(UR_MODERN_HOST_NAV_LEFT) == 0);
    assert(ur_modern_host_navigation_vertical_delta(UR_MODERN_HOST_NAV_CONFIRM) == 0);

    assert(ur_modern_host_navigation_adjustment_delta(UR_MODERN_HOST_NAV_LEFT) == -1);
    assert(ur_modern_host_navigation_adjustment_delta(UR_MODERN_HOST_NAV_RIGHT) == 1);
    assert(ur_modern_host_navigation_adjustment_delta(UR_MODERN_HOST_NAV_UP) == 0);
    assert(ur_modern_host_navigation_adjustment_delta(UR_MODERN_HOST_NAV_BACK) == 0);

    assert(ur_modern_host_navigation_is_confirm(UR_MODERN_HOST_NAV_CONFIRM));
    assert(!ur_modern_host_navigation_is_confirm(UR_MODERN_HOST_NAV_BACK));
    assert(ur_modern_host_navigation_is_back(UR_MODERN_HOST_NAV_BACK));
    assert(!ur_modern_host_navigation_is_back(UR_MODERN_HOST_NAV_CONFIRM));

    UrModernPauseAction pause_action{};
    assert(ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_UP, &pause_action));
    assert(pause_action == UR_MODERN_PAUSE_PREVIOUS);
    assert(ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_DOWN, &pause_action));
    assert(pause_action == UR_MODERN_PAUSE_NEXT);
    assert(ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_CONFIRM, &pause_action));
    assert(pause_action == UR_MODERN_PAUSE_ACTIVATE);
    assert(ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_BACK, &pause_action));
    assert(pause_action == UR_MODERN_PAUSE_CANCEL);
    assert(!ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_LEFT, &pause_action));
    assert(!ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_RIGHT, &pause_action));
    assert(!ur_modern_pause_action_from_navigation(UR_MODERN_HOST_NAV_UP, nullptr));

    return 0;
}

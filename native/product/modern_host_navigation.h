#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Platform-independent host UI navigation vocabulary.
 *
 * Desktop/console adapters translate physical keyboard/gamepad events into
 * these actions before product UI code sees them. Guest controller state is
 * intentionally outside this contract.
 */
typedef enum UrModernHostNavigationAction {
    UR_MODERN_HOST_NAV_UP = 0,
    UR_MODERN_HOST_NAV_DOWN = 1,
    UR_MODERN_HOST_NAV_LEFT = 2,
    UR_MODERN_HOST_NAV_RIGHT = 3,
    UR_MODERN_HOST_NAV_CONFIRM = 4,
    UR_MODERN_HOST_NAV_BACK = 5,
} UrModernHostNavigationAction;

/* Product-facing direction helpers keep menu code independent of physical
 * bindings. A zero result means the action does not belong to that axis. */
static inline int ur_modern_host_navigation_vertical_delta(
    UrModernHostNavigationAction action) {
    return action == UR_MODERN_HOST_NAV_UP
        ? -1
        : (action == UR_MODERN_HOST_NAV_DOWN ? 1 : 0);
}

static inline int ur_modern_host_navigation_adjustment_delta(
    UrModernHostNavigationAction action) {
    return action == UR_MODERN_HOST_NAV_LEFT
        ? -1
        : (action == UR_MODERN_HOST_NAV_RIGHT ? 1 : 0);
}

static inline int ur_modern_host_navigation_is_confirm(
    UrModernHostNavigationAction action) {
    return action == UR_MODERN_HOST_NAV_CONFIRM;
}

static inline int ur_modern_host_navigation_is_back(
    UrModernHostNavigationAction action) {
    return action == UR_MODERN_HOST_NAV_BACK;
}

#ifdef __cplusplus
}
#endif

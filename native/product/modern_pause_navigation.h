#pragma once

#include "modern_host_navigation.h"
#include "modern_pause_input.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Translate platform-independent host navigation into the existing pause
 * command vocabulary. Horizontal adjustment is intentionally not a pause-root
 * command and therefore reports no mapping. */
static inline int ur_modern_pause_action_from_navigation(
    UrModernHostNavigationAction navigation,
    UrModernPauseAction* out_action) {
    if (!out_action) return 0;
    switch (navigation) {
    case UR_MODERN_HOST_NAV_UP:
        *out_action = UR_MODERN_PAUSE_PREVIOUS;
        return 1;
    case UR_MODERN_HOST_NAV_DOWN:
        *out_action = UR_MODERN_PAUSE_NEXT;
        return 1;
    case UR_MODERN_HOST_NAV_CONFIRM:
        *out_action = UR_MODERN_PAUSE_ACTIVATE;
        return 1;
    case UR_MODERN_HOST_NAV_BACK:
        *out_action = UR_MODERN_PAUSE_CANCEL;
        return 1;
    case UR_MODERN_HOST_NAV_LEFT:
    case UR_MODERN_HOST_NAV_RIGHT:
        return 0;
    }
    return 0;
}

#ifdef __cplusplus
}
#endif

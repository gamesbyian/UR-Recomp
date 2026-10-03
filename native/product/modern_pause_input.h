#pragma once

#include "modern_pause_menu.h"
#include "modern_session_c_api.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum UrModernPauseAction {
    UR_MODERN_PAUSE_TOGGLE = 0,
    UR_MODERN_PAUSE_PREVIOUS = 1,
    UR_MODERN_PAUSE_NEXT = 2,
    UR_MODERN_PAUSE_ACTIVATE = 3,
    UR_MODERN_PAUSE_CANCEL = 4,
    UR_MODERN_PAUSE_RESTART_HOTKEY = 5,
} UrModernPauseAction;

/* Platform-independent pause-menu input policy.
 *
 * Keyboard/gamepad/platform layers translate their native events into these
 * semantic actions. Navigation mutates only UrModernPauseMenu. Session effects
 * still travel through the accepted modern session C API.
 */
UrModernSessionResult ur_modern_pause_handle_action(
    UrModernSession* session,
    UrModernPauseMenu* menu,
    UrModernPauseAction action);

#ifdef __cplusplus
}
#endif

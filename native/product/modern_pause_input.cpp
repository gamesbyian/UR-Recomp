#include "modern_pause_input.h"

extern "C" UrModernSessionResult ur_modern_pause_handle_action(
    UrModernSession* session,
    UrModernPauseMenu* menu,
    UrModernPauseAction action) {
    if (!session || !menu) {
        return UR_MODERN_SESSION_REJECTED_BY_RUNTIME;
    }

    const int paused = ur_modern_session_is_paused(session);
    const int restart = ur_modern_session_restart_available(session);

    switch (action) {
    case UR_MODERN_PAUSE_TOGGLE: {
        const UrModernSessionResult result =
            ur_modern_session_handle_key(
                session, UR_MODERN_SESSION_KEY_ESCAPE);
        if (ur_modern_session_is_paused(session)) {
            ur_modern_pause_menu_reset(menu);
        }
        return result;
    }

    case UR_MODERN_PAUSE_PREVIOUS:
        if (!paused) {
            return UR_MODERN_SESSION_NO_OP;
        }
        ur_modern_pause_menu_move(menu, -1, restart);
        return UR_MODERN_SESSION_APPLIED;

    case UR_MODERN_PAUSE_NEXT:
        if (!paused) {
            return UR_MODERN_SESSION_NO_OP;
        }
        ur_modern_pause_menu_move(menu, 1, restart);
        return UR_MODERN_SESSION_APPLIED;

    case UR_MODERN_PAUSE_ACTIVATE: {
        if (!paused) {
            return UR_MODERN_SESSION_NO_OP;
        }
        const UrModernPauseItem selected =
            ur_modern_pause_menu_selected(menu, restart);
        if (selected == UR_MODERN_PAUSE_RESTART) {
            return ur_modern_session_handle_key(
                session, UR_MODERN_SESSION_KEY_RESTART);
        }
        if (selected == UR_MODERN_PAUSE_FOCUS_PAUSE ||
            selected == UR_MODERN_PAUSE_CONTROLS ||
            selected == UR_MODERN_PAUSE_RUN_DATA ||
            selected == UR_MODERN_PAUSE_QUIT) {
            return UR_MODERN_SESSION_NO_OP;
        }
        return ur_modern_session_handle_key(
            session, UR_MODERN_SESSION_KEY_ACCEPT);
    }

    case UR_MODERN_PAUSE_CANCEL:
        return paused
            ? ur_modern_session_handle_key(
                  session, UR_MODERN_SESSION_KEY_ACCEPT)
            : UR_MODERN_SESSION_NO_OP;

    case UR_MODERN_PAUSE_RESTART_HOTKEY:
        return ur_modern_session_handle_key(
            session, UR_MODERN_SESSION_KEY_RESTART);
    }

    return UR_MODERN_SESSION_UNSUPPORTED;
}

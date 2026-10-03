#include "modern_pause_menu.h"

namespace {

UrModernPauseItem normalized_selection(
    const UrModernPauseMenu* menu,
    int restart_available) {
    if (!menu) {
        return UR_MODERN_PAUSE_RESUME;
    }
    switch (menu->selected) {
    case UR_MODERN_PAUSE_RESUME:
        return UR_MODERN_PAUSE_RESUME;
    case UR_MODERN_PAUSE_RESTART:
        return restart_available
            ? UR_MODERN_PAUSE_RESTART
            : UR_MODERN_PAUSE_RESUME;
    case UR_MODERN_PAUSE_FOCUS_PAUSE:
        return UR_MODERN_PAUSE_FOCUS_PAUSE;
    default:
        return UR_MODERN_PAUSE_RESUME;
    }
}

}  // namespace

extern "C" void ur_modern_pause_menu_reset(UrModernPauseMenu* menu) {
    if (menu) menu->selected = UR_MODERN_PAUSE_RESUME;
}

extern "C" void ur_modern_pause_menu_move(
    UrModernPauseMenu* menu,
    int delta,
    int restart_available) {
    if (!menu) return;

    UrModernPauseItem current =
        normalized_selection(menu, restart_available);
    menu->selected = current;
    if (delta == 0) return;

    if (restart_available) {
        if (delta > 0) {
            switch (current) {
            case UR_MODERN_PAUSE_RESUME:
                menu->selected = UR_MODERN_PAUSE_RESTART;
                break;
            case UR_MODERN_PAUSE_RESTART:
                menu->selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
                break;
            case UR_MODERN_PAUSE_FOCUS_PAUSE:
                menu->selected = UR_MODERN_PAUSE_RESUME;
                break;
            }
        } else {
            switch (current) {
            case UR_MODERN_PAUSE_RESUME:
                menu->selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
                break;
            case UR_MODERN_PAUSE_RESTART:
                menu->selected = UR_MODERN_PAUSE_RESUME;
                break;
            case UR_MODERN_PAUSE_FOCUS_PAUSE:
                menu->selected = UR_MODERN_PAUSE_RESTART;
                break;
            }
        }
        return;
    }

    menu->selected =
        current == UR_MODERN_PAUSE_FOCUS_PAUSE
            ? UR_MODERN_PAUSE_RESUME
            : UR_MODERN_PAUSE_FOCUS_PAUSE;
}

extern "C" UrModernPauseItem ur_modern_pause_menu_selected(
    const UrModernPauseMenu* menu,
    int restart_available) {
    return normalized_selection(menu, restart_available);
}

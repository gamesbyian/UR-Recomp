#include "modern_pause_menu.h"

extern "C" void ur_modern_pause_menu_reset(UrModernPauseMenu* menu) {
    if (menu) menu->selected = 0;
}

extern "C" void ur_modern_pause_menu_move(
    UrModernPauseMenu* menu,
    int delta,
    int restart_available) {
    if (!menu) return;
    if (!restart_available) {
        menu->selected = 0;
        return;
    }
    if (delta != 0) {
        menu->selected = menu->selected == 0 ? 1 : 0;
    }
}

extern "C" UrModernPauseItem ur_modern_pause_menu_selected(
    const UrModernPauseMenu* menu,
    int restart_available) {
    if (!menu || !restart_available || menu->selected == 0)
        return UR_MODERN_PAUSE_RESUME;
    return UR_MODERN_PAUSE_RESTART;
}

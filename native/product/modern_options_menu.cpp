#include "modern_options_menu.h"

extern "C" void ur_modern_options_menu_reset(UrModernOptionsMenu* menu) {
    if (menu) menu->selected = UR_MODERN_OPTIONS_FOCUS_PAUSE;
}

extern "C" void ur_modern_options_menu_move(
    UrModernOptionsMenu* menu,
    int delta) {
    if (!menu || delta == 0) return;
    const int count = 4;
    int selected = menu->selected;
    if (selected < 0 || selected >= count) selected = 0;
    selected = (selected + (delta > 0 ? 1 : -1) + count) % count;
    menu->selected = selected;
}

extern "C" UrModernOptionsItem ur_modern_options_menu_selected(
    const UrModernOptionsMenu* menu) {
    if (!menu) {
        return UR_MODERN_OPTIONS_FOCUS_PAUSE;
    }
    switch (menu->selected) {
    case UR_MODERN_OPTIONS_DISPLAY_MODE:
        return UR_MODERN_OPTIONS_DISPLAY_MODE;
    case UR_MODERN_OPTIONS_VSYNC:
        return UR_MODERN_OPTIONS_VSYNC;
    case UR_MODERN_OPTIONS_PRESENTATION_FPS:
        return UR_MODERN_OPTIONS_PRESENTATION_FPS;
    default:
        return UR_MODERN_OPTIONS_FOCUS_PAUSE;
    }
}

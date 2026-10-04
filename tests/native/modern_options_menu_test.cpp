#include "modern_options_menu.h"

#include <cassert>

int main() {
    UrModernOptionsMenu menu{};
    ur_modern_options_menu_reset(&menu);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_FOCUS_PAUSE);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_DISPLAY_MODE);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_VSYNC);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_PRESENTATION_FPS);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_OUTPUT_RESOLUTION);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_WIDESCREEN);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_GHOST);

    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_FOCUS_PAUSE);

    ur_modern_options_menu_move(&menu, -1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_GHOST);

    menu.selected = 99;
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_FOCUS_PAUSE);
    ur_modern_options_menu_move(&menu, 1);
    assert(ur_modern_options_menu_selected(&menu) ==
           UR_MODERN_OPTIONS_DISPLAY_MODE);

    return 0;
}

#include "modern_pause_menu.h"

#include <cassert>

int main() {
    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    // Without Restart the menu is Resume <-> Focus Pause.
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RESUME);
    ur_modern_pause_menu_move(&menu, -1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_reset(&menu);

    // With Restart the menu is Resume -> Restart -> Focus Pause -> Resume.
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);

    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    // Losing Restart availability clamps a Restart selection to Resume.
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(menu.selected == UR_MODERN_PAUSE_RESUME);

    // Focus Pause remains a valid selection if Restart disappears.
    menu.selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);

    return 0;
}

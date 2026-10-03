#include "modern_pause_menu.h"

#include <cassert>

int main() {
    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    // Without Restart:
    // Resume -> Focus Pause -> Controls -> Run Data -> Resume.
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RESUME);
    ur_modern_pause_menu_move(&menu, -1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_reset(&menu);

    // With Restart:
    // Resume -> Restart -> Focus Pause -> Controls -> Run Data -> Resume.
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    // Losing Restart availability clamps Restart to Resume.
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(menu.selected == UR_MODERN_PAUSE_RESUME);

    // Host-owned rows remain valid if Restart disappears.
    menu.selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    menu.selected = UR_MODERN_PAUSE_CONTROLS;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_CONTROLS);
    menu.selected = UR_MODERN_PAUSE_RUN_DATA;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RUN_DATA);

    return 0;
}

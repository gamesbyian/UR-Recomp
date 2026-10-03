#include "modern_pause_menu.h"

#include <cassert>

int main() {
    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    // Without Restart:
    // Resume -> Options -> Controls -> Run Data -> Quit -> Resume.
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_OPTIONS);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_QUIT);
    ur_modern_pause_menu_move(&menu, 1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RESUME);
    ur_modern_pause_menu_move(&menu, -1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_QUIT);
    ur_modern_pause_menu_reset(&menu);

    // With Restart:
    // Resume -> Restart -> Options -> Controls -> Run Data -> Quit -> Resume.
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_OPTIONS);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_QUIT);
    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_QUIT);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RUN_DATA);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_CONTROLS);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_OPTIONS);
    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    // Losing Restart availability clamps Restart to Resume.
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(menu.selected == UR_MODERN_PAUSE_RESUME);

    // Host-owned rows remain valid if Restart disappears.
    menu.selected = UR_MODERN_PAUSE_OPTIONS;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_OPTIONS);
    menu.selected = UR_MODERN_PAUSE_CONTROLS;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_CONTROLS);
    menu.selected = UR_MODERN_PAUSE_RUN_DATA;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RUN_DATA);
    menu.selected = UR_MODERN_PAUSE_QUIT;
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_QUIT);

    // A stale direct Focus Pause selection normalizes into Options.
    menu.selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_OPTIONS);

    return 0;
}

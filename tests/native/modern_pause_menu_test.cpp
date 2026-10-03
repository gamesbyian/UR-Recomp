#include "modern_pause_menu.h"

#include <cassert>

int main() {
    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    ur_modern_pause_menu_move(&menu, -1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESUME);

    ur_modern_pause_menu_move(&menu, 1, 1);
    assert(ur_modern_pause_menu_selected(&menu, 1) == UR_MODERN_PAUSE_RESTART);

    // Losing restart availability clamps the selection back to Resume.
    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);
    assert(menu.selected == 0);

    return 0;
}

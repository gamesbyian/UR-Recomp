#include "modern_pause_menu.h"

#include <cassert>
#include <initializer_list>

int main() {
    static_assert(UR_MODERN_PAUSE_RESUME == 0);
    static_assert(UR_MODERN_PAUSE_RESTART == 1);
    static_assert(UR_MODERN_PAUSE_RUN_DATA == 4);
    static_assert(UR_MODERN_PAUSE_QUIT == 5);
    static_assert(UR_MODERN_PAUSE_OPTIONS == 6);
    static_assert(UR_MODERN_PAUSE_EXIT_FRONTEND == 7);
    static_assert(UR_MODERN_PAUSE_RECORDS == 8);

    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);

    const UrModernPauseItem without_restart[] = {
        UR_MODERN_PAUSE_OPTIONS,
        UR_MODERN_PAUSE_CONTROLS,
        UR_MODERN_PAUSE_RUN_DATA,
        UR_MODERN_PAUSE_RECORDS,
        UR_MODERN_PAUSE_EXIT_FRONTEND,
        UR_MODERN_PAUSE_QUIT,
        UR_MODERN_PAUSE_RESUME,
    };
    for (const auto expected : without_restart) {
        ur_modern_pause_menu_move(&menu, 1, 0);
        assert(ur_modern_pause_menu_selected(&menu, 0) == expected);
    }
    ur_modern_pause_menu_move(&menu, -1, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_QUIT);

    ur_modern_pause_menu_reset(&menu);
    const UrModernPauseItem with_restart[] = {
        UR_MODERN_PAUSE_RESTART,
        UR_MODERN_PAUSE_OPTIONS,
        UR_MODERN_PAUSE_CONTROLS,
        UR_MODERN_PAUSE_RUN_DATA,
        UR_MODERN_PAUSE_RECORDS,
        UR_MODERN_PAUSE_EXIT_FRONTEND,
        UR_MODERN_PAUSE_QUIT,
        UR_MODERN_PAUSE_RESUME,
    };
    for (const auto expected : with_restart) {
        ur_modern_pause_menu_move(&menu, 1, 1);
        assert(ur_modern_pause_menu_selected(&menu, 1) == expected);
    }

    const UrModernPauseItem reverse[] = {
        UR_MODERN_PAUSE_QUIT,
        UR_MODERN_PAUSE_EXIT_FRONTEND,
        UR_MODERN_PAUSE_RECORDS,
        UR_MODERN_PAUSE_RUN_DATA,
        UR_MODERN_PAUSE_CONTROLS,
        UR_MODERN_PAUSE_OPTIONS,
        UR_MODERN_PAUSE_RESTART,
    };
    for (const auto expected : reverse) {
        ur_modern_pause_menu_move(&menu, -1, 1);
        assert(ur_modern_pause_menu_selected(&menu, 1) == expected);
    }

    ur_modern_pause_menu_move(&menu, 0, 0);
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_RESUME);

    for (const auto item : {
             UR_MODERN_PAUSE_OPTIONS,
             UR_MODERN_PAUSE_CONTROLS,
             UR_MODERN_PAUSE_RUN_DATA,
             UR_MODERN_PAUSE_RECORDS,
             UR_MODERN_PAUSE_EXIT_FRONTEND,
             UR_MODERN_PAUSE_QUIT,
         }) {
        menu.selected = item;
        ur_modern_pause_menu_move(&menu, 0, 0);
        assert(ur_modern_pause_menu_selected(&menu, 0) == item);
    }

    menu.selected = UR_MODERN_PAUSE_FOCUS_PAUSE;
    assert(ur_modern_pause_menu_selected(&menu, 0) == UR_MODERN_PAUSE_OPTIONS);
    return 0;
}

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef enum UrModernPauseItem {
    UR_MODERN_PAUSE_RESUME = 0,
    UR_MODERN_PAUSE_RESTART = 1,
    UR_MODERN_PAUSE_FOCUS_PAUSE = 2,
} UrModernPauseItem;

typedef struct UrModernPauseMenu {
    int selected;
} UrModernPauseMenu;

void ur_modern_pause_menu_reset(UrModernPauseMenu* menu);
void ur_modern_pause_menu_move(
    UrModernPauseMenu* menu,
    int delta,
    int restart_available);
UrModernPauseItem ur_modern_pause_menu_selected(
    const UrModernPauseMenu* menu,
    int restart_available);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef enum UrModernOptionsItem {
    UR_MODERN_OPTIONS_FOCUS_PAUSE = 0,
    UR_MODERN_OPTIONS_DISPLAY_MODE = 1,
} UrModernOptionsItem;

typedef struct UrModernOptionsMenu {
    int selected;
} UrModernOptionsMenu;

void ur_modern_options_menu_reset(UrModernOptionsMenu* menu);
void ur_modern_options_menu_move(UrModernOptionsMenu* menu, int delta);
UrModernOptionsItem ur_modern_options_menu_selected(
    const UrModernOptionsMenu* menu);

#ifdef __cplusplus
}
#endif

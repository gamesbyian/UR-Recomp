#pragma once

// The Modern session owns gameplay lifecycle and pause navigation; this
// existing host painter merely composes a native pause panel onto Baldosa's
// LAST frozen source raster. It must never step guest simulation or allocate
// an independent window/render loop.
#include "modern_pause_menu.h"
#include "modern_root_overlay_presenter.hpp"

#include <algorithm>
#include <cstdint>

namespace ur::product {

inline bool render_native_modern_pause_overlay(
    const ModernRootOverlayPainter& paint, std::uint32_t* pixels,
    int stride, int width, int height, const UrModernPauseMenu& menu,
    bool restart_available) {
    if (!paint.valid() || !pixels || width < 400 || stride < width ||
        height < 424)
        return false;
    const int panel_w = std::min(400, width - 24);
    const int panel_h = std::min(400, height - 24);
    const int x = (width - panel_w) / 2;
    const int y = (height - panel_h) / 2;
    const auto& pal = kModernStockMenuPalette;
    paint.fill_rect(pixels, stride, height, x, y, panel_w, panel_h,
                    pal.background);
    paint.fill_rect(pixels, stride, height, x, y, panel_w, 57,
                    pal.header_band);
    paint.stroke_rect(pixels, stride, height, x, y, panel_w, panel_h,
                      pal.frame_grey);
    paint.draw_text(pixels, stride, height, x + 18, y + 13,
                    "UNIRACERS", pal.title_yellow, 2);
    paint.draw_text(pixels, stride, height, x + 18, y + 41,
                    "PAUSED - GUEST FROZEN", pal.secondary_grey, 1);
    struct Row {
        UrModernPauseItem item;
        const char* label;
        bool wired;
    };
    // Keep existing Modern ordering. Baldosa's SDL shutdown now owns Quit;
    // unconnected Records, Options and Exit remain explicitly disabled.
    constexpr Row rows[] = {
        {UR_MODERN_PAUSE_RESUME, "RESUME", true},
        {UR_MODERN_PAUSE_RESTART, "RESTART RACE", true},
        {UR_MODERN_PAUSE_OPTIONS, "OPTIONS", false},
        {UR_MODERN_PAUSE_CONTROLS, "CONTROLS", false},
        {UR_MODERN_PAUSE_RUN_DATA, "RUN DATA", false},
        {UR_MODERN_PAUSE_RECORDS, "RECORDS", false},
        {UR_MODERN_PAUSE_EXIT_FRONTEND, "EXIT TO FRONTEND", false},
        {UR_MODERN_PAUSE_QUIT, "QUIT DESKTOP", true},
    };
    const auto selected = ur_modern_pause_menu_selected(
        &menu, restart_available ? 1 : 0);
    const int first_y = y + 71;
    for (int i = 0; i < 8; ++i) {
        const auto& row = rows[i];
        const bool enabled = row.wired &&
            (row.item != UR_MODERN_PAUSE_RESTART || restart_available);
        const bool active = selected == row.item;
        const int ry = first_y + i * 33;
        if (active) {
            paint.fill_rect(pixels, stride, height,
                x + 12, ry - 4, panel_w - 24, 29, pal.cursor_blue);
        }
        paint.draw_text(pixels, stride, height, x + 21, ry,
            row.label,
            !enabled ? pal.secondary_grey :
            active ? pal.shadow_black : 0xFFFFFFFFu, 2);
        if (!enabled)
            paint.draw_text(pixels, stride, height,
                x + panel_w - 88, ry + 7, "SOON",
                active ? pal.shadow_black : pal.secondary_grey, 1);
    }
    paint.draw_text(pixels, stride, height, x + 16, y + panel_h - 31,
                    "UP/DOWN CHOOSE  A/ENTER SELECT", 0xFFFFFFFFu, 1);
    paint.draw_text(pixels, stride, height, x + 16, y + panel_h - 17,
                    "B/ESC RESUME  START RESUME", pal.cursor_blue, 1);
    return true;
}

}  // namespace ur::product

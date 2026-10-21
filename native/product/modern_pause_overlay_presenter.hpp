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
    // The frozen source may be the real 256x224 (original gameplay) or
    // 342x224 (prepared wide) guest raster. Neither can accept the legacy
    // 400x400 panel. Never step the guest or invent a larger surface.
    if (!paint.valid() || !pixels || width < 256 || stride < width ||
        height < 224)
        return false;
    struct Row {
        UrModernPauseItem item;
        const char* label;
        bool wired;
    };
    // Preserve the same product-owned ordering and disabled functionality
    // in both genuine small-source and legacy enlarged pause renderers.
    constexpr Row rows[] = {
        {UR_MODERN_PAUSE_RESUME, "RESUME", true},
        {UR_MODERN_PAUSE_RESTART, "RESTART RACE", true},
        {UR_MODERN_PAUSE_OPTIONS, "OPTIONS", true},
        {UR_MODERN_PAUSE_CONTROLS, "CONTROLS", false},
        {UR_MODERN_PAUSE_RUN_DATA, "RUN DATA", false},
        {UR_MODERN_PAUSE_RECORDS, "RECORDS", false},
        {UR_MODERN_PAUSE_EXIT_FRONTEND, "EXIT TO FRONTEND", false},
        {UR_MODERN_PAUSE_QUIT, "QUIT DESKTOP", true},
    };
    const auto selected = ur_modern_pause_menu_selected(
        &menu, restart_available ? 1 : 0);
    const auto& pal = kModernStockMenuPalette;
    if (width < 400 || height < 424) {
        const int panel_w = width >= 342 ? 320 : 240;
        constexpr int panel_h = 204;
        const int x = (width - panel_w) / 2;
        const int y = (height - panel_h) / 2;
        paint.fill_rect(pixels, stride, height, x, y, panel_w, panel_h,
                        pal.background);
        paint.fill_rect(pixels, stride, height, x, y, panel_w, 39,
                        pal.header_band);
        paint.stroke_rect(pixels, stride, height, x, y, panel_w, panel_h,
                          pal.frame_grey);
        paint.draw_text(pixels, stride, height, x + 9, y + 5,
                        "UNIRACERS", pal.title_yellow, 2);
        paint.draw_text(pixels, stride, height, x + 9, y + 27,
                        "GAME PAUSED", kModernMenuCheckerLegibleGrey, 1);
        for (int i = 0; i < 8; ++i) {
            const auto& row = rows[i];
            const bool enabled = row.wired &&
                (row.item != UR_MODERN_PAUSE_RESTART || restart_available);
            const bool active = selected == row.item;
            const int ry = y + 48 + i * 17;
            if (active)
                paint.fill_rect(pixels, stride, height, x + 6, ry - 2,
                                panel_w - 12, 15, pal.cursor_blue);
            paint.draw_text(pixels, stride, height, x + 10, ry,
                            row.label,
                            // A focused row sits on the light focus bar;
                            // dim grey there is ~1.8:1, so focus text wins
                            // and "SOON" still marks it as unavailable.
                            active ? pal.shadow_black :
                            !enabled ? pal.secondary_grey : 0xFFFFFFFFu, 1);
            if (!enabled)
                paint.draw_text(pixels, stride, height,
                                x + panel_w - 45, ry, "SOON",
                                active ? pal.shadow_black
                                       : pal.secondary_grey, 1);
        }
        paint.draw_text(pixels, stride, height, x + 8, y + 183,
                        "UP/DOWN  A SELECT", 0xFFFFFFFFu, 1);
        paint.draw_text(pixels, stride, height, x + 8, y + 193,
                        "B/ESC BACK  START RESUME", pal.cursor_blue, 1);
        return true;
    }
    // The existing 512x448 and larger renderer remains pixel-identical.
    const int panel_w = std::min(400, width - 24);
    const int panel_h = std::min(400, height - 24);
    const int x = (width - panel_w) / 2;
    const int y = (height - panel_h) / 2;
    paint.fill_rect(pixels, stride, height, x, y, panel_w, panel_h,
                    pal.background);
    paint.fill_rect(pixels, stride, height, x, y, panel_w, 57,
                    pal.header_band);
    paint.stroke_rect(pixels, stride, height, x, y, panel_w, panel_h,
                      pal.frame_grey);
    paint.draw_text(pixels, stride, height, x + 18, y + 13,
                    "UNIRACERS", pal.title_yellow, 2);
    paint.draw_text(pixels, stride, height, x + 18, y + 41,
                    "GAME PAUSED", kModernMenuCheckerLegibleGrey, 1);

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
            active ? pal.shadow_black :
            !enabled ? pal.secondary_grey : 0xFFFFFFFFu, 2);
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


// The native Options panel while the guest is frozen: the same shared modal
// as the root, centred in a root-style frame on the paused raster.
inline bool render_native_modern_pause_options(
    const ModernRootOverlayPainter& paint, std::uint32_t* pixels,
    int stride, int width, int height, const ModernRootOverlayView& view) {
    if (!paint.valid() || !pixels || width < 256 || stride < width ||
        height < 224 || !view.options_open)
        return false;
    // Share the real source-width contract with the native destination
    // renderer: compact 256 -> 240, prepared wide 342 -> 320 logical px.
    // 2x and 4x fallback rasters keep their original pixel aspect/scale.
    const int scale = width >= 1024 && height >= 896 ? 4 :
                      width >= 512 && height >= 448 ? 2 : 1;
    // Do not infer a widened *source* from an arbitrary large SDL window.
    // Only the exact prepared 342x224 source family opts into wide layout;
    // 1024x768 and 1280x720 output-sized 4:3/16:9 buffers keep legacy
    // compact framing unless the native source actually has that geometry.
    const bool prepared_wide =
        width == 342 * scale && height == 224 * scale;
    const int panel_w = prepared_wide ? 320 : 240;
    constexpr int kPanelH = 204;
    const int x = (width - panel_w * scale) / 2;
    const int y = (height - kPanelH * scale) / 2;
    if (x < 0 || y < 0 ||
        panel_w * scale > width - x ||
        kPanelH * scale > height - y)
        return false;
    const auto& pal = kModernStockMenuPalette;
    paint.fill_rect(pixels, stride, height, x, y, panel_w * scale,
                    kPanelH * scale, pal.background);
    paint.fill_rect(pixels, stride, height, x, y, panel_w * scale,
                    27 * scale, pal.header_band);
    paint.stroke_rect(pixels, stride, height, x, y, panel_w * scale,
                      kPanelH * scale, pal.frame_grey);
    paint.draw_text(pixels, stride, height, x + 9 * scale, y + 6 * scale,
                    "UNIRACERS", pal.title_yellow, 2 * scale);
    paint.draw_text(pixels, stride, height, x + 8 * scale, y + 36 * scale,
                    "GAME PAUSED", kModernMenuCheckerLegibleGrey, scale);
    render_modern_options_modal(paint, pixels, stride, height, scale,
                                panel_w, x, y, view);
    return true;
}

}  // namespace ur::product

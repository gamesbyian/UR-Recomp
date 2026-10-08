#pragma once

#include "modern_stock_menu_palette.hpp"

namespace ur::product {

// Pure presentation-only layout for the read-only Tour Progress panel.
// Ordinary 4:3 keeps the existing 240px width. Widescreen allows a wider
// column for real tour names and medal labels without stretching glyphs.
struct ModernTourOverviewVisualStyle {
    int panel_width_logical = 0;
    int title_glyph_scale = 1;
    int title_x_logical = 8;
    int title_y_logical = 7;
    int header_height_logical = 27;
    ModernStockMenuPalette palette{};
};

constexpr ModernTourOverviewVisualStyle modern_tour_overview_visual_style(
    int logical_view_width) noexcept {
    ModernTourOverviewVisualStyle style{};
    if (logical_view_width <= 32) return style;

    style.panel_width_logical =
        logical_view_width < 268 ? logical_view_width - 16
        : logical_view_width < 320 ? 260
        : logical_view_width - 24 < 324 ? logical_view_width - 24
        : 324;

    // "TOUR PROGRESS" is 13 characters. Stock-style large type is a
    // 16 logical-pixel cell; fall back on narrow host layouts.
    constexpr int kTitleCharacters = 13;
    if (style.panel_width_logical >= 16 + kTitleCharacters * 16)
        style.title_glyph_scale = 2;
    return style;
}

}  // namespace ur::product

#pragma once

#include <cstdint>

#include "modern_stock_menu_palette.hpp"

namespace ur::product {

// Host-only design tokens for the first Uniracers-derived Quick Practice
// hierarchy. Title yellow, small-copy grey and cursor blue are measured from
// analysis/generated/menu-visual-language.json, not a new guest UI palette.
// Rendering remains in the existing modern system overlay.
struct ModernPracticeVisualStyle {
    int panel_width_logical = 0;
    int title_glyph_scale = 1;
    int title_x_logical = 8;
    int title_y_logical = 6;
    int selected_row_y_logical = 62;
    int selected_row_height_logical = 17;

    std::uint32_t title_yellow = kModernStockMenuPalette.title_yellow;
    std::uint32_t secondary_grey = kModernStockMenuPalette.secondary_grey;
    std::uint32_t cursor_blue = kModernStockMenuPalette.cursor_blue;
    std::uint32_t dark_outline = kModernStockMenuPalette.shadow_black;
    std::uint32_t selection_band = 0xA0303858u;
    std::uint32_t panel_fill = kModernStockMenuPalette.background;
    std::uint32_t panel_outline = kModernStockMenuPalette.frame_grey;
};

// Preserve the current 240-pixel 4:3 footprint, but spend the extra width
// on longer course names in a wide field rather than stretching the text.
constexpr ModernPracticeVisualStyle modern_practice_visual_style(
    int logical_view_width) noexcept {
    ModernPracticeVisualStyle result{};
    if (logical_view_width <= 32) return result;
    result.panel_width_logical =
        logical_view_width < 284 ? logical_view_width - 16
        : logical_view_width < 320 ? 276
        : logical_view_width - 24 < 324 ? logical_view_width - 24
        : 324;

    // The 14-character stock-style title uses a 16px high/16px wide
    // hierarchy only when it fits with the existing 8px safe margins.
    constexpr int title_characters = 14;
    if (result.panel_width_logical >= 16 + title_characters * 16)
        result.title_glyph_scale = 2;
    return result;
}

}  // namespace ur::product

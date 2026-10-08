#pragma once

#include "modern_stock_menu_palette.hpp"

namespace ur::product {

// Presentation-only treatment of the Modern onboarding/Help screen.
// The stock BG2 menu grammar (yellow large title, grey small detail and
// blue navigation accents) supplies roles; no guest UI or input is changed.
struct ModernOnboardingVisualStyle {
    int panel_width_logical = 0;
    int panel_height_logical = 206;
    int title_x_logical = 8;
    int title_y_logical = 5;
    int title_glyph_scale = 1;
    int subtitle_y_logical = 27;
    int header_height_logical = 24;
    ModernStockMenuPalette palette{};
};

// At authentic 256px logical width the modal remains the existing 240px
// panel. Widened Modern fields can use 324px of meaningful help-column space,
// never stretched glyphs. The 11-letter "HOW TO RIDE" headline uses the stock
// 16px title pitch only when it fits the logical safe margins.
constexpr ModernOnboardingVisualStyle modern_onboarding_visual_style(
    int logical_view_width) noexcept {
    ModernOnboardingVisualStyle style{};
    if (logical_view_width <= 32) return style;
    style.panel_width_logical =
        logical_view_width < 340 ? logical_view_width - 16 : 324;
    constexpr int kTitleCharacters = 11;
    if (style.panel_width_logical >= 16 + kTitleCharacters * 16)
        style.title_glyph_scale = 2;
    return style;
}

}  // namespace ur::product

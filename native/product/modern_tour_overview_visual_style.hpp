#pragma once

#include "modern_stock_menu_palette.hpp"
#include "modern_overlay_text_fit.hpp"

#include <cstddef>
#include <string>
#include <string_view>

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

// Noninteractive medal columns have one right-aligned status baseline.
// Fit long tour names FIRST, keeping BRONZE/SILVER/GOLD/NOT STARTED intact.
// Locked rows never inspect a source name or medal status.
inline std::string modern_tour_overview_row(
    unsigned slot_one_based,
    bool visible,
    std::string_view name,
    std::string_view medal,
    std::size_t cells) {
    if (slot_one_based < 1 || slot_one_based > 8 || cells == 0)
        return {};
    const std::string prefix = std::to_string(slot_one_based) + ". ";
    if (!visible)
        return fit_modern_overlay_text(prefix + "LOCKED TOUR", cells);
    if (cells <= prefix.size() + medal.size() + 1u)
        return fit_modern_overlay_text(prefix + std::string(medal), cells);

    const std::size_t name_space =
        cells - prefix.size() - medal.size() - 1u;
    std::string row = prefix;
    row.append(name.substr(0, name_space));
    row.append(cells - medal.size() - row.size(), ' ');
    row.append(medal);
    return row;
}

}  // namespace ur::product

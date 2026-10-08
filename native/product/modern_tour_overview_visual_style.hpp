#pragma once

#include "modern_overlay_text_fit.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace ur::product {

// Stock-derived host presentation only. Colours use the decoded BG2 menu
// roles in analysis/generated/menu-visual-language.json. These tokens do not
// substitute the cartridge font or create gameplay/progression authority.
struct ModernTourOverviewVisualStyle {
    int panel_width_logical = 0;
    int title_glyph_scale = 1;
    int title_y_logical = 6;
    int first_tour_y_logical = 51;
    int row_spacing_logical = 16;

    std::uint32_t title_yellow = 0xFFF8F800u;
    std::uint32_t secondary_grey = 0xFF989898u;
    std::uint32_t panel_fill = 0xE02F2F2Fu;
    std::uint32_t panel_outline = 0xFF989898u;
    std::uint32_t dark_outline = 0xFF000000u;
};

constexpr ModernTourOverviewVisualStyle modern_tour_overview_visual_style(
    int logical_view_width) noexcept {
    ModernTourOverviewVisualStyle style{};
    if (logical_view_width <= 32) return style;
    // At 256 logical px retain the original 240px overlay footprint. A
    // widened viewport can provide 324px for separated names/medal states.
    style.panel_width_logical =
        logical_view_width < 284 ? logical_view_width - 16
        : logical_view_width < 320 ? 276
        : logical_view_width - 24 < 324 ? logical_view_width - 24
        : 324;
    // "TOUR PROGRESS" has 13 monospaced host cells. Only use the original
    // 16px menu-title pitch when the full title plus margins will fit.
    constexpr int kTitleCells = 13;
    if (style.panel_width_logical >= 16 + kTitleCells * 16)
        style.title_glyph_scale = 2;
    return style;
}

// Format a single stock-derived tour slot without ever using a hidden name.
// Put available medal status at the right edge so unequal label lengths do
// not make the eight-row hierarchy look ragged; truncate names first.
inline std::string modern_tour_overview_visual_row(
    unsigned slot_one_based,
    bool visible,
    std::string_view tour_name,
    std::string_view medal,
    std::size_t cells) {
    if (slot_one_based < 1 || slot_one_based > 8 || cells == 0) return {};
    const std::string prefix = std::to_string(slot_one_based) + ". ";
    if (!visible) {
        return fit_modern_overlay_text(prefix + "LOCKED TOUR", cells);
    }
    if (cells <= prefix.size() + medal.size() + 1u) {
        return fit_modern_overlay_text(prefix + std::string(medal), cells);
    }

    const std::size_t name_cells =
        cells - prefix.size() - medal.size() - 1u;
    std::string row = prefix;
    row.append(tour_name.substr(0, name_cells));
    row.append(cells - medal.size() - row.size(), ' ');
    row.append(medal);
    return row;
}

}  // namespace ur::product

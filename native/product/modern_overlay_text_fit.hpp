#pragma once

#include "modern_text_layout.hpp"

#include <cstddef>
#include <string>
#include <string_view>

namespace ur::product {

// Host overlay text is drawn in Standard-size cells (the readable-text
// authority's default glyph width) inside an 8-pixel margin on each side of
// its panel. These helpers give one line's cell budget and keep a dynamic
// line inside it instead of letting it spill over the game picture. Fixed
// copy is written to the budget; the box-level fit/fallback decision stays
// with resolve_modern_text_layout. Widths are logical (pre-scale) pixels, so
// presentation density is unaffected.
inline constexpr int kModernOverlayCellPixels =
    ModernTextLayoutRequest{}.standard_glyph_width;
inline constexpr int kModernOverlayPanelMargin = 8;

constexpr std::size_t modern_overlay_text_cells(int panel_w_logical) noexcept {
    const int usable = panel_w_logical - 2 * kModernOverlayPanelMargin;
    return usable > 0
        ? static_cast<std::size_t>(usable / kModernOverlayCellPixels)
        : 0u;
}

inline std::string fit_modern_overlay_text(
    std::string_view text,
    std::size_t cells) {
    return std::string(text.substr(0, cells));
}

}  // namespace ur::product

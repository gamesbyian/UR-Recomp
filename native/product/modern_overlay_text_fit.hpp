#pragma once

#include <cstddef>
#include <string>
#include <string_view>

namespace ur::product {

// Host overlay text is drawn in 8-pixel cells inside an 8-pixel margin on
// each side of its panel. These helpers keep a line inside the panel instead
// of letting it spill over the game picture; layout density is unaffected
// because widths are in logical (pre-scale) pixels.
inline constexpr int kModernOverlayCellPixels = 8;
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

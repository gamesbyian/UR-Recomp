#pragma once

#include <cstdint>

namespace ur::product {

// Logical Modern-overlay roles grounded in the canonical stock BG2 menu
// palette from analysis/generated/menu-visual-language.json. These are
// host presentation tokens, not new guest palette or input authority.
//
// Stock type hierarchy: 16px yellow title, 8px grey supporting labels,
// blue cursor. The host currently retains its provisional ASCII glyphs;
// the original font/arrow raster and animation require separate art review.
struct ModernStockMenuPalette {
    std::uint32_t title_yellow = 0xFFF8F800u;
    std::uint32_t secondary_grey = 0xFF989898u;
    std::uint32_t cursor_blue = 0xFFA0D0F8u;
    std::uint32_t shadow_black = 0xFF000000u;
    std::uint32_t background = 0xE02F2F2Fu;
    std::uint32_t header_band = 0xC0484848u;
    std::uint32_t frame_grey = 0xFF989898u;
};

inline constexpr ModernStockMenuPalette kModernStockMenuPalette{};

}  // namespace ur::product

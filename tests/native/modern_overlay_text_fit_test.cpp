#include "modern_overlay_text_fit.hpp"

#include <cassert>
#include <string>

int main() {
    using ur::product::fit_modern_overlay_text;
    using ur::product::modern_overlay_text_cells;

    // The shared pause-family panel is 212 logical pixels: 24 cells.
    static_assert(modern_overlay_text_cells(212) == 24u);
    // The 2P join panel on a 256-pixel frame is 240 pixels: 28 cells.
    static_assert(modern_overlay_text_cells(240) == 28u);
    static_assert(modern_overlay_text_cells(16) == 0u);
    static_assert(modern_overlay_text_cells(-4) == 0u);

    // The per-line budget agrees with the readable-text authority: a full
    // budget fits a Standard box of the same width, one more cell does not.
    using ur::product::ModernTextLayoutRequest;
    using ur::product::resolve_modern_text_layout;
    ModernTextLayoutRequest request{};
    request.box_width = 212;
    request.box_height = 30;
    request.row_count = 1;
    request.horizontal_padding = ur::product::kModernOverlayPanelMargin;
    request.max_characters =
        static_cast<int>(modern_overlay_text_cells(request.box_width));
    assert(resolve_modern_text_layout(request).visible);
    ++request.max_characters;
    assert(!resolve_modern_text_layout(request).visible);

    assert(fit_modern_overlay_text("SHORT", 24) == std::string("SHORT"));
    assert(fit_modern_overlay_text("PAD P1  XBOX WIRELESS CONTROLLER", 24) ==
           std::string("PAD P1  XBOX WIRELESS CO"));
    assert(fit_modern_overlay_text("ANY", 0).empty());
    return 0;
}

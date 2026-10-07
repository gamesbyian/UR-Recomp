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

    assert(fit_modern_overlay_text("SHORT", 24) == std::string("SHORT"));
    assert(fit_modern_overlay_text("PAD P1  XBOX WIRELESS CONTROLLER", 24) ==
           std::string("PAD P1  XBOX WIRELESS CO"));
    assert(fit_modern_overlay_text("ANY", 0).empty());
    return 0;
}

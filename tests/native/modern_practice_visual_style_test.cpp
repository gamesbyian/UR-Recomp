#include "modern_practice_visual_style.hpp"

#include <cassert>
#include <cstdint>

using namespace ur::product;

int main() {
    const auto original = modern_practice_visual_style(256);
    assert(original.panel_width_logical == 240);
    assert(original.title_glyph_scale == 2);
    assert(original.title_x_logical * 2 +
           14 * 8 * original.title_glyph_scale <=
           original.panel_width_logical);
    assert(original.title_y_logical + 8 * original.title_glyph_scale < 28);
    assert(original.selected_row_y_logical >= 62);
    assert(original.selected_row_y_logical +
           original.selected_row_height_logical < 80);

    // Pixel values are decoded from the original menu's documented
    // yellow title/grey metadata/blue cursor palette hierarchy.
    assert(original.title_yellow == 0xFFF8F800u);
    assert(original.secondary_grey == 0xFF989898u);
    assert(original.cursor_blue == 0xFFA0D0F8u);

    const auto narrow = modern_practice_visual_style(200);
    assert(narrow.panel_width_logical == 184);
    assert(narrow.title_glyph_scale == 1);
    assert(narrow.title_x_logical * 2 + 14 * 8 <=
           narrow.panel_width_logical);

    const auto wide = modern_practice_visual_style(342);
    assert(wide.panel_width_logical == 318);
    assert(wide.title_glyph_scale == 2);
    const auto ultra = modern_practice_visual_style(480);
    assert(ultra.panel_width_logical == 324);
    assert(ultra.title_glyph_scale == 2);

    assert(modern_practice_visual_style(0).panel_width_logical == 0);
    assert(modern_practice_visual_style(32).panel_width_logical == 0);
    return 0;
}

#include "modern_text_layout.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    ModernTextLayoutRequest standard{};
    standard.box_width = 240;
    standard.box_height = 52;
    standard.max_characters = 24;
    standard.row_count = 3;
    standard.horizontal_padding = 8;
    standard.vertical_padding = 4;

    const auto normal = resolve_modern_text_layout(standard);
    assert(normal.visible);
    assert(normal.resolved == ModernTextSize::Standard);
    assert(normal.logical_glyph_scale == 1);
    assert(normal.glyph_width == 8);
    assert(normal.glyph_height == 8);
    assert(normal.line_height == 15);
    assert(!normal.fell_back);
    assert(modern_text_raster_scale(normal, 1) == 1);
    assert(modern_text_raster_scale(normal, 4) == 4);

    ModernTextLayoutRequest roomy = standard;
    roomy.box_width = 420;
    roomy.box_height = 104;
    roomy.requested = ModernTextSize::Large;
    const auto large = resolve_modern_text_layout(roomy);
    assert(large.visible);
    assert(large.resolved == ModernTextSize::Large);
    assert(large.logical_glyph_scale == 2);
    assert(large.glyph_width == 16);
    assert(large.glyph_height == 16);
    assert(large.line_height == 30);
    assert(!large.fell_back);
    assert(modern_text_raster_scale(large, 1) == 2);
    assert(modern_text_raster_scale(large, 2) == 4);
    assert(modern_text_raster_scale(large, 4) == 8);

    ModernTextLayoutRequest tight = standard;
    tight.requested = ModernTextSize::Large;
    const auto fallback = resolve_modern_text_layout(tight);
    assert(fallback.visible);
    assert(fallback.resolved == ModernTextSize::Standard);
    assert(fallback.logical_glyph_scale == 1);
    assert(fallback.fell_back);
    assert(fallback.required_width <= tight.box_width);
    assert(fallback.required_height <= tight.box_height);

    ModernTextLayoutRequest impossible = standard;
    impossible.box_width = 100;
    impossible.requested = ModernTextSize::Large;
    const auto hidden = resolve_modern_text_layout(impossible);
    assert(!hidden.visible);
    assert(!hidden.fell_back);
    assert(modern_text_raster_scale(hidden, 2) == 0);

    ModernTextLayoutRequest rows{};
    rows.box_width = 200;
    rows.box_height = 53;
    rows.max_characters = 10;
    rows.row_count = 4;
    rows.horizontal_padding = 2;
    rows.vertical_padding = 0;
    const auto row_fit = resolve_modern_text_layout(rows);
    assert(row_fit.visible);
    assert(row_fit.required_height == 53);

    rows.box_height = 52;
    const auto row_overflow = resolve_modern_text_layout(rows);
    assert(!row_overflow.visible);

    ModernTextLayoutRequest invalid{};
    assert(!resolve_modern_text_layout(invalid).visible);
    assert(modern_text_raster_scale(normal, 0) == 0);
    assert(modern_text_raster_scale(normal, 5) == 0);

    return 0;
}

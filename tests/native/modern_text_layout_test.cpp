#include "modern_text_layout.hpp"

#include <cassert>
#include <limits>

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

    // Malformed or extreme UI envelopes must fail closed without signed
    // overflow, even when an impossible Large request falls back to Standard.
    constexpr int kMax = std::numeric_limits<int>::max();
    ModernTextLayoutRequest huge_width = standard;
    huge_width.box_width = kMax;
    huge_width.box_height = kMax;
    huge_width.max_characters = kMax;
    huge_width.standard_glyph_width = kMax;
    huge_width.horizontal_padding = kMax;
    const auto width_overflow = resolve_modern_text_layout(huge_width);
    assert(!width_overflow.visible);
    assert(width_overflow.required_width == 0);

    ModernTextLayoutRequest huge_height = standard;
    huge_height.box_height = kMax;
    huge_height.row_count = kMax;
    huge_height.standard_line_height = kMax;
    huge_height.vertical_padding = kMax;
    const auto height_overflow = resolve_modern_text_layout(huge_height);
    assert(!height_overflow.visible);
    assert(height_overflow.required_height == 0);

    ModernTextLayoutRequest large_overflow = standard;
    large_overflow.box_width = kMax;
    large_overflow.box_height = kMax;
    large_overflow.max_characters = 1;
    large_overflow.row_count = 1;
    large_overflow.horizontal_padding = 0;
    large_overflow.vertical_padding = 0;
    large_overflow.standard_glyph_width = kMax / 2 + 1;
    large_overflow.standard_glyph_height = 1;
    large_overflow.standard_line_height = 1;
    large_overflow.requested = ModernTextSize::Large;
    const auto safe_fallback = resolve_modern_text_layout(large_overflow);
    assert(safe_fallback.visible);
    assert(safe_fallback.fell_back);
    assert(safe_fallback.resolved == ModernTextSize::Standard);
    assert(safe_fallback.required_width == kMax / 2 + 1);

    ModernTextLayoutRequest exact_boundary = standard;
    exact_boundary.box_width = kMax;
    exact_boundary.box_height = 20;
    exact_boundary.max_characters = kMax;
    exact_boundary.row_count = 1;
    exact_boundary.horizontal_padding = 0;
    exact_boundary.vertical_padding = 0;
    exact_boundary.standard_glyph_width = 1;
    const auto boundary = resolve_modern_text_layout(exact_boundary);
    assert(boundary.visible);
    assert(boundary.required_width == kMax);

    return 0;
}

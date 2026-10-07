#pragma once

#include <cstdint>

namespace ur::product {

enum class ModernTextSize : std::uint8_t {
    Standard = 0,
    Large = 1,
};

struct ModernTextLayoutRequest {
    int box_width = 0;
    int box_height = 0;
    int max_characters = 0;
    int row_count = 0;
    int horizontal_padding = 0;
    int vertical_padding = 0;
    int standard_glyph_width = 8;
    int standard_glyph_height = 8;
    int standard_line_height = 15;
    ModernTextSize requested = ModernTextSize::Standard;
};

struct ModernTextLayout {
    ModernTextSize resolved = ModernTextSize::Standard;
    int logical_glyph_scale = 1;
    int glyph_width = 8;
    int glyph_height = 8;
    int line_height = 15;
    int required_width = 0;
    int required_height = 0;
    bool visible = false;
    bool fell_back = false;
};

constexpr bool modern_text_layout_request_valid(
    const ModernTextLayoutRequest& request) noexcept {
    return request.box_width > 0 &&
           request.box_height > 0 &&
           request.max_characters > 0 &&
           request.row_count > 0 &&
           request.horizontal_padding >= 0 &&
           request.vertical_padding >= 0 &&
           request.standard_glyph_width > 0 &&
           request.standard_glyph_height > 0 &&
           request.standard_line_height >= request.standard_glyph_height;
}

constexpr ModernTextLayout modern_text_layout_for_scale(
    const ModernTextLayoutRequest& request,
    int logical_glyph_scale) noexcept {
    ModernTextLayout layout{};
    if (!modern_text_layout_request_valid(request) ||
        logical_glyph_scale < 1 || logical_glyph_scale > 2) {
        return layout;
    }

    layout.logical_glyph_scale = logical_glyph_scale;
    layout.glyph_width =
        request.standard_glyph_width * logical_glyph_scale;
    layout.glyph_height =
        request.standard_glyph_height * logical_glyph_scale;
    layout.line_height =
        request.standard_line_height * logical_glyph_scale;
    layout.required_width =
        request.horizontal_padding * 2 +
        request.max_characters * layout.glyph_width;
    layout.required_height =
        request.vertical_padding * 2 +
        (request.row_count - 1) * layout.line_height +
        layout.glyph_height;
    layout.visible =
        layout.required_width <= request.box_width &&
        layout.required_height <= request.box_height;
    layout.resolved = logical_glyph_scale == 2
        ? ModernTextSize::Large
        : ModernTextSize::Standard;
    return layout;
}

/*
 * Readability changes logical UI layout, not presentation density.
 *
 * Standard text uses the existing logical glyph metrics. Large text doubles
 * logical glyph/line metrics only when the caller-provided content envelope
 * still fits the existing logical box. If Large cannot fit, the request falls
 * back to Standard rather than clipping, growing the canvas, or multiplying
 * Internal Render Scale. If Standard cannot fit either, the layout fails
 * closed and the caller must reflow/shorten its content explicitly.
 */
constexpr ModernTextLayout resolve_modern_text_layout(
    const ModernTextLayoutRequest& request) noexcept {
    if (!modern_text_layout_request_valid(request)) return {};

    if (request.requested == ModernTextSize::Large) {
        auto large = modern_text_layout_for_scale(request, 2);
        if (large.visible) return large;

        auto standard = modern_text_layout_for_scale(request, 1);
        standard.fell_back = standard.visible;
        return standard;
    }
    return modern_text_layout_for_scale(request, 1);
}

/* Compose the final raster glyph scale only after logical fitting.
 * presentation_scale is the existing 1x-4x density authority. */
constexpr int modern_text_raster_scale(
    const ModernTextLayout& layout,
    int presentation_scale) noexcept {
    if (!layout.visible ||
        presentation_scale < 1 || presentation_scale > 4) {
        return 0;
    }
    return layout.logical_glyph_scale * presentation_scale;
}

}  // namespace ur::product

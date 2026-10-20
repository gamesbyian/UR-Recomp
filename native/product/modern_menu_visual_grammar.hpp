#pragma once

// Shared presentation-only Uniracers menu grammar. No SDL, input, route,
// profile, ROM/guest state, or owner-specific screen composition lives here.
// Evidence: analysis/generated/menu-visual-language.json (canonical USA
// clean-boot BG1/BG2 + OBJ observation), docs/UI-STATE-MAP.md.
// In particular the actual 16x16 glyph shapes and 32x32 spinning OBJ arrow
// have NOT been reconstructed into a host sprite atlas. Never describe the
// provisional host ASCII fallback as the original type or cursor art.

#include "modern_stock_menu_palette.hpp"
#include "modern_menu_source_atlas.hpp"  // optional source-verified raster adapter

#include <array>
#include <cstdint>

namespace ur::product {

// BGR555 source colours expressed as the measured RGB8 steps. The original
// yellow letters use all five steps vertically, not a flat "brand yellow".
// The renderer's currently installed ASCII glyphs cannot consume a gradient:
// screen owners should provide an authentic, licensed raster atlas before
// considering that last-mile font gap solved.
inline constexpr std::array<std::uint32_t, 5> kModernMenuYellowRamp{{
    0xFFF8F800u, 0xFFC8C800u, 0xFF989800u, 0xFF686800u, 0xFF303000u
}};
inline constexpr std::array<std::uint32_t, 5> kModernMenuGreyRamp{{
    0xFF808080u, 0xFF686868u, 0xFF505050u, 0xFF303030u, 0xFF181818u
}};

// Stock main-menu arrow OBJ palette 7, brightest sampled outline/highlight
// and the shadow's measured +7/+7 raster displacement.
inline constexpr std::uint32_t kModernMenuCursorLight = 0xFFA0D0F8u;
inline constexpr std::uint32_t kModernMenuCursorDark = 0xFF283058u;
inline constexpr int kModernMenuCursorWidth = 32;
inline constexpr int kModernMenuCursorHeight = 32;
inline constexpr int kModernMenuCursorShadowOffset = 7;
inline constexpr int kModernMenuTitleCell = 16;
inline constexpr int kModernMenuDetailPitch = 8;
inline constexpr int kModernMenuDetailHeight = 16;
inline constexpr int kModernMenuStockRowPitch = 24;
inline constexpr int kModernMenuCheckerCell = 16;
inline constexpr int kModernMenuStockSlideDistance = 256;
inline constexpr int kModernMenuSlideFrameCount = 39;
inline constexpr int kModernMenuSpinPeriod = 32;

// Genuine stock cursor CHR tile addresses, chronological orientation order.
// Two guest video frames per tile; 16 frames of animation, 32-frame loop.
// A host atlas must remap these addresses to decoded art; do not draw an
// invented triangle in place of the original dimensional arrow.
inline constexpr std::array<int, 16> kModernMenuSpinTile{{
    8, 4, 0, 204, 200, 196, 192, 140,
    136, 132, 128, 76, 72, 68, 64, 12
}};

constexpr int modern_menu_cursor_chr_tile(std::uint32_t frame) noexcept {
    return kModernMenuSpinTile[(frame / 2u) % kModernMenuSpinTile.size()];
}

// Measured stock 39-frame BG2 strip slide. BG1/logo stays fixed; this is
// motion *metadata*, not permission to scroll Authentic host assets.
inline constexpr std::array<int, kModernMenuSlideFrameCount> kModernMenuSlidePixels{{
    1, 3, 6, 10, 15, 21, 28, 36, 44, 52, 60, 68, 76,
    84, 92, 100, 108, 116, 124, 132, 140, 148, 156,
    164, 172, 180, 188, 196, 204, 212, 220, 228,
    235, 241, 246, 250, 253, 255, 256
}};

constexpr int modern_menu_slide_pixels(unsigned elapsed_frames,
                                       bool backwards) noexcept {
    const int offset = elapsed_frames == 0 ? 0 :
        elapsed_frames >= kModernMenuSlideFrameCount ? kModernMenuStockSlideDistance :
        kModernMenuSlidePixels[elapsed_frames - 1u];
    return backwards ? kModernMenuStockSlideDistance - offset : offset;
}

// Integer-only stock approximation: input-frame start, roughly 1/4 of the
// remaining displacement each frame, no overshoot; stable at the target.
// For e.g. 24px movement the first steps are 6, 5, 4...  Preserve the real
// independent animation clock and reduced-motion preference at host boundary.
constexpr int modern_menu_cursor_ease_axis(int current, int target) noexcept {
    if (current == target) return target;
    const auto distance = current > target
        ? static_cast<std::int64_t>(current) - target
        : static_cast<std::int64_t>(target) - current;
    const auto step = (distance + 3) / 4;
    const auto next = current > target
        ? static_cast<std::int64_t>(current) - step
        : static_cast<std::int64_t>(current) + step;
    return static_cast<int>(next);
}

struct ModernMenuColumns {
    int content_inset = 8;
    int primary_width = 0;
    int secondary_x = 0;
    int secondary_width = 0;
    bool two_column = false;
};

// Shared column *contract* for screen composers, not a root/title layout.
// The 16:9 native canvas is 342x224 logical at 7:6 PAR; 4:3 is 256x224.
// Detail/preview columns only appear when at least 320 logical pixels fit.
// Overflow is rejected, not cropped or reinterpreted as density scaling.
constexpr ModernMenuColumns modern_menu_columns(int available_width) noexcept {
    ModernMenuColumns result{};
    if (available_width < 32) return result;
    if (available_width < 320) {
        result.primary_width = available_width - 16;
        return result;
    }
    result.two_column = true;
    result.primary_width = 168;
    result.secondary_x = 184;
    result.secondary_width = available_width - 192;
    return result;
}

constexpr bool modern_menu_native_canvas(int width, int height) noexcept {
    return height == 224 && (width == 256 || width == 342);
}

// This is the exact existing host text-shadow composition, factored into a
// common type primitive. Actual source glyph shape/shading remains subject to
// original-atlas reconstruction; the host fallback draw_text is still ASCII.
// The caller positions the heading and fits its text before drawing.
template <typename Painter>
inline void modern_menu_paint_shadowed_heading(
    const Painter& paint, std::uint32_t* pixels,
    int stride, int surface_height,
    int x, int y, const char* label,
    int glyph_scale, int physical_scale) {
    if (!paint.draw_text || !pixels || !label ||
        stride <= 0 || surface_height <= 0 ||
        x < 0 || y < 0 || x >= stride || y >= surface_height ||
        glyph_scale < 1 || glyph_scale > 2 ||
        physical_scale < 1 || physical_scale > 4) return;
    paint.draw_text(pixels, stride, surface_height,
                    x + physical_scale, y + physical_scale,
                    label, kModernStockMenuPalette.shadow_black,
                    glyph_scale * physical_scale);
    paint.draw_text(pixels, stride, surface_height,
                    x, y, label, kModernStockMenuPalette.title_yellow,
                    glyph_scale * physical_scale);
}

// A restrained reuse of stock BG1's measured grey checkerboard motif.
// Host-only and clipped by caller-owned panel rect, never replaces the real
// logo, recovered leaf artwork, or stock guest presentation. The checker
// lives underneath content; selection colour comes from the stock blue OBJ.
template <typename Painter>
inline void modern_menu_paint_checker_backdrop(
    const Painter& paint, std::uint32_t* pixels,
    int stride, int surface_height,
    int x, int y, int width, int height, int logical_scale) {
    if (!paint.fill_rect || !pixels || stride <= 0 || surface_height <= 0 ||
        x < 0 || y < 0 || width <= 0 || height <= 0 ||
        x > stride || y > surface_height ||
        width > stride - x || height > surface_height - y ||
        logical_scale < 1 || logical_scale > 4) return;

    const int cell = kModernMenuCheckerCell * logical_scale;
    paint.fill_rect(pixels, stride, surface_height, x, y, width, height,
                    kModernStockMenuPalette.background);
    // Sparse every-other-square underlay. Grey palette ramp RGB8 48/80;
    // alpha retains the caller's existing host overlay convention.
    for (int yy = 0, row = 0; yy < height; yy += cell, ++row) {
        for (int xx = (row & 1) ? 0 : cell; xx < width; xx += 2 * cell) {
            const int w = xx + cell > width ? width - xx : cell;
            const int h = yy + cell > height ? height - yy : cell;
            paint.fill_rect(pixels, stride, surface_height,
                            x + xx, y + yy, w, h, 0xE0505050u);
        }
    }
}

// Stock arrow blue against a dark OBJ-colour-derived selection field.
// This is a presentation fallback until the actual 32x32 arrow atlas is
// supplied; the selector must always remain legible without animation.
// The row's string, x/y and spacing are owned by each screen composer.
template <typename Painter>
inline void modern_menu_paint_focus_band(
    const Painter& paint, std::uint32_t* pixels,
    int stride, int surface_height,
    int x, int y, int width, int height, int scale) {
    if (!paint.fill_rect || !pixels || stride <= 0 || surface_height <= 0 ||
        x < 0 || y < 0 || width <= 0 || height <= 0 ||
        width > stride - x || height > surface_height - y ||
        scale < 1 || scale > 4) return;
    paint.fill_rect(pixels, stride, surface_height, x, y, width, height,
                    0xE0283058u);
    const int marker_width = 3 * scale > width ? width : 3 * scale;
    paint.fill_rect(pixels, stride, surface_height,
                    x, y, marker_width, height, kModernMenuCursorLight);
}

} // namespace ur::product

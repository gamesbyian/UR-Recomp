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
#include <cstddef>
#include <cstdint>
#include <string_view>

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
// A narrowly scoped host accessibility adaptation, not an original CGRAM
// assertion: #989898 stock-family grey has only 2.80:1 contrast against
// the bright #505050 checker squares in the native root. #C8C8C8 preserves
// the neutral secondary hierarchy but meets 4.82:1 on the worst square.
// Applied only to root supporting copy drawn directly over the checker;
// source raster palettes and Authentic remain completely untouched.
inline constexpr std::uint32_t kModernMenuCheckerLegibleGrey = 0xFFC8C8C8u;

inline constexpr std::uint32_t kModernMenuCursorLight = 0xFFA0D0F8u;
inline constexpr std::uint32_t kModernMenuCursorDark = 0xFF283058u;
// Captured stock cursor is two distinct 32x32 OBJs: blue arrow palette 7,
// maroon drop-shadow palette 5 at +7,+7. This exact 72/32/48 shade belongs
// inside the 39x39 composited original sheet; do NOT paint a second shadow
// over an already composite source atlas.
inline constexpr std::uint32_t kModernMenuSourceCursorShadow = 0xFF482030u;
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

// Context-specific highlights recovered from the original PPU menu states.
// The main menu blue is NOT the colour of every original menu cursor:
// PICK YOUR UNI uses RGB(136,200,240), while PICK TOUR and PICK TRACK use
// RGB(240,160,136). These are source palette observations, not an automatic
// Modern destination mapping. A screen owner selects context deliberately.
enum class ModernMenuSourceCursor : std::uint8_t {
    Main, Rider, Tour, Track,
};

constexpr std::uint32_t modern_menu_cursor_highlight(
    ModernMenuSourceCursor context) noexcept {
    switch (context) {
        case ModernMenuSourceCursor::Rider: return 0xFF88C8F0u;
        case ModernMenuSourceCursor::Tour:
        case ModernMenuSourceCursor::Track: return 0xFFF0A088u;
        case ModernMenuSourceCursor::Main: return kModernMenuCursorLight;
    }
    // Invalid future enum values stay visibly focused rather than
    // introducing an invented colour or an invisible selection marker.
    return kModernMenuCursorLight;
}

// The stock big-font source uses 16px word gaps in the main, tour and
// track headings, but PICK YOUR UNI is composed with measured 8px gaps.
// Source font painters must lay out words with these advances; the host
// ASCII fallback does not become original lettering by applying this rule.
constexpr int modern_menu_observed_heading_word_gap(
    ModernMenuSourceCursor context) noexcept {
    return context == ModernMenuSourceCursor::Rider ? 8 : 16;
}

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

// One specifically observed 1994 cursor route: main-menu row 1 to row 2,
// y=70 -> y=93. These are the 12 measured *per-video-frame* displacement
// increments in analysis/generated/menu-visual-language.json, not a general
// easing formula. In particular, the original briefly holds at frames 10/11
// before the final 1px settle; our proportional approximation cannot encode
// that without explicit source data. Animation ownership/clock stays with
// the consuming host.
inline constexpr std::array<int, 12> kModernMenuObservedRowMoveY{{
    6, 4, 3, 3, 2, 1, 1, 1, 1, 0, 0, 1
}};

constexpr int modern_menu_observed_first_row_move_y(
    unsigned elapsed_frames) noexcept {
    int delta = 0;
    const auto frames = elapsed_frames < kModernMenuObservedRowMoveY.size()
        ? elapsed_frames : static_cast<unsigned>(kModernMenuObservedRowMoveY.size());
    for (unsigned i = 0; i < frames; ++i)
        delta += kModernMenuObservedRowMoveY[i];
    return delta;
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
    // This public primitive can be used outside the already bounded root.
    // Its old guard admitted a title starting at the final framebuffer
    // column, then issued BOTH text calls with most glyph pixels clipped.
    // Preflight the whole 8px-pitch host string and the shadow offset first.
    // Real root labels are short literals, but a malformed external label
    // must not trigger either callback or scan without a bound.
    std::size_t glyph_count = 0;
    while (glyph_count <= 128u && label[glyph_count] != '\0')
        ++glyph_count;
    if (glyph_count == 0u || glyph_count > 128u) return;
    const std::int64_t draw_scale =
        static_cast<std::int64_t>(glyph_scale) * physical_scale;
    const std::int64_t right =
        static_cast<std::int64_t>(x) + glyph_count * 8 * draw_scale +
        physical_scale;
    const std::int64_t bottom =
        static_cast<std::int64_t>(y) + 8 * draw_scale + physical_scale;
    if (right > stride || bottom > surface_height) return;
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
    int x, int y, int width, int height, int scale,
    ModernMenuSourceCursor cursor_context = ModernMenuSourceCursor::Main) {
    if (!paint.fill_rect || !pixels || stride <= 0 || surface_height <= 0 ||
        x < 0 || y < 0 || width <= 0 || height <= 0 ||
        width > stride - x || height > surface_height - y ||
        scale < 1 || scale > 4) return;
    paint.fill_rect(pixels, stride, surface_height, x, y, width, height,
                    0xE0283058u);
    const int marker_width = 3 * scale > width ? width : 3 * scale;
    paint.fill_rect(pixels, stride, surface_height,
                    x, y, marker_width, height,
                    modern_menu_cursor_highlight(cursor_context));
}

// Optional exact source-raster consumer: only screen owners with a
// separately admitted original heading atlas may call this. The shared
// source image painter performs whole-string preflight and pixel-atomic
// refusal; this adapter supplies just the measured screen word gap.
inline bool modern_menu_paint_source_heading_context(
    const ModernMenuSourcePixels& source_heading,
    std::uint32_t* pixels, std::size_t count,
    int stride, int surface_height, int x, int y,
    std::string_view label, int scale,
    ModernMenuSourceCursor context) noexcept {
    return modern_menu_paint_source_text(
        source_heading, ModernMenuSourceSheet::Heading,
        pixels, count, stride, surface_height, x, y, label, scale,
        modern_menu_observed_heading_word_gap(context));
}

// The first-party exported 624x39 cursor sheet stores sixteen original
// MAIN-menu arrow+shadow 39x39 poses in frame 0,2,...,30 order. Its pixels
// retain the main screen's blue CGRAM: do NOT call this a Tour/Track warm
// cursor or assume the separate focus-band highlight can recolour it.
// A non-main source sprite demands separate same-state PPU/rights proof.
// Each pose holds for
// exactly two *host menu* frames, repeating at 32. Source palette and shadow
// pixels come from the admitted atlas: never flatten them to one accent.
// This does not drive or read the guest's animation clock and paints nothing
// if the supplied image/target is invalid. Caller owns coordinates, focus
// fallback, clipping and reduced-motion frame selection.
// A sprite sheet with fifteen good poses and one corrupted late pose
// must not be partially admitted and visibly vanish half-way through the
// original 32-frame spin. Verify all sixteen 39x39 source poses before
// drawing any phase. This is a raster completeness check, NOT source ROM,
// CGRAM palette, art ownership or licence attestation.
inline bool modern_menu_source_cursor_sheet_complete(
    const ModernMenuSourcePixels& sheet) noexcept {
    if (!modern_menu_source_buffer(sheet, 624, 39)) return false;
    for (int pose = 0; pose < 16; ++pose) {
        bool has_ink = false;
        for (int yy = 0; yy < 39; ++yy)
            for (int xx = 0; xx < 39; ++xx) {
                const auto pixel =
                    sheet.pixels[static_cast<std::size_t>(yy) * sheet.stride +
                                 static_cast<std::size_t>(pose * 39 + xx)];
                const auto alpha = pixel >> 24;
                if (alpha == 255) has_ink = true;
                else if (alpha != 0 || pixel != 0u) return false;
            }
        if (!has_ink) return false;
    }
    return true;
}

inline bool modern_menu_paint_source_cursor_phase(
    const ModernMenuSourcePixels& source_cursor,
    std::uint32_t* pixels, std::size_t count,
    int stride, int surface_height, int x, int y,
    std::uint32_t menu_frame, int scale) noexcept {
    if (!modern_menu_source_cursor_sheet_complete(source_cursor))
        return false;
    const int pose = static_cast<int>((menu_frame / 2u) % kModernMenuSpinTile.size());
    return modern_menu_paint_source_cell(
        source_cursor, ModernMenuSourceSheet::Cursor,
        pixels, count, stride, surface_height, x, y, pose, scale);
}

} // namespace ur::product

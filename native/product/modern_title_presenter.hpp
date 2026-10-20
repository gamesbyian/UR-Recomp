#pragma once

// Native Modern title artwork and timing. Draws through the SAME host-owned
// pixel/text painter as the five-destination Modern root; no SDL, ROM/WRAM,
// independent input loop, guest lifecycle, or Authentic mode participation.
// 342x224 at the preserved 7:6 PAR is a physical 16:9 composition. The 256px
// fallback is deliberately composed (not cropped from 342) for fixed hosts.
#include "modern_root_overlay_presenter.hpp"
#include "modern_title_retail_reference.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace ur::product {

enum class ModernTitlePhase : std::uint8_t {
    Intro,
    Leaving,
    Root,
};

struct ModernTitleState {
    ModernTitlePhase phase = ModernTitlePhase::Root;
    unsigned age = 0;
    unsigned exit_age = 0;
    bool reduced_motion = false;
};

constexpr ModernTitleState modern_title_boot(
    bool enabled, bool reduced_motion = false) noexcept {
    return {enabled ? ModernTitlePhase::Intro : ModernTitlePhase::Root,
            reduced_motion ? 40u : 0u, 0u, reduced_motion};
}

constexpr bool modern_title_active(ModernTitleState state) noexcept {
    return state.phase != ModernTitlePhase::Root;
}

// Root handoff is a one-way confirmation on a genuine *new* A/Start/Enter
// physical edge. All other inputs remain owned by the title while visible.
// A held button cannot select PLAY on the following frame.
constexpr ModernTitleState modern_title_confirm(ModernTitleState state) noexcept {
    if (state.phase == ModernTitlePhase::Intro) {
        state.phase = state.reduced_motion
            ? ModernTitlePhase::Root : ModernTitlePhase::Leaving;
        state.exit_age = 0;
    }
    return state;
}

constexpr ModernTitleState modern_title_advance(ModernTitleState state) noexcept {
    if (state.phase == ModernTitlePhase::Intro && state.age < 4095u)
        ++state.age;
    if (state.phase == ModernTitlePhase::Leaving && ++state.exit_age >= 14u)
        state.phase = ModernTitlePhase::Root;
    return state;
}

inline bool render_modern_title(
    const ModernRootOverlayPainter& paint,
    std::uint32_t* pixels, int stride, int surface_height,
    int logical_width, ModernTitleState state, bool europe = false) {
    if (!paint.valid() || !pixels || (logical_width != 256 && logical_width != 342) ||
        stride < logical_width || surface_height < 224 ||
        !modern_title_active(state))
        return false;

    constexpr auto black = 0xFF080D1Bu;
    constexpr auto midnight = 0xFF101B32u;
    constexpr auto cobalt = 0xFF1F4877u;
    constexpr auto blue = 0xFF6CBFEBu;
    constexpr auto gold = kModernStockMenuPalette.title_yellow;
    constexpr auto grey = kModernStockMenuPalette.secondary_grey;
    const int w = logical_width;
    const int h = 224;
    const bool wide = w == 342;
    const int center = w / 2;

    // Full-bleed horizontal bands leave readable letterforms on either
    // screen size. All geometry is resolution-independent logical pixels.
    paint.fill_rect(pixels, stride, surface_height, 0, 0, w, h, black);
    paint.fill_rect(pixels, stride, surface_height, 0, 0, w, 130, midnight);
    paint.fill_rect(pixels, stride, surface_height, 0, 129, w, 2, cobalt);
    // Fine-grid technical register references the original cartridge's
    // fast strip/racing grammar without borrowing unapproved HD rider art.
    for (int x = 13; x < w; x += 24)
        paint.fill_rect(pixels, stride, surface_height, x, 132, 1, 92,
                        0xFF152943u);
    for (int y = 139; y < h; y += 16)
        paint.fill_rect(pixels, stride, surface_height, 0, y, w, 1,
                        0xFF152943u);
    paint.fill_rect(pixels, stride, surface_height, 0, 0, w, 3, gold);
    paint.fill_rect(pixels, stride, surface_height, 0, 3, w, 2, cobalt);

    // Floating strip: articulated, alternating shaded sections with an
    // independent far edge. No posts, ground shadow or implied flat road.
    for (int x = 0; x < w; x += 3) {
        const int t = ((x / 6) + 5) % 48;
        const int hill = t < 24 ? t : 48 - t;
        const int y = 160 + (hill - 12) / 2;
        const std::uint32_t deck = (x / 18) % 3 == 2
            ? 0xFF24456Du : 0xFF32628Cu;
        const int section_w = std::min(3, w - x);
        paint.fill_rect(pixels, stride, surface_height, x, y, section_w, 17, deck);
        paint.fill_rect(pixels, stride, surface_height, x, y, section_w, 2, blue);
        paint.fill_rect(pixels, stride, surface_height, x, y + 16, section_w, 2,
                        0xFF07101Bu);
    }

    // Retail-verified 238x81 Uniracers/Unirally title logo and two title
    // unicycles, preserved without resampling or an AI redraw. The original
    // indexed RGB content comes from regional_title_retail_asset.hpp, whose
    // exact source/EU crops were independently hash-qualified. The border
    // deliberately frames a 4:3 source plate within the Modern 16:9 field.
    const char* brand = europe ? "UNIRALLY" : "UNIRACERS";
    const int brand_chars = europe ? 8 : 9;
    const int reveal = state.phase == ModernTitlePhase::Intro
        ? static_cast<int>(std::min(state.age, 24u)) : 24;
    if (reveal > 4) {
        const int lift = (24 - reveal) / 2;
        const int artwork_x = center - regional_title_asset::kWidth / 2;
        const int artwork_y = 27 + lift;
        paint.draw_text(pixels, stride, surface_height,
                        center - brand_chars * 4, 12, brand, grey, 1);
        paint.stroke_rect(pixels, stride, surface_height,
                          artwork_x - 2, artwork_y - 2,
                          regional_title_asset::kWidth + 4,
                          regional_title_asset::kHeight + 4, cobalt);
        const bool retail_drawn = title_retail_reference::paint_retail_title_art(
            pixels, stride, surface_height, artwork_x, artwork_y, europe);
        if (!retail_drawn) {
            // Corrupt or absent retail data fails closed to the same
            // stock-yellow 16px title treatment as the Modern root.
            paint.draw_text(pixels, stride, surface_height,
                            center - brand_chars * 8 + 1, 54 + lift + 1,
                            brand, black, 2);
            paint.draw_text(pixels, stride, surface_height,
                            center - brand_chars * 8, 54 + lift,
                            brand, gold, 2);
        }
        const char* strap = "THE ONE-WHEEL RACING CLASSIC";
        paint.draw_text(pixels, stride, surface_height,
                        center - 28 * 4, 116 + lift, strap, grey, 1);
    }

    // A disciplined small unicycle vignette within the track strip, clear
    // of the authentic title plate and subtitle. Source title art above
    // remains the authoritative hero, with no substituted gameplay sprite.
    const int wheel_cx = wide ? w - 51 : w - 39;
    const int wheel_cy = 170;
    constexpr int radius = 18;
    if (state.age >= 12 || state.phase == ModernTitlePhase::Leaving) {
        // Eight fixed-radius, integer-only spoke paths: reproducible 1x
        // raster regardless of host math implementations or frame rate.
        constexpr int spokes[8][2] = {
            {0, -14}, {10, -10}, {14, 0}, {10, 10},
            {0, 14}, {-10, 10}, {-14, 0}, {-10, -10}};
        for (const auto& spoke : spokes) {
            for (int n = 0; n <= 14; ++n) {
                const int px = wheel_cx + (spoke[0] * n) / 14;
                const int py = wheel_cy + (spoke[1] * n) / 14;
                paint.fill_rect(pixels, stride, surface_height,
                    px, py, 1, 1, cobalt);
            }
        }
        // Pixel-rim ring and dark tyre. Every scanline explicitly paints
        // the top/bottom points, never leaves the wheel as open brackets.
        for (int dy = -radius; dy <= radius; ++dy) {
            const double unit = static_cast<double>(dy) / radius;
            const int extent = static_cast<int>(
                std::sqrt(std::max(0.0, 1.0 - unit * unit)) * radius);
            const int y = wheel_cy + dy;
            paint.fill_rect(pixels, stride, surface_height,
                wheel_cx - extent, y, 2, 1, gold);
            paint.fill_rect(pixels, stride, surface_height,
                wheel_cx + extent - 1, y, 2, 1, gold);
        }
        // Bounded fork and seat register. Unlike the earlier tall graphic,
        // the saddle begins BELOW the slogan and cannot cut its glyphs.
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 1, 134, 3, 33, blue);
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 8, 130, 17, 4, gold);
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 5, 129, 11, 1, blue);
        for (int n = 0; n < 17; ++n) {
            paint.fill_rect(pixels, stride, surface_height,
                wheel_cx - 3 - n / 5, 152 + n, 2, 1, blue);
            paint.fill_rect(pixels, stride, surface_height,
                wheel_cx + 2 + n / 5, 152 + n, 2, 1, blue);
        }
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 2, wheel_cy - 2, 5, 5, gold);
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 1, wheel_cy + 3, 2, 7, blue);
        paint.fill_rect(pixels, stride, surface_height,
            wheel_cx - 8, wheel_cy + 10, 8, 2, gold);
    }

    // A short controller-first affordance sits in a steady safe-area.
    // Pulse is additive but the prompt never disappears completely.
    paint.fill_rect(pixels, stride, surface_height,
                    0, h - 31, w, 31, 0xFF080D1Bu);
    paint.fill_rect(pixels, stride, surface_height,
                    0, h - 31, w, 2, gold);
    if (state.phase == ModernTitlePhase::Intro) {
        const bool bright = state.reduced_motion || (state.age / 30u) % 2u == 0u;
        constexpr char prompt[] = "PRESS A / START";
        paint.draw_text(pixels, stride, surface_height,
                        center - 15 * 4, h - 21, prompt,
                        bright ? gold : grey, 1);
    } else {
        // An exact fourteen-guest-frame exit sweep announces the handoff,
        // then the existing Modern root takes sole rendering/input ownership.
        const int sweep = static_cast<int>(
            (static_cast<unsigned>(w) * state.exit_age) / 14u);
        paint.fill_rect(pixels, stride, surface_height,
                        0, 192, sweep, 3, blue);
        constexpr char opening[] = "SELECTING RACER";
        paint.draw_text(pixels, stride, surface_height,
                        center - 15 * 4, h - 21, opening, gold, 1);
    }
    return true;
}

} // namespace ur::product

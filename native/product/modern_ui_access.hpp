#pragma once

// Shared Modern UI accessibility and presentation primitives. Presentation
// policy only: no SDL, input routing, profile, ROM/guest state or
// owner-specific screen composition. Screen owners consume these helpers;
// they do not restyle Authentic, and passing them is a measured engineering
// check, never human visual approval or original-game parity.
//
//  * WCAG 2.x relative luminance / contrast on literal framebuffer RGB
//    (integer fixed point, usable in static_assert).
//  * Focus indicators that never depend on colour or animation alone.
//  * Title/action-safe insets and integer resolution scaling for the
//    342x224 (16:9) and 256x224 (4:3) native logical canvases.
//  * Reduced-motion resolution to the settled frame.
//  * Disabled-control semantics: visible, skipped by navigation, refused
//    on activation, with a reason that remains discoverable.

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

// sRGB-to-linear in Q20 for every 8-bit channel value.
inline constexpr std::array<std::uint32_t, 256> kModernUiLinearQ20{{
    0u, 318u, 637u, 955u, 1273u, 1591u, 1910u, 2228u,
    2546u, 2864u, 3183u, 3509u, 3855u, 4220u, 4605u, 5009u,
    5433u, 5878u, 6343u, 6828u, 7335u, 7863u, 8413u, 8984u,
    9578u, 10193u, 10832u, 11492u, 12176u, 12883u, 13614u, 14368u,
    15145u, 15947u, 16773u, 17624u, 18499u, 19399u, 20324u, 21274u,
    22250u, 23251u, 24278u, 25331u, 26410u, 27516u, 28648u, 29807u,
    30993u, 32205u, 33445u, 34713u, 36008u, 37331u, 38681u, 40060u,
    41467u, 42903u, 44367u, 45860u, 47381u, 48932u, 50512u, 52121u,
    53760u, 55428u, 57127u, 58855u, 60613u, 62402u, 64221u, 66071u,
    67951u, 69862u, 71805u, 73778u, 75783u, 77819u, 79886u, 81985u,
    84117u, 86280u, 88475u, 90702u, 92962u, 95254u, 97579u, 99937u,
    102328u, 104751u, 107208u, 109698u, 112222u, 114779u, 117370u, 119994u,
    122653u, 125345u, 128072u, 130833u, 133628u, 136458u, 139323u, 142222u,
    145156u, 148125u, 151130u, 154169u, 157244u, 160355u, 163501u, 166683u,
    169900u, 173154u, 176443u, 179769u, 183131u, 186530u, 189964u, 193436u,
    196944u, 200489u, 204072u, 207691u, 211347u, 215041u, 218772u, 222540u,
    226346u, 230190u, 234071u, 237991u, 241948u, 245944u, 249978u, 254050u,
    258161u, 262310u, 266498u, 270724u, 274990u, 279294u, 283637u, 288020u,
    292442u, 296903u, 301404u, 305944u, 310523u, 315143u, 319802u, 324502u,
    329241u, 334021u, 338840u, 343700u, 348601u, 353542u, 358523u, 363546u,
    368609u, 373713u, 378858u, 384044u, 389271u, 394539u, 399849u, 405201u,
    410594u, 416028u, 421504u, 427022u, 432582u, 438184u, 443828u, 449515u,
    455243u, 461014u, 466827u, 472683u, 478582u, 484523u, 490507u, 496534u,
    502604u, 508717u, 514873u, 521072u, 527315u, 533601u, 539930u, 546303u,
    552720u, 559181u, 565685u, 572234u, 578826u, 585462u, 592143u, 598868u,
    605637u, 612451u, 619309u, 626211u, 633159u, 640151u, 647188u, 654270u,
    661397u, 668569u, 675786u, 683048u, 690356u, 697709u, 705108u, 712552u,
    720042u, 727577u, 735159u, 742786u, 750459u, 758178u, 765944u, 773755u,
    781613u, 789517u, 797468u, 805465u, 813509u, 821599u, 829736u, 837920u,
    846151u, 854429u, 862753u, 871125u, 879545u, 888011u, 896525u, 905086u,
    913695u, 922351u, 931055u, 939807u, 948606u, 957453u, 966349u, 975292u,
    984283u, 993323u, 1002411u, 1011547u, 1020731u, 1029964u, 1039246u, 1048576u,
}};

// Q20 relative luminance of 0xAARRGGBB (alpha ignored: composite first).
constexpr std::uint32_t modern_ui_luminance_q20(std::uint32_t argb) noexcept {
    const std::uint64_t r = kModernUiLinearQ20[(argb >> 16) & 0xFFu];
    const std::uint64_t g = kModernUiLinearQ20[(argb >> 8) & 0xFFu];
    const std::uint64_t b = kModernUiLinearQ20[argb & 0xFFu];
    // Rec.709 weights 0.2126/0.7152/0.0722 in Q16.
    return static_cast<std::uint32_t>((r * 13933u + g * 46871u + b * 4732u) >> 16);
}

// Contrast ratio in hundredths (4.50:1 == 450). Range 100..2100.
constexpr std::uint32_t modern_ui_contrast_x100(std::uint32_t a,
                                                std::uint32_t b) noexcept {
    std::uint64_t hi = modern_ui_luminance_q20(a);
    std::uint64_t lo = modern_ui_luminance_q20(b);
    if (hi < lo) { const auto t = hi; hi = lo; lo = t; }
    const std::uint64_t half = (1u << 20) / 20u;  // 0.05
    return static_cast<std::uint32_t>(((hi + half) * 100u) / (lo + half));
}

inline constexpr std::uint32_t kModernUiTextContrastX100 = 450;    // body text
inline constexpr std::uint32_t kModernUiFocusContrastX100 = 300;   // indicators

constexpr bool modern_ui_text_legible(std::uint32_t fg,
                                      std::uint32_t bg) noexcept {
    return modern_ui_contrast_x100(fg, bg) >= kModernUiTextContrastX100;
}

// Worst-case check against a set of backgrounds (e.g. both checker cells).
template <std::size_t N>
constexpr bool modern_ui_text_legible_on_all(
    std::uint32_t fg, const std::array<std::uint32_t, N>& backgrounds) noexcept {
    for (const auto bg : backgrounds)
        if (!modern_ui_text_legible(fg, bg)) return false;
    return true;
}

// Smallest 8px-pitch host glyph scale whose physical cap height reaches
// min_physical_px; refuses (0) when no scale up to 4 qualifies.
constexpr int modern_ui_min_text_scale(int min_physical_px) noexcept {
    for (int s = 1; s <= 4; ++s)
        if (8 * s >= min_physical_px) return s;
    return 0;
}

struct ModernUiRect {
    int x = 0, y = 0, width = 0, height = 0;
    constexpr int right() const noexcept { return x + width; }
    constexpr int bottom() const noexcept { return y + height; }
};

constexpr bool modern_ui_rect_contains(const ModernUiRect& outer,
                                       const ModernUiRect& inner) noexcept {
    return inner.width > 0 && inner.height > 0 &&
           inner.x >= outer.x && inner.y >= outer.y &&
           inner.right() <= outer.right() && inner.bottom() <= outer.bottom();
}

// Title-safe region of a logical canvas: 5% of each dimension, rounded up,
// never less than 8px horizontally (one host glyph). Invalid canvases give
// an empty rectangle so callers refuse to paint.
constexpr ModernUiRect modern_ui_title_safe(int width, int height) noexcept {
    if (width < 64 || height < 64 || width > 16384 || height > 16384) return {};
    const int dx = (width * 5 + 99) / 100;
    const int dy = (height * 5 + 99) / 100;
    const int ix = dx < 8 ? 8 : dx;
    return {ix, dy, width - 2 * ix, height - 2 * dy};
}

// Action-safe: the larger 2.5% region interactive chrome must stay within.
constexpr ModernUiRect modern_ui_action_safe(int width, int height) noexcept {
    if (width < 64 || height < 64 || width > 16384 || height > 16384) return {};
    const int dx = (width * 5 + 199) / 200;
    const int dy = (height * 5 + 199) / 200;
    return {dx, dy, width - 2 * dx, height - 2 * dy};
}

struct ModernUiScale {
    int factor = 0;       // integer logical->physical scale; 0 means refuse
    ModernUiRect viewport;  // centred letterboxed physical rectangle
};

// Integer-only resolution independence: the largest whole scale of the
// logical canvas that fits the output, centred. 720p 342x224 -> 3x,
// 1080p -> 4x, 2160p -> 9x; 1024x768 256x224 -> 3x.
constexpr ModernUiScale modern_ui_integer_scale(int logical_w, int logical_h,
                                                int out_w, int out_h) noexcept {
    if (logical_w <= 0 || logical_h <= 0 || out_w < logical_w ||
        out_h < logical_h || out_w > 16384 || out_h > 16384) return {};
    int f = out_w / logical_w;
    const int fy = out_h / logical_h;
    if (fy < f) f = fy;
    if (f < 1) return {};
    const int w = logical_w * f, h = logical_h * f;
    return {f, {(out_w - w) / 2, (out_h - h) / 2, w, h}};
}

// Reduced motion: animations resolve to their settled final frame rather
// than being slowed or skipped, so state never depends on a transition.
constexpr unsigned modern_ui_motion_frame(unsigned elapsed, unsigned duration,
                                          bool reduced_motion) noexcept {
    if (reduced_motion || elapsed >= duration) return duration;
    return elapsed;
}

// Focus indicator: a solid bar plus a rectangular outline, so focus is
// readable without colour discrimination or the spinning cursor.
struct ModernUiFocusGeometry {
    ModernUiRect bar;       // leading marker, 3 logical px wide
    std::array<ModernUiRect, 4> outline;  // top, bottom, left, right
    bool valid = false;
};

constexpr ModernUiFocusGeometry modern_ui_focus_geometry(
    const ModernUiRect& row, int scale) noexcept {
    ModernUiFocusGeometry g{};
    if (scale < 1 || scale > 16 || row.width < 8 * scale || row.height < 4 * scale)
        return g;
    const int t = scale;  // 1 logical px outline
    const int bw = 3 * scale > row.width ? row.width : 3 * scale;
    g.bar = {row.x, row.y, bw, row.height};
    g.outline = {ModernUiRect{row.x, row.y, row.width, t},
                 ModernUiRect{row.x, row.bottom() - t, row.width, t},
                 ModernUiRect{row.x, row.y, t, row.height},
                 ModernUiRect{row.right() - t, row.y, t, row.height}};
    g.valid = true;
    return g;
}

// Disabled-control semantics for menu rows. Disabled rows stay visible and
// carry a reason code so the UI can say why; navigation skips them and
// activation is refused, but they are never silently removed.
enum class ModernUiDisabledReason : std::uint8_t {
    None, Locked, NoProfile, NotAvailable, Busy,
};

struct ModernUiRowState {
    bool enabled = true;
    ModernUiDisabledReason reason = ModernUiDisabledReason::None;
};

constexpr bool modern_ui_row_consistent(const ModernUiRowState& r) noexcept {
    return r.enabled == (r.reason == ModernUiDisabledReason::None);
}

// Next enabled row from `index` in direction dir (+1/-1), wrapping. Returns
// -1 when no row is enabled (callers keep focus and show the reason) and
// the original index when it is the only enabled row. Rows must be
// consistent; an inconsistent row is treated as disabled (fail closed).
template <std::size_t N>
constexpr int modern_ui_next_enabled(const std::array<ModernUiRowState, N>& rows,
                                     int index, int dir) noexcept {
    if (N == 0 || N > 64 || (dir != 1 && dir != -1)) return -1;
    const int n = static_cast<int>(N);
    int i = index;
    if (i < 0 || i >= n) i = dir > 0 ? -1 : n;
    for (int step = 0; step < n; ++step) {
        i = ((i + dir) % n + n) % n;
        const auto& r = rows[static_cast<std::size_t>(i)];
        if (r.enabled && modern_ui_row_consistent(r)) return i;
    }
    return -1;
}

// Activation is permitted only on a consistent, enabled row.
constexpr bool modern_ui_may_activate(const ModernUiRowState& r) noexcept {
    return r.enabled && modern_ui_row_consistent(r);
}

}  // namespace ur::product

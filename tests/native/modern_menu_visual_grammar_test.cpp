// Standalone native C++ contract against the production Modern menu helpers.
// No ROM/SDL or separate mock frontend: these same functions are consumed by
// native/product/modern_root_overlay_presenter.hpp.
#include "native/product/modern_menu_visual_grammar.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>

using namespace ur::product;

namespace {
int paints = 0;
int text_draws = 0;
std::uint32_t last_heading_colour = 0u;
int last_heading_scale = 0;
void text_stub(std::uint32_t*, int, int, int, int, const char*,
               std::uint32_t colour, int size) {
    ++text_draws;
    last_heading_colour = colour;
    last_heading_scale = size;
}
void fill(std::uint32_t* pixels, int stride, int height,
          int x, int y, int w, int h, std::uint32_t color) {
    assert(x >= 0 && y >= 0 && w > 0 && h > 0);
    assert(x + w <= stride && y + h <= height);
    ++paints;
    for (int yy = y; yy < y + h; ++yy)
        for (int xx = x; xx < x + w; ++xx)
            pixels[yy * stride + xx] = color;
}
struct Painter {
    decltype(&fill) fill_rect = &fill;
    decltype(&text_stub) draw_text = &text_stub;
};
} // namespace

static_assert(kModernMenuTitleCell == 16, "measured stock type geometry");
static_assert(kModernMenuDetailPitch == 8, "measured small font pitch");
static_assert(kModernMenuStockRowPitch == 24, "measured row pitch");
static_assert(kModernMenuCursorShadowOffset == 7, "measured OBJ shadow");
static_assert(kModernMenuSpinPeriod == 32, "measured arrow period");
static_assert(modern_menu_cursor_chr_tile(0) == 8);
static_assert(modern_menu_cursor_chr_tile(1) == 8);
static_assert(modern_menu_cursor_chr_tile(2) == 4);
static_assert(modern_menu_cursor_chr_tile(30) == 12);
static_assert(modern_menu_cursor_chr_tile(32) == 8);
static_assert(modern_menu_slide_pixels(0, false) == 0);
static_assert(modern_menu_slide_pixels(1, false) == 1);
static_assert(modern_menu_slide_pixels(39, false) == 256);
static_assert(modern_menu_slide_pixels(40, true) == 0);
static_assert(modern_menu_slide_pixels(0, true) == 256);
static_assert(modern_menu_slide_pixels(1, true) == 255);
static_assert(modern_menu_cursor_ease_axis(70, 94) == 76);
static_assert(modern_menu_cursor_ease_axis(94, 70) == 88);
static_assert(modern_menu_cursor_ease_axis(3, 3) == 3);
static_assert(modern_menu_cursor_ease_axis(3, 4) == 4);
static_assert(modern_menu_native_canvas(342, 224));
static_assert(modern_menu_native_canvas(256, 224));
static_assert(!modern_menu_native_canvas(342, 216));
static_assert(!modern_menu_native_canvas(384, 224));
static_assert(!modern_menu_columns(31).two_column);
static_assert(modern_menu_columns(31).primary_width == 0);
static_assert(!modern_menu_columns(256).two_column);
static_assert(modern_menu_columns(256).primary_width == 240);
static_assert(modern_menu_columns(319).primary_width == 303);
static_assert(modern_menu_columns(320).two_column);
static_assert(modern_menu_columns(342).primary_width == 168);
static_assert(modern_menu_columns(342).secondary_x == 184);
static_assert(modern_menu_columns(342).secondary_width == 150);

int main() {
    // Regression fence: all 39 original-strip positions and reverse
    // progression are monotonic and bounded, with no extra phantom frame.
    int prior = 0;
    for (unsigned frame = 1; frame <= 39; ++frame) {
        const int pos = modern_menu_slide_pixels(frame, false);
        assert(pos > prior && pos <= 256);
        assert(modern_menu_slide_pixels(frame, true) == 256 - pos);
        prior = pos;
    }
    assert(prior == 256);

    int cursor = 70;
    for (int f = 0; f != 32; ++f) {
        const int next = modern_menu_cursor_ease_axis(cursor, 94);
        assert(next >= cursor && next <= 94);
        cursor = next;
    }
    assert(cursor == 94);

    constexpr Painter painter{};
    std::uint32_t framebuffer[256 * 224]{};
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 6, "UNIRACERS", 2, 1);
    assert(text_draws == 2);
    assert(last_heading_colour == kModernStockMenuPalette.title_yellow);
    assert(last_heading_scale == 2);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 6, "UNIRACERS", 3, 1);
    assert(text_draws == 2); // invalid text density fails closed

    modern_menu_paint_checker_backdrop(
        painter, framebuffer, 256, 224, 8, 10, 240, 204, 1);
    assert(paints > 30);
    assert(framebuffer[10 * 256 + 8] ==
           kModernStockMenuPalette.background);
    assert(framebuffer[10 * 256 + 24] == 0xE0505050u);
    assert(framebuffer[10 * 256 + 248] == 0u); // no out-of-panel write

    // Draw the focus treatment on top of the same real pixel buffer.
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 13, 50, 168, 17, 1);
    assert(framebuffer[50 * 256 + 13] == kModernMenuCursorLight);
    assert(framebuffer[50 * 256 + 15] == kModernMenuCursorLight);
    assert(framebuffer[50 * 256 + 16] == 0xE0283058u);
    assert(framebuffer[67 * 256 + 13] != kModernMenuCursorLight);

    // Invalid geometry must not dispatch a single out-of-bounds pixel op.
    const int count = paints;
    modern_menu_paint_checker_backdrop(
        painter, framebuffer, 256, 224, 200, 10, 240, 204, 1);
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, -1, 10, 168, 17, 1);
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 8, 10, 168, 17, 5);
    assert(paints == count);
    std::puts("PASS: source-measured Modern menu grammar and native pixel primitives");
    return 0;
}

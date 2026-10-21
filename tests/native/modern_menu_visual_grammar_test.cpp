// Standalone native C++ contract against the production Modern menu helpers.
// No ROM/SDL or separate mock frontend: these same functions are consumed by
// native/product/modern_root_overlay_presenter.hpp.
#include "native/product/modern_menu_visual_grammar.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

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
static_assert(kModernMenuSourceCursorShadow == 0xFF482030u,
              "source shadow uses palette 5 dark maroon, not arrow blue");
// Original states intentionally use different arrow palette highlights.
static_assert(modern_menu_cursor_highlight(ModernMenuSourceCursor::Main)
              == 0xFFA0D0F8u);
static_assert(modern_menu_cursor_highlight(ModernMenuSourceCursor::Rider)
              == 0xFF88C8F0u);
static_assert(modern_menu_cursor_highlight(ModernMenuSourceCursor::Tour)
              == 0xFFF0A088u);
static_assert(modern_menu_cursor_highlight(ModernMenuSourceCursor::Track)
              == 0xFFF0A088u);
static_assert(modern_menu_cursor_highlight(
                  static_cast<ModernMenuSourceCursor>(255))
              == kModernMenuCursorLight);

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
static_assert(modern_menu_observed_heading_word_gap(
                  ModernMenuSourceCursor::Main) == 16);
static_assert(modern_menu_observed_heading_word_gap(
                  ModernMenuSourceCursor::Rider) == 8);
static_assert(modern_menu_observed_heading_word_gap(
                  ModernMenuSourceCursor::Tour) == 16);
static_assert(modern_menu_observed_heading_word_gap(
                  ModernMenuSourceCursor::Track) == 16);
static_assert(kModernMenuObservedRowMoveY.size() == 12);
static_assert(modern_menu_observed_first_row_move_y(0) == 0);
static_assert(modern_menu_observed_first_row_move_y(1) == 6);
static_assert(modern_menu_observed_first_row_move_y(2) == 10);
static_assert(modern_menu_observed_first_row_move_y(9) == 22);
static_assert(modern_menu_observed_first_row_move_y(10) == 22);
static_assert(modern_menu_observed_first_row_move_y(11) == 22);
static_assert(modern_menu_observed_first_row_move_y(12) == 23);
static_assert(modern_menu_observed_first_row_move_y(40) == 23);
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

    // Every frame of the observed original 70->93 Y trajectory is
    // reproducible, including two held frames and the final settle pixel.
    constexpr int expected_y[] = {70,76,80,83,86,88,89,90,91,92,92,92,93};
    for (unsigned frame = 0; frame <= 12; ++frame)
        assert(70 + modern_menu_observed_first_row_move_y(frame)
               == expected_y[frame]);


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
    // The host's fallback 8px glyph cell plus offset shadow must all
    // fit before a single callback. A partial word or bottom spill is
    // forbidden even though the text stub itself would have accepted it.
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 225, 6, "OPTIONS", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 215, "OPTIONS", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 6,
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 248, 0, "A", 1, 1);
    assert(text_draws == 2);
    // Exact right-edge fit includes the host-density shadow.
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 247, 0, "A", 1, 1);
    assert(text_draws == 4);


    // The shared heading is a public host primitive, not a framebuffer
    // clipper. An entire 9-glyph shadowed 2x heading fits at x=111/y=207;
    // moving it only 1px farther right or down must paint neither layer.
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 111, 207, "UNIRACERS", 2, 1);
    assert(text_draws == 6);
    const int bounded_draws = text_draws;
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 112, 207, "UNIRACERS", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 111, 208, "UNIRACERS", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 255, 10, "UNIRACERS", 2, 1);
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 6, "", 2, 1);
    const std::string excessive_heading(129, 'A');
    modern_menu_paint_shadowed_heading(
        painter, framebuffer, 256, 224, 20, 6,
        excessive_heading.c_str(), 2, 1);
    assert(text_draws == bounded_draws);

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

    // The existing root/default remains ice blue; explicit stock-source
    // contexts change only the focus marker, never the dark selection field.
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 13, 75, 168, 17, 1,
        ModernMenuSourceCursor::Rider);
    assert(framebuffer[75 * 256 + 13] == 0xFF88C8F0u);
    assert(framebuffer[75 * 256 + 16] == 0xE0283058u);
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 13, 100, 168, 17, 1,
        ModernMenuSourceCursor::Tour);
    assert(framebuffer[100 * 256 + 13] == 0xFFF0A088u);
    assert(framebuffer[100 * 256 + 16] == 0xE0283058u);
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 13, 125, 168, 17, 1,
        ModernMenuSourceCursor::Track);
    assert(framebuffer[125 * 256 + 13] == 0xFFF0A088u);
    modern_menu_paint_focus_band(
        painter, framebuffer, 256, 224, 13, 150, 168, 17, 1,
        static_cast<ModernMenuSourceCursor>(255));
    assert(framebuffer[150 * 256 + 13] == kModernMenuCursorLight);

    // Wide source and its integer 4x host density use the same source
    // colour context and proportional marker, with no 4:3-style crop.
    constexpr int wide_w = 342;
    constexpr int wide_h = 224;
    std::vector<std::uint32_t> wide(wide_w * wide_h);
    modern_menu_paint_focus_band(
        painter, wide.data(), wide_w, wide_h,
        184, 80, 150, 24, 1, ModernMenuSourceCursor::Tour);
    assert(wide[80 * wide_w + 184] == 0xFFF0A088u);
    assert(wide[80 * wide_w + 186] == 0xFFF0A088u);
    assert(wide[80 * wide_w + 187] == 0xE0283058u);
    assert(wide[80 * wide_w + 334] == 0u); // right safe inset

    constexpr int dense_w = wide_w * 4;
    constexpr int dense_h = wide_h * 4;
    std::vector<std::uint32_t> dense(dense_w * dense_h);
    modern_menu_paint_focus_band(
        painter, dense.data(), dense_w, dense_h,
        184 * 4, 80 * 4, 150 * 4, 24 * 4, 4,
        ModernMenuSourceCursor::Tour);
    assert(dense[(80 * 4) * dense_w + 184 * 4] == 0xFFF0A088u);
    assert(dense[(80 * 4) * dense_w + 184 * 4 + 11] == 0xFFF0A088u);
    assert(dense[(80 * 4) * dense_w + 184 * 4 + 12] == 0xE0283058u);
    assert(dense[(80 * 4) * dense_w + 334 * 4] == 0u);

    // The optional original-font wrapper hands measured 8px/16px word
    // advances to the existing atomic native source-atlas painter.
    // All synthetic pixels below are test-only, never extracted game art.
    std::vector<std::uint32_t> heading_pixels(640 * 16);
    heading_pixels[10 * 16] = 0xFFF8F800u; // synthetic A in slot 10
    ModernMenuSourcePixels heading{
        heading_pixels.data(), heading_pixels.size(), 640, 640, 16
    };
    std::vector<std::uint32_t> source_target(256 * 224);
    assert(modern_menu_paint_source_heading_context(
        heading, source_target.data(), source_target.size(), 256, 224,
        10, 20, "A A", 1, ModernMenuSourceCursor::Rider));
    assert(source_target[20 * 256 + 10] == 0xFFF8F800u);
    assert(source_target[20 * 256 + 34] == 0xFFF8F800u);
    assert(source_target[20 * 256 + 42] == 0u);
    assert(modern_menu_paint_source_heading_context(
        heading, source_target.data(), source_target.size(), 256, 224,
        10, 40, "A A", 1, ModernMenuSourceCursor::Main));
    assert(source_target[40 * 256 + 10] == 0xFFF8F800u);
    assert(source_target[40 * 256 + 42] == 0xFFF8F800u);
    const auto good_heading = source_target;
    assert(!modern_menu_paint_source_heading_context(
        heading, source_target.data(), source_target.size(), 256, 224,
        244, 80, "A A", 1, ModernMenuSourceCursor::Tour));
    assert(source_target == good_heading); // entire text refuses overflow

    // Full sixteen-pose source sheet, one synthetic visible witness pixel
    // per pose. Phase is 2 host menu frames per source pose, no second
    // animation state, with 32-frame wrap and atomically refused clipping.
    std::vector<std::uint32_t> cursor_pixels(624 * 39);
    for (std::uint32_t pose = 0; pose < 16; ++pose)
        cursor_pixels[pose * 39] = 0xFF000000u | (pose + 1u);
    ModernMenuSourcePixels original_cursor{
        cursor_pixels.data(), cursor_pixels.size(), 624, 624, 39
    };
    assert(modern_menu_source_cursor_sheet_complete(original_cursor));
    // A future damaged pose disqualifies even otherwise valid frame zero:
    // this avoids intermittently disappearing cursors during the stock spin.
    cursor_pixels[15 * 39] = 0u;
    assert(!modern_menu_source_cursor_sheet_complete(original_cursor));
    const auto cursor_before_reject = source_target;
    assert(!modern_menu_paint_source_cursor_phase(
        original_cursor, source_target.data(), source_target.size(),
        256, 224, 3, 3, 0, 1));
    assert(source_target == cursor_before_reject);
    cursor_pixels[15 * 39] = 0xFF000010u;
    cursor_pixels[38 * 624 + 15 * 39 + 38] = 0x7F010203u;
    assert(!modern_menu_source_cursor_sheet_complete(original_cursor));
    cursor_pixels[38 * 624 + 15 * 39 + 38] = 0x00010203u;
    assert(!modern_menu_source_cursor_sheet_complete(original_cursor));
    cursor_pixels[38 * 624 + 15 * 39 + 38] = 0u;
    assert(modern_menu_source_cursor_sheet_complete(original_cursor));
    const auto expect_pose = [&](std::uint32_t frame, std::uint32_t colour) {
        source_target.assign(256 * 224, 0u);
        assert(modern_menu_paint_source_cursor_phase(
            original_cursor, source_target.data(), source_target.size(),
            256, 224, 3, 3, frame, 1));
        assert(source_target[3 * 256 + 3] == colour);
        assert(source_target[3 * 256 + 4] == 0u);
    };
    expect_pose(0, 0xFF000001u);
    expect_pose(1, 0xFF000001u);
    expect_pose(2, 0xFF000002u);
    expect_pose(30, 0xFF000010u);
    expect_pose(31, 0xFF000010u);
    expect_pose(32, 0xFF000001u);
    expect_pose(65, 0xFF000001u);
    // Verify all sixteen poses and both host frames of each phase, not
    // only the representative transition and wrap witnesses above.
    for (std::uint32_t pose = 0; pose < 16; ++pose) {
        const auto colour = 0xFF000000u | (pose + 1u);
        expect_pose(pose * 2u, colour);
        expect_pose(pose * 2u + 1u, colour);
    }
    const auto good_cursor = source_target;
    assert(!modern_menu_paint_source_cursor_phase(
        original_cursor, source_target.data(), source_target.size(),
        256, 224, 250, 3, 0, 1));
    assert(source_target == good_cursor);
    cursor_pixels[0] = 0u;
    assert(!modern_menu_paint_source_cursor_phase(
        original_cursor, source_target.data(), source_target.size(),
        256, 224, 3, 3, 0, 1));
    assert(source_target == good_cursor);
    cursor_pixels[0] = 0xFF000001u; // restore before valid 4x use
    assert(modern_menu_source_cursor_sheet_complete(original_cursor));

    // 4x original-raster path is exactly nearest-neighbour: a 1-pixel
    // source font/arrow sample becomes a 4x4 block on the actual dense
    // framebuffer, without stretching away the 7:6 canvas or fabricating
    // source pixels. Both adapters still use the SAME source painter.
    std::vector<std::uint32_t> source_dense(342 * 4 * 224 * 4);
    assert(modern_menu_paint_source_heading_context(
        heading, source_dense.data(), source_dense.size(), 342 * 4, 224 * 4,
        12 * 4, 16 * 4, "A A", 4, ModernMenuSourceCursor::Rider));
    for (int dy = 0; dy < 4; ++dy)
        for (int dx = 0; dx < 4; ++dx) {
            assert(source_dense[(16 * 4 + dy) * (342 * 4) + 12 * 4 + dx]
                   == 0xFFF8F800u);
            assert(source_dense[(16 * 4 + dy) * (342 * 4) +
                                (12 + 24) * 4 + dx] == 0xFFF8F800u);
        }
    assert(source_dense[16 * 4 * (342 * 4) + (12 + 32) * 4] == 0u);
    const auto dense_heading_snapshot = source_dense;
    assert(!modern_menu_paint_source_heading_context(
        heading, source_dense.data(), source_dense.size(), 342 * 4, 224 * 4,
        12 * 4, 16 * 4, "A?A", 4, ModernMenuSourceCursor::Main));
    assert(source_dense == dense_heading_snapshot);

    // Source cursor 4x density, including clipped and translucent
    // rejections. Malformed pixels late in a 39x39 pose do not paint a
    // valid earlier pixel or corrupt the surrounding game image.
    // Separate original blue OBJ and palette-5 maroon shadow survive the
    // same 39x39 atlas composite. Synthetic single source pixels represent
    // each endpoint; the painter must not collapse them into a blue band.
    cursor_pixels[4 * 39 + 38 * 624 + 38] =
        kModernMenuSourceCursorShadow;
    source_dense.assign(342 * 4 * 224 * 4, 0u);
    assert(modern_menu_paint_source_cursor_phase(
        original_cursor, source_dense.data(), source_dense.size(),
        342 * 4, 224 * 4, 184 * 4, 80 * 4, 8, 4));
    for (int dy = 0; dy < 4; ++dy)
        for (int dx = 0; dx < 4; ++dx)
            assert(source_dense[(80 * 4 + dy) * (342 * 4) +
                                184 * 4 + dx] == 0xFF000005u);
    assert(source_dense[80 * 4 * (342 * 4) + 184 * 4 + 4] == 0u);
    for (int dy = 0; dy < 4; ++dy)
        for (int dx = 0; dx < 4; ++dx)
            assert(source_dense[((80 + 38) * 4 + dy) * (342 * 4) +
                                (184 + 38) * 4 + dx]
                   == kModernMenuSourceCursorShadow);
    assert(source_dense[(80 + 38) * 4 * (342 * 4) +
                        (184 + 39) * 4] == 0u);
    const auto good_dense_cursor = source_dense;
    assert(!modern_menu_paint_source_cursor_phase(
        original_cursor, source_dense.data(), source_dense.size(),
        342 * 4, 224 * 4, 305 * 4, 80 * 4, 8, 4));
    assert(source_dense == good_dense_cursor);
    cursor_pixels[4 * 39 + 38 * 624 + 38] = 0x7F112233u;
    assert(!modern_menu_paint_source_cursor_phase(
        original_cursor, source_dense.data(), source_dense.size(),
        342 * 4, 224 * 4, 184 * 4, 80 * 4, 8, 4));
    assert(source_dense == good_dense_cursor);

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

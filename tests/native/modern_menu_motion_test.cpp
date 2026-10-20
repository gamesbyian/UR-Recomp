#include "native/product/modern_menu_motion.hpp"
#include "native/product/modern_menu_stock_hero.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>

namespace {
using namespace ur::product;
static_assert(modern_menu_tick60(0) == 0);
static_assert(modern_menu_tick60(999) == 59);
static_assert(modern_menu_tick60(1000) == 60);
static_assert(modern_menu_tick60(2000) == 120);
static_assert(modern_menu_entrance_remaining(0) == 256);
static_assert(modern_menu_entrance_remaining(39) == 0);
static_assert(modern_menu_cursor_distance(0, 21) == 21);
static_assert(modern_menu_cursor_distance(12, 21) == 0);

struct DrawRecorder {
    int calls = 0;
    int x = 0, y = 0, width = 0, height = 0;
    std::uint32_t colour = 0;
};
DrawRecorder draws;

void fake_fill(std::uint32_t* pixels, int stride, int h, int x, int y,
               int width, int height, std::uint32_t colour) {
    assert(pixels);
    assert(x >= 0 && y >= 0 && x + width <= stride && y + height <= h);
    ++draws.calls;
    draws.x = x; draws.y = y;
    draws.width = width; draws.height = height;
    draws.colour = colour;
    for (int yy = y; yy < y + height; ++yy)
        for (int xx = x; xx < x + width; ++xx)
            pixels[static_cast<std::size_t>(yy) * stride + xx] = colour;
}
void fake_stroke(std::uint32_t*, int, int, int, int, int, int,
                 std::uint32_t) {}
void fake_text(std::uint32_t*, int, int, int, int, const char*,
               std::uint32_t, int) {}
struct FakePainter {
    decltype(&fake_fill) fill_rect = &fake_fill;
    decltype(&fake_stroke) stroke_rect = &fake_stroke;
    decltype(&fake_text) draw_text = &fake_text;
    constexpr bool valid() const noexcept { return true; }
};
void test_motion() {
    // A native capture may freeze one exact UI tick without changing the
    // guest-frame clock. Invalid numeric strings cannot hijack the clock.
    assert(modern_menu_resolve_test_tick60(123u, nullptr) == 123u);
    assert(modern_menu_resolve_test_tick60(123u, "") == 123u);
    assert(modern_menu_resolve_test_tick60(123u, "0") == 0u);
    assert(modern_menu_resolve_test_tick60(123u, "000041") == 41u);
    assert(modern_menu_resolve_test_tick60(123u,
        "18446744073709551615") == UINT64_MAX);
    assert(modern_menu_resolve_test_tick60(123u,
        "18446744073709551616") == 123u);
    assert(modern_menu_resolve_test_tick60(123u, "12x") == 123u);
    assert(modern_menu_resolve_test_tick60(123u, "+12") == 123u);
    assert(modern_menu_resolve_test_tick60(123u, "-12") == 123u);
    assert(modern_menu_resolve_test_tick60(123u, " 12") == 123u);
    ModernMenuMotionState state{};
    auto pose = advance_modern_menu_motion(state, {1000, 0, true, false});
    assert(pose.visible && pose.selection == 0);
    assert(pose.cursor_spin_phase == 4); // 1000/2 mod 16
    assert(pose.entrance_distance_px == 256);
    assert(pose.cursor_remainder_px == 0);
    const auto exact = advance_modern_menu_motion(
        state, {1000, 0, true, false});
    assert(exact.cursor_spin_phase == pose.cursor_spin_phase);
    assert(exact.entrance_distance_px == pose.entrance_distance_px);

    pose = advance_modern_menu_motion(state, {1001, 1, true, false});
    assert(pose.selection == 1);
    // The original cursor responds in the press frame, rather than lagging
    // one host draw: measured 6/23 of the modern 21px row is already travelled.
    assert(pose.cursor_remainder_px == -16);
    pose = advance_modern_menu_motion(state, {1002, 1, true, false});
    assert(pose.cursor_remainder_px < 0 && pose.cursor_remainder_px > -21);
    pose = advance_modern_menu_motion(state, {1013, 1, true, false});
    assert(pose.cursor_remainder_px == 0);

    // Selection response interrupts the earlier animation immediately,
    // including a new selection on the very next 60Hz tick.
    pose = advance_modern_menu_motion(state, {1014, 2, true, false});
    assert(pose.cursor_remainder_px == -16);
    pose = advance_modern_menu_motion(state, {1015, 1, true, false});
    // Physical cursor continued from near pixel 30 and immediately eased
    // toward destination 1 (pixel 21), instead of jumping from target 2.
    assert(pose.cursor_remainder_px == 7);
    pose = advance_modern_menu_motion(state, {1015, 2, true, false});
    assert(pose.cursor_remainder_px == -10);
    pose = advance_modern_menu_motion(state, {1015, 1, true, false});
    assert(pose.cursor_remainder_px == 8);
    pose = advance_modern_menu_motion(state, {1016, 4, true, false});
    assert(pose.selection == 4 && pose.cursor_remainder_px == 0);
    pose = advance_modern_menu_motion(state, {1017, 0, true, false});
    assert(pose.selection == 0 && pose.cursor_remainder_px == 0);

    // No audio/guest/frame side effects. A hidden surface resets the
    // screen-entry animation and cannot accrue offscreen motion.
    pose = advance_modern_menu_motion(state, {2000, 0, false, false});
    assert(!pose.visible && !state.visible);
    pose = advance_modern_menu_motion(state, {3000, 2, true, false});
    assert(pose.entrance_distance_px == 256);
    pose = advance_modern_menu_motion(state, {3040, 2, true, false});
    assert(pose.entrance_distance_px == 0);
    pose = advance_modern_menu_motion(state, {50, 2, true, false});
    assert(pose.entrance_distance_px == 256); // clock rollover

    pose = advance_modern_menu_motion(state, {51, 3, true, true});
    assert(pose.selection == 3 && pose.reduced_motion);
    assert(pose.cursor_spin_phase == 0);
    assert(pose.cursor_remainder_px == 0);
    assert(pose.hero_bob_px == 0 && pose.hero_lean_px == 0);
    assert(pose.entrance_distance_px == 0);
    pose = advance_modern_menu_motion(state, {52, 3, true, false});
    assert(pose.selection == 3);
    assert(pose.cursor_remainder_px == 0);
    assert(pose.entrance_distance_px == 0);
    assert(pose.hero_frame_ordinal == 7);
    // A genuine new selection after motion is re-enabled animates again.
    pose = advance_modern_menu_motion(state, {53, 4, true, false});
    assert(pose.selection == 4);
    assert(pose.cursor_remainder_px == -16);
    assert(pose.entrance_distance_px == 0);
    assert(pose.hero_frame_ordinal == 0);
    // Even if reduced motion is toggled inside an incomplete entrance, the
    // previous 39-frame sweep does not suddenly restart when re-enabled.
    ModernMenuMotionState reentry{};
    pose = advance_modern_menu_motion(reentry, {1, 0, true, false});
    assert(pose.entrance_distance_px == 256);
    pose = advance_modern_menu_motion(reentry, {2, 0, true, true});
    assert(pose.entrance_distance_px == 0);
    pose = advance_modern_menu_motion(reentry, {3, 0, true, false});
    assert(pose.entrance_distance_px == 0);
    assert(pose.cursor_remainder_px == 0);
}
void test_raster() {
    // Actual source/modern host geometry: 256x224 compact and 342x224
    // widescreen, each at 1x and 4x. A fictitious 384-wide logical panel
    // must not be mistaken for the shipping 16:9 composition.
    for (int logical_width : {256, 342}) for (int scale : {1, 4}) {
        const int w = logical_width * scale;
        const int h = 224 * scale;
        const int panel_w = logical_width == 342 ? 320 : 240;
        const HostOverlayRect panel{
            (w - panel_w * scale) / 2, 10 * scale,
            panel_w * scale, 204 * scale};
        std::vector<std::uint32_t> pixels(
            static_cast<std::size_t>(w) * h, 0xFF111111u);
        ModernMenuMotionState state{};
        auto pose = advance_modern_menu_motion(
            state, {100, 1, true, false});
        draws = {};
        assert(paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, scale, panel, pose));
        assert(draws.calls == 1);
        assert(draws.x == panel.x + 5 * scale);
        assert(draws.y == panel.y + (57 + 21) * scale);
        assert(draws.width == 2 * scale);
        assert(draws.height == 12 * scale);
        assert(draws.colour == pixels[
            static_cast<std::size_t>(draws.y) * w + draws.x]);
        const auto first_pixel = pixels[
            static_cast<std::size_t>(draws.y) * w + draws.x];
        assert(first_pixel != 0xFF111111u);
        assert(pixels[0] == 0xFF111111u); // framebuffer elsewhere untouched

        // Original blue cursor remains blue throughout the 32-frame phase:
        // visual breathing is a small geometric inset, never flashing color.
        pose.cursor_spin_phase = 8;
        draws = {};
        assert(paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, scale, panel, pose));
        assert(draws.colour == kModernStockMenuPalette.cursor_blue);
        assert(draws.y == panel.y + (57 + 21 + 1) * scale);
        assert(draws.height == 10 * scale);
        pose.reduced_motion = true;
        draws = {};
        assert(paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, scale, panel, pose));
        assert(draws.y == panel.y + (57 + 21) * scale);
        assert(draws.height == 12 * scale);
        pose.reduced_motion = false;

        pose.visible = false;
        assert(!paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, scale, panel, pose));
        assert(draws.calls == 1);
        pose.visible = true;
        assert(!paint_modern_menu_selection_motion(
            FakePainter{}, nullptr, w, h, scale, panel, pose));
        assert(!paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, 0, panel, pose));
        const HostOverlayRect offscreen{w - 3, 0, 40, 204};
        assert(!paint_modern_menu_selection_motion(
            FakePainter{}, pixels.data(), w, h, scale, offscreen, pose));
    }
}

void test_source_stock_hero() {
    // Test pixels are deliberately synthetic and never supplied to the
    // running game. Only source-verified reconstructed original poses can
    // pass the real host consumer.
    std::vector<std::uint32_t> first(kModernMenuStockHeroPixels, 0u);
    std::vector<std::uint32_t> second(kModernMenuStockHeroPixels, 0u);
    constexpr std::size_t kCentre = 32u * 64u + 32u;
    first[kCentre] = 0xffff0000u;
    second[kCentre] = 0xff0000ffu;
    ModernMenuStockHeroFrame frames[2]{
        {first.data(), first.size(), 0x0541,
         modern_menu_stock_hero_digest(first.data(), first.size()), true},
        {second.data(), second.size(), 0x0540,
         modern_menu_stock_hero_digest(second.data(), second.size()), true},
    };
    ModernMenuStockHeroSequence sequence{frames, 2, true};
    assert(modern_menu_stock_hero_sequence_eligible(sequence));
    ModernMenuMotionState animator{};
    auto pose = advance_modern_menu_motion(animator, {0, 0, true, false});
    std::vector<std::uint32_t> output(256u * 224u, 0xff101010u);
    const HostOverlayRect safe{0, 0, 256, 224};
    const ModernMenuStockHeroPlacement placement{60, 40, 2};
    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, placement, sequence, pose) ==
        ModernMenuStockHeroDraw::Drawn);
    assert(output[static_cast<std::size_t>(40 + 64) * 256u + 60u + 64u]
           == 0xffff0000u);
    assert(output[0] == 0xff101010u);

    pose = advance_modern_menu_motion(animator, {1, 0, true, false});
    assert(pose.hero_frame_ordinal == 1);
    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, placement, sequence, pose) ==
        ModernMenuStockHeroDraw::Drawn);
    assert(output[static_cast<std::size_t>(40 + 64) * 256u + 60u + 64u]
           == 0xff0000ffu);

    // This source sequence is one-shot, not a guessed seamless idle loop.
    pose = advance_modern_menu_motion(animator, {100, 0, true, false});
    assert(pose.hero_frame_ordinal == 7);
    pose = advance_modern_menu_motion(animator, {101, 0, true, false});
    assert(pose.hero_frame_ordinal == 7);
    pose = advance_modern_menu_motion(animator, {102, 1, true, false});
    assert(pose.hero_frame_ordinal == 0);
    // A wrong digest or unproven order never touches a pixel.
    const auto before = output;
    frames[1].source_argb_digest ^= 1u;
    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, placement, sequence, pose) ==
        ModernMenuStockHeroDraw::Unverified);
    assert(output == before);
    frames[1].source_argb_digest ^= 1u;
    sequence.original_pose_order_verified = false;
    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, placement, sequence, pose) ==
        ModernMenuStockHeroDraw::Unverified);
    assert(output == before);
    sequence.original_pose_order_verified = true;

    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, {200, 40, 2}, sequence, pose) ==
        ModernMenuStockHeroDraw::OutOfBounds);
    assert(output == before);
    assert(paint_modern_menu_stock_hero(
        nullptr, 256, 224, safe, placement, sequence, pose) ==
        ModernMenuStockHeroDraw::OutOfBounds);

    auto quiet = advance_modern_menu_motion(
        animator, {12, 0, true, true});
    assert(quiet.hero_frame_ordinal == 0);
    assert(quiet.hero_bob_px == 0 && quiet.hero_lean_px == 0);
    assert(paint_modern_menu_stock_hero(
        output.data(), 256, 224, safe, placement, sequence, quiet) ==
        ModernMenuStockHeroDraw::Drawn);
    assert(output[static_cast<std::size_t>(40 + 64) * 256u + 60u + 64u]
           == 0xffff0000u);

    // An actual 4x-density native compositing buffer, not a resized mock.
    std::vector<std::uint32_t> wide(1536u * 896u, 0xff101010u);
    (void)advance_modern_menu_motion(
        animator, {18, 0, true, false});
    auto wide_pose = advance_modern_menu_motion(
        animator, {26, 0, true, false});
    assert(wide_pose.hero_frame_ordinal == 7);
    assert(paint_modern_menu_stock_hero(
        wide.data(), 1536, 896, {0, 0, 1536, 896},
        {650, 280, 4}, sequence, wide_pose) ==
        ModernMenuStockHeroDraw::Drawn);
    assert(wide[static_cast<std::size_t>(
                280 + wide_pose.hero_bob_px * 4 + 128) * 1536u +
                static_cast<std::size_t>(
                    650 + wide_pose.hero_lean_px * 4 + 128)] ==
           0xff0000ffu);
    assert(wide[0] == 0xff101010u);

    // Alpha-safe overscan: the padded 64x64 raster is larger than the 4x
    // viewport but every opaque pixel is still faithfully visible.
    std::vector<std::uint32_t> cropped(256u * 224u, 0xff101010u);
    assert(paint_modern_menu_stock_hero(
        cropped.data(), 256, 224, safe, {100, -50, 4},
        sequence, quiet) == ModernMenuStockHeroDraw::Drawn);
    assert(cropped[static_cast<std::size_t>(78) * 256u + 228u] ==
           0xffff0000u);
    assert(cropped[0] == 0xff101010u);

    // Opaque overscan in EVEN ANOTHER registered source frame rejects the
    // entire image before touching any frame-0 pixels.
    const auto unchanged = cropped;
    second[63u * 64u + 63u] = 0xffffffffu;
    frames[1].source_argb_digest =
        modern_menu_stock_hero_digest(second.data(), second.size());
    assert(paint_modern_menu_stock_hero(
        cropped.data(), 256, 224, safe, {100, -50, 4},
        sequence, quiet) == ModernMenuStockHeroDraw::OutOfBounds);
    assert(cropped == unchanged);
    second[63u * 64u + 63u] = 0u;
    frames[1].source_argb_digest =
        modern_menu_stock_hero_digest(second.data(), second.size());
}
} // namespace

int main() {
    test_motion();
    test_raster();
    test_source_stock_hero();
    std::puts("PASS: Modern native menu motion 60Hz, 4:3/16:9, reduced motion");
    return 0;
}

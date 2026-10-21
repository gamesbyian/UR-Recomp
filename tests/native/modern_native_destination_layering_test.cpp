// Regression for real frame compositing: the main-menu focus band and root
// prompts must not leak through a fully opened destination. The host calls the
// shared shell with a presentation-only view copy, then the child with the
// *unmodified* product view. This pixel fixture runs that exact draw order;
// it neither invents input nor claims native SDL/artistic acceptance.
#include "native/product/modern_native_destination_presenter.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

using namespace ur::product;

namespace {
void fill(std::uint32_t* dst, int stride, int screen_h,
          int x, int y, int w, int h, std::uint32_t colour) {
    assert(dst && stride > 0 && screen_h > 0);
    assert(x >= 0 && y >= 0 && w > 0 && h > 0);
    assert(w <= stride - x && h <= screen_h - y);
    for (int row = y; row < y + h; ++row)
        std::fill_n(dst + row * stride + x, w, colour);
}
void stroke(std::uint32_t* dst, int stride, int screen_h,
            int x, int y, int w, int h, std::uint32_t colour) {
    fill(dst, stride, screen_h, x, y, w, 1, colour);
    fill(dst, stride, screen_h, x, y + h - 1, w, 1, colour);
    fill(dst, stride, screen_h, x, y, 1, h, colour);
    fill(dst, stride, screen_h, x + w - 1, y, 1, h, colour);
}
void text(std::uint32_t* dst, int stride, int screen_h,
          int x, int y, const char* label, std::uint32_t colour, int scale) {
    assert(label && scale > 0 && scale <= 8);
    // A block per displayed native glyph provides a conservative ink
    // envelope. This deliberate synthetic raster only tests draw ordering
    // and occlusion, not source ROM font likeness.
    const std::size_t cells = std::strlen(label);
    assert(cells < 128);
    if (!cells) return;
    fill(dst, stride, screen_h, x, y, static_cast<int>(cells) * 8 * scale,
         8 * scale, colour);
}
void exercise(int screen_w, int panel_w) {
    constexpr int height = 224;
    constexpr ModernRootOverlayPainter painter{&fill, &stroke, &text};
    const HostOverlayRect root{(screen_w - panel_w) / 2, 10, panel_w, 204};
    const auto palette = kModernStockMenuPalette;
    std::vector<std::uint32_t> pixels(static_cast<std::size_t>(screen_w) * height);
    // Exercise root compositing across every materially different child
    // family, including alternate read-only / help / join / next-boot
    // variants that previously had no raster-level occlusion witness.
    std::array<const char*, 10> names{{
        "options", "practice", "records", "multiplayer", "profile",
        "options-help", "practice-entering", "records-2p",
        "two-seat-join", "profile-switch"
    }};

    for (int which = 0; which < static_cast<int>(names.size()); ++which) {
        std::fill(pixels.begin(), pixels.end(), 0u);
        ModernRootOverlayView actual{};
        actual.racer_name = "NO PROFILE";
        if (which == 0) {
            actual.options_open = true;
            actual.options_row_count = 1;
            actual.options_rows[0] = {"VOLUME", "90%", true};
        } else if (which == 1) {
            actual.practice_picker_open = true;
            actual.practice_course_name = "Zoom Zoo";
            actual.practice_courses_open = 20;
        } else if (which == 2) {
            actual.read_only_records_open = true;
            actual.records_status = "NO RUNS YET";
        } else if (which == 3) {
            actual.unbound_two_player_warning_open = true;
        } else if (which == 4) {
            actual.first_racer_open = true;
            actual.first_racer_preset_name = "MIKE";
        } else if (which == 5) {
            actual.options_open = true;
            actual.options_controls_help = true;
        } else if (which == 6) {
            actual.practice_launch_pending = true;
            actual.practice_course_name = "Dragster";
        } else if (which == 7) {
            actual.read_only_records_open = true;
            actual.read_only_records_two_player = true;
            actual.read_only_records_pages_available = true;
            actual.records_status = "MY 2P 1";
            actual.records_recent = "W 1 L 0 D 0";
            actual.records_detail = "LAST 01 WIN 00:28.76";
        } else if (which == 8) {
            actual.two_seat_join_open = true;
            actual.join_p1_name = "MIKE";
            actual.join_p2_name = "MARTIN";
            actual.join_p1_stock = "MIKE";
            actual.join_p2_stock = "MARTIN";
            actual.join_p1_confirmed = true;
        } else {
            actual.first_racer_open = true;
            actual.first_racer_is_switch = true;
            actual.first_racer_preset_name = "MARTIN";
            actual.first_racer_created = true;
        }
        auto shell = actual;
        shell.practice_picker_open = false;
        shell.practice_launch_pending = false;
        shell.options_open = false;
        shell.read_only_records_open = false;
        shell.two_seat_join_open = false;
        shell.first_racer_open = false;
        shell.unbound_two_player_warning_open = false;
        assert(render_modern_root_overlay(
            painter, pixels.data(), screen_w, height,
            1, panel_w, root, shell));
        const auto sample = [&](int dx, int dy) {
            return pixels[static_cast<std::size_t>(root.y + dy) * screen_w
                          + root.x + dx];
        };
        // Prove the shell ACTUALLY rendered a bright selected band and both
        // rows of its stock root controller bar before the child overpaints.
        const auto exposed_cursor_ink = sample(6, 60);
        const auto identity_ink = sample(15, 42);
        // Main's shared root now paints profile identity in the measured
        // checker-legible grey (not the old low-contrast stock UI grey).
        // Preserve those actual source-root glyph pixels under the child.
        assert(identity_ink == kModernMenuCheckerLegibleGrey);
        const auto exposed_footer_ink = sample(11, 195);
        assert(exposed_cursor_ink != palette.header_band);
        assert(exposed_footer_ink != palette.background);
        assert(render_modern_native_destination(
            painter, pixels.data(), screen_w, height,
            1, panel_w, root, actual));
        // The child header covers the old blue bar even in the tiny left
        // margin. Its full-height solid body also removes the root footer.
        assert(sample(6, 60) == palette.header_band);
        assert(sample(11, 195) == palette.background);
        // Only a single blue pixel happened to be checked originally.
        // Every narrow edge gutter now has to be fully occluded, from just
        // below the preserved identity baseline through the root footer.
        // This catches focus/legend residues regardless of which row moves.
        for (int yy = 47; yy < 202; ++yy) {
            assert(sample(1, yy) == palette.background);
            assert(sample(root.width - 2, yy) == palette.background);
        }
        // Racer identity is at root y+36 with 8 original-sized glyph rows.
        // Masking from y+40 severed its bottom half in real SDL captures.
        assert(sample(15, 42) == identity_ink);
        // Outer root border remains undamaged by a properly inset child.
        assert(sample(0, 203) == palette.frame_grey);
        std::printf("occlusion %s %dx224 root=%d\n",
            names[static_cast<std::size_t>(which)], screen_w, root.width);
    }
}
}  // namespace

int main() {
    exercise(256, 240);
    exercise(342, 320);
    std::puts("PASS: destination occlusion on compact and native-wide shells");
}

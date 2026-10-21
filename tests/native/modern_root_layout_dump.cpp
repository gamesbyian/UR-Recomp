// Layout harness: renders the production Modern root presenter into an
// opaque RGB_ALPHA P7 on the native logical canvas (256x224 or 342x224),
// source-over blending the presenter's real fill alphas. Text is rasterised
// as a conservative solid 7x7 box per non-space 8x8 cell (the real 8x8 glyph
// font belongs to the external pinned framework), so this verifies GEOMETRY,
// clipping, focus and exact text colours of the production layout, never the
// glyph art.
// Usage: modern_root_layout_dump <width 256|342> <out.p7> [root|practice|
//        join|options|records|warning|first-racer, optionally prefixed
//        "dest-" for the native-host composition: root shell + separate
//        destination presenter] [--audit]
#include "native/product/modern_native_destination_presenter.hpp"
#include "native/product/modern_root_overlay_presenter.hpp"
#include "native/product/modern_ui_access.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
int g_h = 224;
bool g_audit = false;
bool g_low = false;
const char* g_variant = "root";
int g_width = 0;
// Legibility audit: contrast of each text draw against the WORST pixel
// already on the surface under its 8x8 cells (font independent).
struct Box { int x, y, w, h; std::string t; };
std::vector<Box> g_boxes;
// Geometry audit: every text box inside the action-safe region and no two
// differently-worded text boxes overlapping (duplicates are shadows).
void audit_geometry(int stride, int x, int y, const char* t, int scale) {
    const auto safe = ur::product::modern_ui_action_safe(stride, g_h);
    const ur::product::ModernUiRect box{x, y,
        static_cast<int>(std::string(t).size()) * 8 * scale, 8 * scale};
    if (box.width > 0 && !ur::product::modern_ui_rect_contains(safe, box)) {
        g_low = true;
        std::printf("CLIP %s %d \"%s\" box=%d,%d,%d,%d\n", g_variant, g_width,
                    t, box.x, box.y, box.width, box.height);
    }
    for (const auto& o : g_boxes) {
        if (o.t == t) continue;
        if (x < o.x + o.w && o.x < x + box.width && y < o.y + o.h && o.y < y + box.height) {
            g_low = true;
            std::printf("OVERLAP %s %d \"%s\" with \"%s\"\n", g_variant, g_width,
                        t, o.t.c_str());
        }
    }
    g_boxes.push_back({x, y, box.width, box.height, t});
}
void audit_text(const std::uint32_t* p, int stride, int x, int y,
                const char* t, std::uint32_t c, int scale) {
    // Drop shadows are decorative duplicates of a legible heading.
    if (c == ur::product::kModernStockMenuPalette.shadow_black) return;
    std::uint32_t worst = 100000u, worst_bg = 0;
    for (int i = 0; t[i]; ++i) {
        if (t[i] == ' ') continue;
        for (int yy = y; yy < y + 8 * scale; ++yy)
            for (int xx = x + i * 8 * scale; xx < x + (i + 1) * 8 * scale; ++xx) {
                if (xx < 0 || yy < 0 || xx >= stride || yy >= g_h) continue;
                const auto bg = p[yy * stride + xx];
                const auto r = ur::product::modern_ui_contrast_x100(c, bg);
                if (r < worst) { worst = r; worst_bg = bg; }
            }
    }
    if (worst < ur::product::kModernUiTextContrastX100) {
        g_low = true;
        std::printf("LOW %s %d \"%s\" fg=%08X bg=%08X ratio=%u.%02u\n",
                    g_variant, g_width, t, c, worst_bg, worst / 100, worst % 100);
    }
}
std::uint32_t blend(std::uint32_t dst, std::uint32_t src) {
    const std::uint32_t a = src >> 24;
    auto ch = [&](int shift) {
        const std::uint32_t s = (src >> shift) & 255u, d = (dst >> shift) & 255u;
        return (s * a + d * (255u - a) + 127u) / 255u;
    };
    return 0xFF000000u | (ch(16) << 16) | (ch(8) << 8) | ch(0);
}
void put(std::uint32_t* p, int stride, int x, int y, std::uint32_t c) {
    if (x < 0 || y < 0 || x >= stride || y >= g_h) return;
    p[y * stride + x] = blend(p[y * stride + x], c);
}
void fill(std::uint32_t* p, int stride, int, int x, int y, int w, int h,
          std::uint32_t c) {
    // A near-opaque panel masks earlier text at least half beneath it.
    if (g_audit && (c >> 24) >= 0xE0u)
        g_boxes.erase(std::remove_if(g_boxes.begin(), g_boxes.end(),
            [&](const Box& b) {
                const int ix = std::max(0, std::min(b.x + b.w, x + w) - std::max(b.x, x));
                const int iy = std::max(0, std::min(b.y + b.h, y + h) - std::max(b.y, y));
                return ix * iy * 2 >= b.w * b.h;
            }), g_boxes.end());
    for (int yy = y; yy < y + h; ++yy)
        for (int xx = x; xx < x + w; ++xx) put(p, stride, xx, yy, c);
}
void stroke(std::uint32_t* p, int stride, int, int x, int y, int w, int h,
            std::uint32_t c) {
    fill(p, stride, 0, x, y, w, 1, c);
    fill(p, stride, 0, x, y + h - 1, w, 1, c);
    fill(p, stride, 0, x, y, 1, h, c);
    fill(p, stride, 0, x + w - 1, y, 1, h, c);
}
void text(std::uint32_t* p, int stride, int, int x, int y, const char* t,
          std::uint32_t c, int scale) {
    if (g_audit) {
        audit_text(p, stride, x, y, t, c, scale);
        audit_geometry(stride, x, y, t, scale);
    }
    for (int i = 0; t[i]; ++i)
        if (t[i] != ' ')
            fill(p, stride, 0, x + i * 8 * scale, y, 7 * scale, 7 * scale, c);
}
}  // namespace

int main(int argc, char** argv) {
    if (argc < 3 || argc > 5) return 2;
    g_audit = argc == 5 && std::string(argv[4]) == "--audit";
    std::string variant = argc >= 4 ? argv[3] : "root";
    const bool dest = variant.rfind("dest-", 0) == 0;
    if (dest) variant = variant.substr(5);
    g_variant = argc >= 4 ? argv[3] : "root";
    const int width = std::atoi(argv[1]);
    if (width != 256 && width != 342) return 2;
    g_width = width;
    std::vector<std::uint32_t> px(static_cast<std::size_t>(width) * g_h, 0xFF000000u);
    const int panel_w = width == 342 ? 320 : 240;
    const HostOverlayRect rect{(width - panel_w) / 2, 10, panel_w, 204};
    const ModernRootOverlayPainter painter{&fill, &stroke, &text};
    ModernRootOverlayView view{};
    if (variant == "practice") {
        view.practice_picker_open = true;
        view.practice_course_name = "ZOO";
        view.practice_tour_name = "TOUR 1";
        view.practice_kind_label = "RACE";
        view.practice_courses_open = 3;
    } else if (variant == "join") {
        view.two_seat_join_open = true;
        view.join_p1_name = "IAN";
        view.join_p2_name = "GUEST";
        view.join_p1_stock = "BLADE";
        view.join_p2_stock = "AXEL";
    } else if (variant == "options") {
        view.options_open = true;
        view.options_row_count = 3;
        view.options_rows[0] = {"WINDOW", "1280X720", true};
        view.options_rows[1] = {"SCALE", "AUTO", true};
        view.options_rows[2] = {"CONTROLS", "", false};
    } else if (variant == "records") {
        view.read_only_records_open = true;
        view.records_status = "NO RUNS YET";
        view.records_recent = "COMPLETE A RACE";
    } else if (variant == "warning") {
        view.unbound_two_player_warning_open = true;
    } else if (variant == "first-racer") {
        view.first_racer_open = true;
        view.first_racer_preset_name = "BLADE";
    } else if (variant != "root") {
        return 2;
    }
    ModernRootOverlayView shell = view;
    if (dest) {
        // Native host composition: modal flags are cleared for the shell,
        // then the separate destination presenter paints the child.
        shell.practice_picker_open = shell.practice_launch_pending = false;
        shell.options_open = shell.read_only_records_open = false;
        shell.two_seat_join_open = shell.first_racer_open = false;
        shell.unbound_two_player_warning_open = false;
    }
    if (!render_modern_root_overlay(painter, px.data(), width, g_h, 1, panel_w,
                                    rect, shell)) {
        std::fprintf(stderr, "root render refused\n");
        return 1;
    }
    if (dest && !render_modern_native_destination(painter, px.data(), width, g_h,
                                                  1, panel_w, rect, view)) {
        std::fprintf(stderr, "destination render refused\n");
        return 1;
    }
    if (g_audit) return g_low ? 3 : 0;
    std::FILE* f = std::fopen(argv[2], "wb");
    if (!f) return 1;
    std::fprintf(f, "P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n", width, g_h);
    for (auto v : px) {
        const unsigned char rgba[4] = {static_cast<unsigned char>(v >> 16),
            static_cast<unsigned char>(v >> 8), static_cast<unsigned char>(v), 255};
        std::fwrite(rgba, 1, 4, f);
    }
    std::fclose(f);
    return 0;
}

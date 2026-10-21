// The native paused-menu painter: OPTIONS is now wired (no SOON label) while
// the still-unconnected rows stay explicitly disabled, and the paused Options
// panel reuses the shared modal without ever stepping the guest.
#include "native/product/modern_pause_overlay_presenter.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::vector<std::string> painted;
int legible_pause_status_draws = 0;
std::vector<std::pair<std::string, std::uint32_t>> colour_draws;
int active_w = 0;
int active_h = 0;
void check_bounds(int x, int y, int w, int h) {
    if (!active_w) return;
    assert(x >= 0 && y >= 0 && w > 0 && h > 0);
    assert(x <= active_w - w && y <= active_h - h);
}
struct DrawRect { int x, y, w, h; };
std::vector<DrawRect> fill_rects;
void fill(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t) {
    check_bounds(x,y,w,h);
    fill_rects.push_back({x,y,w,h});
}
void stroke(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t) {
    check_bounds(x,y,w,h);
}
void text(std::uint32_t*,int,int,int x,int y,const char* t,std::uint32_t colour,int scale) {
    check_bounds(x,y,static_cast<int>(std::string(t).size()) * 8 * scale,8 * scale);
    painted.emplace_back(t);
    colour_draws.emplace_back(t, colour);
    if (std::string(t) == "GAME PAUSED" &&
        colour == kModernMenuCheckerLegibleGrey)
        ++legible_pause_status_draws;
}
bool contains(const std::string& s) {
    for (const auto& item : painted) if (item == s) return true;
    return false;
}
int count(const std::string& s) {
    int n = 0;
    for (const auto& item : painted) if (item == s) ++n;
    return n;
}
bool drawn_in(const std::string& label, std::uint32_t colour) {
    for (const auto& d : colour_draws)
        if (d.first == label && d.second == colour) return true;
    return false;
}
}  // namespace

int main() {
    static std::uint32_t pixels[512 * 448]{};
    constexpr ModernRootOverlayPainter painter{&fill, &stroke, &text};
    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    active_w = 512;
    active_h = 448;

    // Pause panel: Options connected; Controls, Run Data, Records and Exit
    // remain SOON (4 labels), Resume/Restart/Options/Quit carry none.
    assert(render_native_modern_pause_overlay(
        painter, pixels, 512, 512, 448, menu, true));
    assert(contains("OPTIONS") && contains("RESUME") && contains("QUIT DESKTOP"));
    assert(contains("GAME PAUSED"));
    assert(!contains("PAUSED - GUEST FROZEN"));
    assert(legible_pause_status_draws == 1);
    assert(count("SOON") == 4);
    // Focus can land on a not-yet-wired row. Its label and SOON tag must stay
    // readable on the light focus bar (dark focus text, never dim grey).
    for (int source_w : {256, 342}) {
        active_w = source_w;
        active_h = 224;
        UrModernPauseMenu focused{};
        ur_modern_pause_menu_reset(&focused);
        focused.selected = UR_MODERN_PAUSE_CONTROLS;
        painted.clear();
        colour_draws.clear();
        assert(render_native_modern_pause_overlay(
            painter, pixels, source_w, source_w, 224, focused, true));
        assert(drawn_in("CONTROLS", kModernStockMenuPalette.shadow_black));
        assert(!drawn_in("CONTROLS", kModernStockMenuPalette.secondary_grey));
        assert(drawn_in("SOON", kModernStockMenuPalette.shadow_black));
        assert(drawn_in("RUN DATA", kModernStockMenuPalette.secondary_grey));
    }
    active_w = 512;
    active_h = 448;
    painted.clear();
    // Compact prepared-source frames must paint directly into their real
    // framebuffer. Keep all eight rows and disabled/selection policies;
    // a 1280x720 SDL window alone cannot substitute for these source sizes.
    for (int source_w : {256,342}) {
        active_w = source_w;
        active_h = 224;
        painted.clear();
        assert(render_native_modern_pause_overlay(
            painter,pixels,source_w,source_w,224,menu,true));
        assert(contains("GAME PAUSED"));
        assert(contains("RESTART RACE") && contains("QUIT DESKTOP"));
        assert(count("SOON") == 4);
        assert(contains("B/ESC BACK  START RESUME"));
        assert(!contains("PAUSED - GUEST FROZEN"));
        painted.clear();
        assert(render_native_modern_pause_overlay(
            painter,pixels,source_w,source_w,224,menu,false));
        assert(count("SOON") == 5); // Restart is disabled as before
        assert(contains("GAME PAUSED"));
    }
    // A host lifecycle pause names its reason in place of the subtitle, in
    // every panel size, inside the panel; without one nothing changes.
    struct StatusCase { int w, h, panel_x, panel_w; };
    constexpr StatusCase status_cases[] = {
        {256,224,8,240}, {342,224,11,320}, {512,448,56,400}};
    for (const auto& c : status_cases) {
        active_w = c.w;
        active_h = c.h;
        painted.clear();
        fill_rects.clear();
        assert(render_native_modern_pause_overlay(
            painter,pixels,c.w,c.w,c.h,menu,true,"P2 CONTROLLER DISCONNECTED"));
        assert(contains("P2 CONTROLLER DISCONNECTED"));
        assert(!contains("GAME PAUSED"));
        assert(fill_rects.front().x == c.panel_x && fill_rects.front().w == c.panel_w);
        const int inset = c.w >= 400 ? 18 : 9;
        assert(inset + 26 * 8 <= c.panel_w - 4);
    }
    active_w = 512;
    active_h = 448;
    painted.clear();
    // The two small-source branches have independent status witnesses;
    // start a fresh colour receipt for the separate paused-Options path.
    legible_pause_status_draws = 0;
    assert(!render_native_modern_pause_overlay(
        painter,pixels,255,255,224,menu,true));
    assert(painted.empty());

    // Paused Options: refuses to draw unless the shared view says it is open.
    painted.clear();
    ModernRootOverlayView view{};
    assert(!render_native_modern_pause_options(
        painter, pixels, 512, 512, 448, view));
    assert(painted.empty());
    view.options_open = true;
    view.options_row_count = 3;
    view.options_selected = 2;
    view.options_rows[0] = {"DISPLAY", "WINDOWED", true};
    view.options_rows[1] = {"VSYNC", "ON", true};
    view.options_rows[2] = {"VOLUME", "90%", true};
    view.options_status = "SAVED";
    assert(render_native_modern_pause_options(
        painter, pixels, 512, 512, 448, view));
    assert(contains("GAME PAUSED") && contains("OPTIONS"));
    assert(!contains("PAUSED - GUEST FROZEN"));
    assert(legible_pause_status_draws == 1);
    assert(contains(">VOLUME   < 90% >") && contains("SAVED"));
    assert(contains("L/R CHANGE  B BACK"));
    // Actual prepared 342 source and 2x/4x fallbacks now use the same
    // centered 320-logical geometry as the native root and destinations.
    // The original 256 source and 512x448 4:3 panel remain 240 logical.
    struct SourceCase { int w, h, x, y, panel_w, panel_h; };
    constexpr SourceCase source_cases[] = {
        {256,224,8,10,240,204},
        {342,224,11,10,320,204},
        {512,448,16,20,480,408},
        {684,448,22,20,640,408},
        {1024,896,32,40,960,816},
        {1368,896,44,40,1280,816},
        // Output-size buffers are not automatically 342-native widescreen.
        {1024,768,272,180,480,408},
        {1280,720,400,156,480,408},
    };
    for (const auto& c : source_cases) {
        active_w = c.w;
        active_h = c.h;
        painted.clear();
        fill_rects.clear();
        legible_pause_status_draws = 0;
        assert(render_native_modern_pause_options(
            painter,pixels,c.w,c.w,c.h,view));
        assert(!fill_rects.empty());
        const auto& first = fill_rects.front();
        assert(first.x == c.x && first.y == c.y &&
               first.w == c.panel_w && first.h == c.panel_h);
        assert(contains("GAME PAUSED") && contains("OPTIONS") &&
               contains("SAVED"));
        assert(legible_pause_status_draws == 1);
    }
    active_w = 512;
    active_h = 448;
    // Too small a raster is refused, never partially drawn.
    painted.clear();
    assert(!render_native_modern_pause_options(
        painter, pixels, 200, 200, 200, view));
    assert(painted.empty());
    assert(!render_native_modern_pause_options(
        {}, pixels, 512, 512, 448, view));
    std::puts("PASS: native paused menu wires OPTIONS and shares one Options modal");
    return 0;
}

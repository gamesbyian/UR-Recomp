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
int active_w = 0;
int active_h = 0;
void check_bounds(int x, int y, int w, int h) {
    if (!active_w) return;
    assert(x >= 0 && y >= 0 && w > 0 && h > 0);
    assert(x <= active_w - w && y <= active_h - h);
}
void fill(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t) {
    check_bounds(x,y,w,h);
}
void stroke(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t) {
    check_bounds(x,y,w,h);
}
void text(std::uint32_t*,int,int,int x,int y,const char* t,std::uint32_t colour,int scale) {
    check_bounds(x,y,static_cast<int>(std::string(t).size()) * 8 * scale,8 * scale);
    painted.emplace_back(t);
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

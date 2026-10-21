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
void fill(std::uint32_t*,int,int,int,int,int,int,std::uint32_t) {}
void stroke(std::uint32_t*,int,int,int,int,int,int,std::uint32_t) {}
void text(std::uint32_t*,int,int,int,int,const char* t,std::uint32_t,int) {
    painted.emplace_back(t);
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

    // Pause panel: Options connected; Controls, Run Data, Records and Exit
    // remain SOON (4 labels), Resume/Restart/Options/Quit carry none.
    assert(render_native_modern_pause_overlay(
        painter, pixels, 512, 512, 448, menu, true));
    assert(contains("OPTIONS") && contains("RESUME") && contains("QUIT DESKTOP"));
    assert(contains("GAME PAUSED"));
    assert(!contains("PAUSED - GUEST FROZEN"));
    assert(count("SOON") == 4);

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

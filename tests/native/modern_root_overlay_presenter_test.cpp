// Reuse one exact first-party Modern root presenter for Baldosa and
// the existing modern host. Host painter stubs record every visual operation.
#include "native/product/modern_root_overlay_presenter.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::vector<std::string> painted;
std::uint32_t chosen_color;
void fill(std::uint32_t*,int,int,int,int,int,int,std::uint32_t color) {
    painted.emplace_back("fill");
    chosen_color = color;
}
void stroke(std::uint32_t*,int,int,int,int,int,int,std::uint32_t) {
    painted.emplace_back("stroke");
}
void text(std::uint32_t*,int,int,int,int,const char* t,std::uint32_t,int) {
    painted.emplace_back(t);
}
bool contains(const std::string& s) {
    for (const auto& item : painted) if (item == s) return true;
    return false;
}
int count(const std::string& s) {
    int result=0;
    for (const auto& item : painted) if (item == s) ++result;
    return result;
}
} // namespace

int main() {
    std::uint32_t pixels[64]{};
    constexpr ModernRootOverlayPainter painter{&fill,&stroke,&text};
    constexpr HostOverlayRect old_view{8,10,240,204};
    constexpr HostOverlayRect wide_view{80,20,356*4,204*4};
    ModernRootOverlayView view{};

    // Exactly five source-derived destinations with the old labels, cursor,
    // title, details and 240x204 authentic geometry. No independent router.
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("UNIRACERS"));
    assert(contains("RACER: CREATE A RACER WITH X"));
    assert(contains("> PLAY"));
    assert(contains("  PRACTICE"));
    assert(contains("  MULTIPLAYER"));
    assert(contains("  RECORDS"));
    assert(contains("  OPTIONS"));
    assert(contains("TOUR AND CONTINUE"));
    assert(contains("A/ENTER SELECT   B/ESC QUIT"));
    assert(count("UNIRACERS") == 2); // unchanged title/shadow
    assert(!contains("SELECTED")); // narrow default shell

    painted.clear();
    view.europe = true;
    view.racer_name = "CUSTOM RACER";
    view.menu = modern_root_menu_move(view.menu,3);
    view.tour_continue_available = true;
    view.quit_confirm = true;
    assert(render_modern_root_overlay(painter,pixels,1368,896,4,356,
                                      wide_view,view));
    assert(contains("UNIRALLY"));
    assert(contains("RACER: CUSTOM RACER"));
    assert(contains("> RECORDS"));
    assert(contains("SELECTED"));
    assert(contains("RUNS AND BEST TIMES"));
    assert(contains("QUIT TO DESKTOP?"));
    assert(contains("A/ENTER YES   B/ESC NO"));
    assert(!contains("CONTINUE READY")); // only on selected Play

    painted.clear();
    view.menu = modern_root_menu_reset();
    assert(render_modern_root_overlay(painter,pixels,1368,896,4,356,
                                      wide_view,view));
    assert(contains("CONTINUE READY"));

    painted.clear();
    assert(!render_modern_root_overlay({},pixels,256,224,1,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,0,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,nullptr,256,224,1,240,
                                       old_view,view));
    assert(painted.empty()); // rejection never partially draws an overlay
    std::puts("PASS: one shared Modern root artwork presenter, five routes, old+wide views");
}

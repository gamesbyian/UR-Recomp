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
    constexpr HostOverlayRect wide_view{56,20,356*4,204*4};
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
    // Navigation deliberately moves one destination per input event, even
    // when the signed delta has magnitude greater than one.
    for (int i = 0; i < 3; ++i)
        view.menu = modern_root_menu_move(view.menu, 1);
    view.tour_continue_available = true;
    view.quit_confirm = true;
    assert(render_modern_root_overlay(painter,pixels,1536,896,4,356,
                                      wide_view,view));
    assert(contains("UNIRALLY"));
    assert(contains("RACER: CUSTOM RACER"));
    assert(contains("> RECORDS"));
    assert(contains("SELECTED"));
    // The shared painter applies the existing cell budget to detail copy.
    assert(contains(fit_modern_overlay_text(
        "RUNS AND BEST TIMES", modern_overlay_text_cells(356 - 193))));
    assert(contains("QUIT TO DESKTOP?"));
    assert(contains("A/ENTER YES   B/ESC NO"));
    assert(!contains("CONTINUE READY")); // only on selected Play

    painted.clear();
    view.menu = modern_root_menu_reset();
    assert(render_modern_root_overlay(painter,pixels,1536,896,4,356,
                                      wide_view,view));
    assert(contains("CONTINUE READY"));

    painted.clear();
    // Native Baldosa exposes only Play and Multiplayer until the underlying
    // Modern routes are wired. The shared ship renderer remains unchanged.
    view.europe = false;
    view.quit_confirm = false;
    view.racer_shortcuts_available = false;
    view.available_destinations =
        (1u << static_cast<unsigned>(ModernRootDestination::Play)) |
        (1u << static_cast<unsigned>(ModernRootDestination::Multiplayer));
    for (int i = 0; i < 3; ++i)
        view.menu = modern_root_menu_move(view.menu, 1);
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("> RECORDS"));
    assert(count("SOON") == 3);
    assert(contains("NOT YET AVAILABLE"));
    assert(contains("RACER SETUP NOT YET LINKED"));
    assert(!contains("X/F2 RACERS   F1 HELP"));
    painted.clear();
    view.available_destinations = 0x1fu;
    view.racer_shortcuts_available = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(count("SOON") == 0);
    assert(contains("RUNS AND BEST TIMES"));
    assert(contains("X/F2 RACERS   F1 HELP"));

    painted.clear();
    // Native Records uses the SAME shared root painter and a read-only
    // modal; old shipping host defaults to modal closed without new UI.
    view.available_destinations =
        (1u << static_cast<unsigned>(ModernRootDestination::Play)) |
        (1u << static_cast<unsigned>(ModernRootDestination::Multiplayer)) |
        (1u << static_cast<unsigned>(ModernRootDestination::Records));
    view.read_only_records_open = true;
    view.records_status = "SAVED: 2  UNAVAILABLE: 1";
    view.records_recent = "LATEST: course:02 00:15.50";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(count("SOON") == 2); // Practice and Options only
    assert(contains("STORED RUNS"));
    assert(contains("SAVED: 2  UNAVAILABLE: 1"));
    assert(contains("LATEST: course:02 00:15.50"));
    assert(contains("READ ONLY - NO REPLAY"));
    assert(contains("A/ENTER  B/ESC BACK"));
    painted.clear();
    view.read_only_records_open = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("STORED RUNS"));
    assert(!contains("READ ONLY - NO REPLAY"));

    painted.clear();
    assert(!render_modern_root_overlay({},pixels,256,224,1,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,0,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,nullptr,256,224,1,240,
                                       old_view,view));
    const HostOverlayRect out_of_bounds{30,10,240,204};
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,240,
                                       out_of_bounds,view));
    assert(painted.empty()); // rejection never partially draws an overlay
    std::puts("PASS: one shared Modern root artwork presenter, five routes, old+wide views");
}

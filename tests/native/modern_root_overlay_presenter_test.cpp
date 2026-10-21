// Reuse one exact first-party Modern root presenter for Baldosa and
// the existing modern host. Host painter stubs record every visual operation.
#include "native/product/modern_root_overlay_presenter.hpp"

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::vector<std::string> painted;
struct TextDraw { int x; int y; int scale; std::string content; std::uint32_t color; };
struct RectDraw { int x; int y; int width; int height; };
std::vector<TextDraw> text_draws;
std::vector<RectDraw> rect_draws;
std::uint32_t chosen_color;
void fill(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t color) {
    painted.emplace_back("fill");
    rect_draws.push_back({x,y,w,h});
    chosen_color = color;
}
void stroke(std::uint32_t*,int,int,int x,int y,int w,int h,std::uint32_t) {
    painted.emplace_back("stroke");
    rect_draws.push_back({x,y,w,h});
}
void text(std::uint32_t*,int,int,int x,int y,const char* t,
          std::uint32_t color,int scale) {
    painted.emplace_back(t);
    text_draws.push_back({x, y, scale, t, color});
}
bool contains(const std::string& s) {
    for (const auto& item : painted) if (item == s) return true;
    return false;
}
bool drawn_in_color(const std::string& value, std::uint32_t color) {
    for (const auto& row : text_draws)
        if (row.content == value && row.color == color) return true;
    return false;
}
int count(const std::string& s) {
    int result=0;
    for (const auto& item : painted) if (item == s) ++result;
    return result;
}
// First-party native text ABI draws 8px source glyphs at integer scale.
// Check actual coordinates, not just that particular strings were sent.
bool rect_draws_fit(HostOverlayRect panel) {
    for (const auto& draw : rect_draws)
        if (draw.width <= 0 || draw.height <= 0 ||
            draw.x < panel.x || draw.y < panel.y ||
            static_cast<std::int64_t>(draw.x) + draw.width >
                static_cast<std::int64_t>(panel.x) + panel.width ||
            static_cast<std::int64_t>(draw.y) + draw.height >
                static_cast<std::int64_t>(panel.y) + panel.height)
            return false;
    return true;
}
bool text_draws_fit(HostOverlayRect panel) {
    for (const auto& draw : text_draws) {
        if (draw.scale <= 0 || draw.x < panel.x || draw.y < panel.y ||
            draw.x + static_cast<int>(draw.content.size()) * 8 * draw.scale >
                panel.x + panel.width ||
            draw.y + 8 * draw.scale > panel.y + panel.height)
            return false;
    }
    return true;
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
    assert(drawn_in_color("RACER: CREATE A RACER WITH X",
                          kModernMenuCheckerLegibleGrey));
    static_assert(kModernMenuCheckerLegibleGrey == 0xFFC8C8C8u);
    assert(contains("> PLAY"));
    assert(contains("  PRACTICE"));
    assert(contains("  MULTIPLAYER"));
    assert(contains("  RECORDS"));
    assert(contains("  OPTIONS"));
    assert(contains("TOUR AND CONTINUE"));
    assert(contains("A/ENTER SELECT   B/ESC QUIT"));
    assert(count("UNIRACERS") == 2); // unchanged title/shadow
    assert(!contains("SELECTED")); // narrow default shell
    assert(text_draws_fit(old_view)); // every root label stays in 240px panel
    assert(rect_draws_fit(old_view)); // checker, focus and frame remain inside
    // Real 640x480 SDL baseline: the anonymous rider was previously printed
    // as "RACER: STOCK RACER - NO PROF", losing the source state.
    painted.clear();
    view.racer_name = "STOCK RACER - NO PROFILE";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("RACER: NO PROFILE"));
    assert(drawn_in_color("RACER: NO PROFILE",
                          kModernMenuCheckerLegibleGrey));
    assert(!contains("RACER: STOCK RACER - NO PROF"));
    // In narrow mode the identity is truthful and never overflows.
    assert(text_draws_fit(old_view));
    // The actual native host emits this status when the active SRAM/racer
    // profile changes during a race. An ordinary prefix+truncation used to
    // lose the only useful action, RESTART APP, at 240 logical pixels.
    painted.clear();
    view.racer_name = "PROFILE CHANGED - RESTART APP";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("RACER: CHANGED - RESTART APP"));
    assert(!contains("RACER: PROFILE CHANGED - ..."));
    assert(drawn_in_color("RACER: CHANGED - RESTART APP",
                          kModernMenuCheckerLegibleGrey));
    assert(text_draws_fit(old_view));
    // Exact native host statuses keep the essential RESTART/SAVE action
    // in every stock-width banner; ordinary names still use an ellipsis.
    const char* const statuses[] = {
        "RESTART TO USE NEW RACER",
        "SECOND RACER SAVED - RESTART",
        "P1 SWITCH QUEUED - QUIT TO SAVE"
    };
    const char* const compact[] = {
        "RACER: RESTART FOR NEW RACER",
        "RACER: P2 SAVED - RESTART",
        "RACER: SWITCH: QUIT TO SAVE"
    };
    for (std::size_t i = 0; i < 3; ++i) {
        painted.clear();
        view.racer_name = statuses[i];
        assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                          old_view,view));
        assert(contains(compact[i]));
        assert(text_draws_fit(old_view));
    }
    painted.clear();
    view.racer_name = "THIS IS AN EXCESSIVELY LONG RACER NAME";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("RACER: THIS IS AN EXCESSI..."));
    assert(!contains("RACER: THIS IS AN EXCESSIV"));
    painted.clear();

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
    assert(contains("RECORDS")); // real active destination in wide preview
    assert(!contains("SELECTED")); // generic engineering heading removed
    // Original stock-family wide context must expose both complete clauses.
    // Earlier 320px-panel output silently emitted only "RUNS AND BEST".
    assert(contains("RUNS AND"));
    assert(contains("BEST TIMES"));
    assert(!contains("RUNS AND BEST"));
    assert(contains("QUIT TO DESKTOP?"));
    assert(contains("A/ENTER YES   B/ESC NO"));
    assert(!contains("CONTINUE READY")); // only on selected Play

    painted.clear();
    view.menu = modern_root_menu_reset();
    assert(render_modern_root_overlay(painter,pixels,1536,896,4,356,
                                      wide_view,view));
    assert(contains("CONTINUE READY"));
    // This same native sentinel has enough room to retain its full wording
    // in the wide panel: only the 240px fallback requires compact copy.
    // Isolate geometry receipts by draw: compact coordinates accumulated
    // above must never be treated as output of this 4x widescreen render.
    painted.clear();
    text_draws.clear();
    rect_draws.clear();
    view.racer_name = "PROFILE CHANGED - RESTART APP";
    assert(render_modern_root_overlay(painter,pixels,1536,896,4,356,
                                      wide_view,view));
    assert(contains("RACER: PROFILE CHANGED - RESTART APP"));
    assert(!contains("RACER: CHANGED - RESTART APP"));
    assert(text_draws_fit(wide_view));
    // Native wide retains all original host statuses verbatim.
    for (const char* status : {"RESTART TO USE NEW RACER",
                                "SECOND RACER SAVED - RESTART",
                                "P1 SWITCH QUEUED - QUIT TO SAVE"}) {
        painted.clear();
        view.racer_name = status;
        assert(render_modern_root_overlay(painter,pixels,1536,896,4,356,
                                          wide_view,view));
        assert(contains(std::string("RACER: ") + status));
        assert(text_draws_fit(wide_view));
    }
    view.racer_name = "CUSTOM RACER";

    painted.clear();
    // The actual 320-logical-pixel Modern root admits just 13 text cells
    // in the secondary column, at both 1x logical size and 4x scaling.
    constexpr HostOverlayRect real_wide_view{0,0,320*4,204*4};
    view.available_destinations = 0x1fu;
    view.quit_confirm = false;
    view.tour_continue_available = false;
    constexpr const char* expected_lines[][2] = {
        {"TOUR AND", "CONTINUE"},
        {"CHOOSE A", "COURSE"},
        {"LOCAL", "TWO PLAYER"},
        {"RUNS AND", "BEST TIMES"},
        {"DISPLAY AND", "CONTROLS"}
    };
    for (unsigned i = 0; i < kModernRootDestinationCount; ++i) {
        painted.clear();
        text_draws.clear();
        rect_draws.clear();
        view.menu = modern_root_menu_reset();
        for (unsigned j = 0; j < i; ++j)
            view.menu = modern_root_menu_move(view.menu, 1);
        assert(render_modern_root_overlay(painter,pixels,1536,896,4,320,
                                          real_wide_view,view));
        assert(contains(expected_lines[i][0]));
        assert(contains(expected_lines[i][1]));
        // Independent of the route hint, its yellow preview heading is
        // exactly the selected source destination, never a stale label.
        const char* active = modern_root_destination_label(
            modern_root_destination_from_index(i));
        assert(contains(active));
        assert(drawn_in_color(active, kModernStockMenuPalette.title_yellow));
        assert(!contains("SELECTED"));
        assert(text_draws_fit(real_wide_view));
        assert(rect_draws_fit(real_wide_view));
        assert(!contains("TOUR AND CONT")); // old silently cropped copy
        assert(!contains("DISPLAY AND CON")); // old silently cropped copy
    }
    painted.clear();
    view.menu = modern_root_menu_reset();
    view.available_destinations = 0;
    assert(render_modern_root_overlay(painter,pixels,1536,896,4,320,
                                      real_wide_view,view));
    assert(contains("NOT YET"));
    assert(contains("AVAILABLE"));
    assert(!contains("NOT YET AVAI"));
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
    assert(drawn_in_color("SOON", kModernMenuCheckerLegibleGrey));
    assert(drawn_in_color("> RECORDS", kModernMenuCheckerLegibleGrey));
    assert(contains("NOT YET AVAILABLE"));
    // No setup route is advertised for a host with no shortcut. The former
    // "RACER SETUP NOT YET LINKED" was an internal false player instruction.
    assert(!contains("RACER SETUP NOT YET LINKED"));
    assert(!contains("X/F2 RACERS   F1 HELP"));
    assert(!contains("")); // do not issue an empty draw-text command
    assert(contains("A/ENTER SELECT   B/ESC QUIT"));
    painted.clear();
    view.available_destinations = 0x1fu;
    view.racer_shortcuts_available = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(count("SOON") == 0);
    assert(contains("RUNS AND BEST TIMES"));
    assert(contains("X/F2 RACERS   F1 HELP"));

    // One actual shipped P1 shortcut, no development-only "stock" jargon.
    // Does not change what profile the existing shortcut creates.
    // Source-bound geometry checks must count THIS compact draw alone;
    // prior wide-root operations use incompatible (larger) coordinates.
    painted.clear();
    text_draws.clear();
    rect_draws.clear();
    view.racer_shortcuts_available = false;
    view.first_racer_shortcut_available = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("X CREATE RACER"));
    assert(!contains("X CREATE STOCK RACER"));
    assert(text_draws_fit(old_view));
    view.first_racer_shortcut_available = false;
    view.racer_shortcuts_available = true;

    painted.clear();
    // Native Records uses the SAME shared root painter and a read-only
    // modal; old shipping host defaults to modal closed without new UI.
    view.available_destinations =
        (1u << static_cast<unsigned>(ModernRootDestination::Play)) |
        (1u << static_cast<unsigned>(ModernRootDestination::Multiplayer)) |
        (1u << static_cast<unsigned>(ModernRootDestination::Records));
    view.read_only_records_open = true;
    view.records_status = "VALID 2  UNAVAILABLE 1";
    view.records_recent = "LAST: course:02 00:15.50";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(count("SOON") == 2); // Practice and Options only
    assert(contains("STORED RUNS"));
    assert(modern_overlay_text_cells(240 - 30) >=
           view.records_status.size());
    assert(modern_overlay_text_cells(240 - 30) >=
           view.records_recent.size());
    // Exact full text, not a truncated/budgeted prefix. The hundredths
    // must remain visible in the original 256x224 narrow presentation.
    assert(contains("VALID 2  UNAVAILABLE 1"));
    assert(contains("LAST: course:02 00:15.50"));
    assert(contains("REPLAY UNAVAILABLE"));
    assert(contains("A/ENTER  B/ESC BACK"));
    painted.clear();
    // The existing 1P modal is still the default for old consumers.
    // Native Baldosa alone advertises an explicit 2P page: no invented
    // match results, only canonical already-paired history and a pad hint.
    view.read_only_records_pages_available = true;
    view.read_only_records_two_player = true;
    view.records_status = "MY 2P 1  UNAVAILABLE 3";
    view.records_recent = "W 1  L 0  D 0";
    view.records_detail = "LAST 01 WIN 00:28.76";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("TWO PLAYER RECORDS"));
    assert(contains("MY 2P 1  UNAVAILABLE 3"));
    assert(contains("W 1  L 0  D 0"));
    assert(contains("LAST 01 WIN 00:28.76"));
    assert(contains("UP/DOWN 1P  B BACK"));
    assert(contains("REPLAY UNAVAILABLE"));
    painted.clear();
    view.read_only_records_two_player = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("STORED RUNS"));
    assert(!contains("LAST 01 WIN 00:28.76"));
    assert(contains("UP/DOWN 2P  B BACK"));
    painted.clear();
    view.read_only_records_open = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("STORED RUNS"));
    assert(!contains("REPLAY UNAVAILABLE"));

    // The native P1/P2 join is now a child of this SAME renderer, never
    // separately drawn by the execution adapter. Older hosts opt out by
    // default. P1 is visibly fixed to the loaded profile; P2 alone browses.
    painted.clear();
    view.two_seat_join_open = true;
    view.join_p1_name = "MIKE";
    view.join_p2_name = "ANDREW";
    view.join_p1_stock = "MIKE";
    view.join_p2_stock = "ANDREW";
    view.join_p1_confirmed = false;
    view.join_p2_confirmed = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("TWO PLAYER PROFILES"));
    assert(contains("P1 MIKE ACTIVE"));
    assert(contains("P2 ANDREW CHOOSE"));
    assert(contains("RACE AS: MIKE / ANDREW"));
    assert(contains("P1 A READY / B BACK"));
    assert(contains("P2 DPAD+A / B CLEAR"));
    assert(!contains("STOCK: MIKE / ANDREW"));
    painted.clear();
    view.join_p1_confirmed = true;
    view.join_p2_confirmed = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("P1 MIKE READY"));
    assert(contains("P2 ANDREW READY"));
    painted.clear();
    view.two_seat_join_open = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("TWO PLAYER PROFILES"));
    painted.clear();
    view.unbound_two_player_warning_open = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("UNRECORDED TWO PLAYER"));
    assert(contains("NEED TWO NAMED RACERS"));
    assert(contains("2P RESULTS NOT SAVED"));
    assert(contains("PLAY LOCAL 2P ANYWAY?"));
    assert(contains("P1 A YES  B BACK"));
    painted.clear();
    view.unbound_two_player_warning_open = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("UNRECORDED TWO PLAYER"));
    // Exact product flags must label both actual native racer modes.
    painted.clear();
    view.first_racer_open = true;
    view.first_racer_is_switch = false;
    view.first_racer_is_second = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("FIRST RACER"));
    view.first_racer_is_second = true;
    painted.clear();
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("SECOND RACER"));
    view.first_racer_open = false;
    view.first_racer_is_second = false;

    // A refused route or stale racer is stated in the root's hint line, and
    // multi-course Practice names its tour, kind and open-course count.
    painted.clear();
    view.root_notice = "COURSE NOT REACHABLE - RETRY";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("COURSE NOT REACHABLE - RETRY"));
    assert(!contains("X/F2 RACERS   F1 HELP"));
    view.root_notice = {};
    painted.clear();
    view.practice_picker_open = true;
    view.practice_course_name = "Looper";
    view.practice_tour_name = "Shuffler";
    view.practice_kind_label = "RACE";
    view.practice_courses_open = 20;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("Looper"));
    assert(contains("Shuffler - RACE"));
    assert(contains("20 OPEN - MORE FROM MEDALS"));
    assert(contains("A START L/R TOUR B BACK"));
    painted.clear();
    view.practice_courses_open = 40;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("40 COURSES OPEN") && !contains("40 OPEN - MORE FROM MEDALS"));
    painted.clear();
    view.practice_courses_open = 0;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("1 VERIFIED COURSE") && contains("A START  B BACK"));
    view.practice_picker_open = false;
    // Existing source-owned launch pending keeps its actionable copy.
    painted.clear();
    view.practice_launch_pending = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("STARTING PRACTICE"));
    assert(contains("WAIT FOR GO"));
    view.practice_launch_pending = false;

    // Native OPTIONS is opt-in: the old host's exact layout is unchanged and
    // the modal shows only what the host supplied, with the selected
    // adjustable value bracketed and any status/notice on one line.
    painted.clear();
    assert(!view.options_open);
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("L/R CHANGE  B BACK"));
    painted.clear();
    view.options_open = true;
    view.options_row_count = 3;
    view.options_selected = 1;
    view.options_rows[0] = {"DISPLAY", "WINDOWED", true};
    view.options_rows[1] = {"VSYNC", "ON", true};
    view.options_rows[2] = {"CONTROLS", "SHOW", false};
    view.options_status = "SAVED";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains(" DISPLAY  WINDOWED"));
    assert(contains(">VSYNC    < ON >"));
    assert(contains(" CONTROLS SHOW"));
    assert(contains("SAVED"));
    assert(contains("L/R CHANGE  B BACK"));
    painted.clear();
    view.options_status = {};
    view.options_notice = "SAVED OPTIONS DAMAGED";
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("SAVED OPTIONS DAMAGED"));
    painted.clear();
    view.options_controls_help = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("MENU CONTROLS"));
    assert(contains("LEFT/RIGHT  CHANGE"));
    assert(contains("B/ESC    BACK"));
    assert(!contains(">VSYNC    < ON >"));
    assert(contains("X  RACER SETUP")); // historical capable host
    // Native without an actual racer action must never advertise the X
    // shortcut, even on the deep Controls help screen. The other movement
    // and select/back help remains untouched and reachable.
    painted.clear();
    view.racer_shortcuts_available = false;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(!contains("X  RACER SETUP"));
    assert(contains("MENU CONTROLS"));
    assert(contains("UP/DOWN  MOVE"));
    assert(contains("B/ESC    BACK"));
    // A host may explicitly support first-time racer creation without the
    // legacy F2 shortcut family. That is still a real X destination.
    painted.clear();
    view.first_racer_shortcut_available = true;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    assert(contains("X  RACER SETUP"));
    view.first_racer_shortcut_available = false;
    view.racer_shortcuts_available = true;
    // A host cannot over-declare rows past the fixed bound.
    painted.clear();
    view.options_controls_help = false;
    view.options_row_count = 99;
    assert(render_modern_root_overlay(painter,pixels,256,224,1,240,
                                      old_view,view));
    view.options_open = false;
    view.options_row_count = 0;
    view.options_notice = {};

    // Optional original *source-pixel* header is now consumable by the
    // ACTUAL shared root painter, not just the isolated atlas test. This
    // synthetic buffer contains no copyrighted image and is opt-in only.
    // Without it, all existing Windows/host callers paint identical text.
    painted.clear();
    view.europe = false;
    std::vector<std::uint32_t> source_pixels(640u * 16u, 0xFF112233u);
    const ModernMenuSourcePixels source_atlas{
        source_pixels.data(), source_pixels.size(), 640, 640, 16};
    std::vector<std::uint32_t> framebuffer(256u * 224u, 0u);
    assert(render_modern_root_overlay(
        painter, framebuffer.data(), 256, 224, 1, 240,
        old_view, view, &source_atlas));
    assert(!contains("UNIRACERS")); // no synthetic duplicate/shadow draw
    assert(contains("  PRACTICE")); // all other source-owned routes unchanged
    assert(framebuffer[static_cast<std::size_t>(16) * 256 + 17] ==
           0xFF112233u); // at 8+9, 10+6 source-heading origin

    // Regional original source text must use UNIRALLY, not UNIRACERS.
    painted.clear();
    view.europe = true;
    std::fill(framebuffer.begin(), framebuffer.end(), 0u);
    assert(render_modern_root_overlay(
        painter, framebuffer.data(), 256, 224, 1, 240,
        old_view, view, &source_atlas));
    assert(!contains("UNIRALLY"));
    assert(framebuffer[static_cast<std::size_t>(16) * 256 + 17] ==
           0xFF112233u);

    // Source raster is also scaled through the SAME native root at 4x
    // density without changing source geometry or the host's content.
    painted.clear();
    std::vector<std::uint32_t> wide_framebuffer(1536u * 896u, 0u);
    assert(render_modern_root_overlay(
        painter, wide_framebuffer.data(), 1536, 896, 4, 356,
        wide_view, view, &source_atlas));
    assert(!contains("UNIRALLY"));
    assert(wide_framebuffer[
        static_cast<std::size_t>(20 + 6 * 4) * 1536 + (56 + 9 * 4)] ==
           0xFF112233u);

    // An invalid source buffer or unsupported intermediate alpha must
    // fail atomically and fall back to the preexisting host title; it
    // must not render half a real heading or skip the title altogether.
    painted.clear();
    std::fill(framebuffer.begin(), framebuffer.end(), 0u);
    const ModernMenuSourcePixels short_atlas{
        source_pixels.data(), 10, 640, 640, 16};
    assert(render_modern_root_overlay(
        painter, framebuffer.data(), 256, 224, 1, 240,
        old_view, view, &short_atlas));
    assert(contains("UNIRALLY"));
    assert(std::all_of(framebuffer.begin(), framebuffer.end(),
                       [](std::uint32_t px) {return px == 0;}));
    painted.clear();
    const std::size_t used_heading_pixel =
        static_cast<std::size_t>(modern_menu_heading_slot('U')) * 16u;
    source_pixels[used_heading_pixel] = 0x80112233u;
    assert(render_modern_root_overlay(
        painter, framebuffer.data(), 256, 224, 1, 240,
        old_view, view, &source_atlas));
    assert(contains("UNIRALLY"));
    assert(std::all_of(framebuffer.begin(), framebuffer.end(),
                       [](std::uint32_t px) {return px == 0;}));
    source_pixels[used_heading_pixel] = 0xFF112233u;
    view.europe = false;

    // The public Options painter can be called by in-race pause screens.
    // Missing host callbacks, invalid logical scale or a box which extends
    // beyond the real output must return without ANY painter action.
    painted.clear();
    render_modern_options_modal({}, pixels, 256, 224, 1, 240, 8, 10, view);
    assert(painted.empty());
    render_modern_options_modal(painter, nullptr, 256, 224, 1, 240, 8, 10, view);
    assert(painted.empty());
    render_modern_options_modal(painter, pixels, 256, 224, 5, 240, 8, 10, view);
    assert(painted.empty());
    render_modern_options_modal(painter, pixels, 256, 224, 1, 240, 25, 10, view);
    assert(painted.empty());
    render_modern_options_modal(painter, pixels, 256, 224, 1, 240, 8, 45, view);
    assert(painted.empty());
    render_modern_options_modal(painter, pixels, 256, 224, 1, 513, 8, 10, view);
    assert(painted.empty());
    render_modern_options_modal(painter, pixels, 256, 224, 1, 175, 8, 10, view);
    assert(painted.empty());
    text_draws.clear();
    rect_draws.clear();
    render_modern_options_modal(painter, pixels, 256, 224, 1, 240, 8, 10, view);
    assert(contains("OPTIONS"));
    assert(rect_draws_fit(old_view));
    assert(text_draws_fit(old_view));
    painted.clear();

    painted.clear();
    assert(!render_modern_root_overlay({},pixels,256,224,1,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,0,240,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,5,240,
                                       old_view,view));
    // Host must not expose any part of the root outside its own panel.
    // These boxes lie INSIDE a valid framebuffer but cannot contain the
    // complete 240x204 source menu shell or 320-wide preview.
    constexpr HostOverlayRect short_panel{8, 10, 240, 203};
    constexpr HostOverlayRect thin_panel{8, 10, 239, 204};
    constexpr HostOverlayRect not_scaled{8, 10, 240, 204};
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,240,
                                       short_panel,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,240,
                                       thin_panel,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,4,240,
                                       not_scaled,view));
    constexpr HostOverlayRect small_wide{56,20,319*4,204*4};
    assert(!render_modern_root_overlay(painter,pixels,1536,896,4,320,
                                       small_wide,view));
    // Extreme numeric values must be rejected before 27*scale etc are used
    // to draw. A valid surface bounds check alone is not enough.
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,513,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,175,
                                       old_view,view));
    assert(!render_modern_root_overlay(painter,nullptr,256,224,1,240,
                                       old_view,view));
    const HostOverlayRect out_of_bounds{30,10,240,204};
    assert(!render_modern_root_overlay(painter,pixels,256,224,1,240,
                                       out_of_bounds,view));
    assert(painted.empty()); // rejection never partially draws an overlay
    std::puts("PASS: one shared Modern root artwork presenter, five routes, old+wide views");
}

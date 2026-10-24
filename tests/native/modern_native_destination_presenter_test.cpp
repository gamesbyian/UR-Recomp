// Exact native destination painter contract, with no synthetic game state.
// Each text/rectangle goes through the same painter ABI as the real Baldosa
// host; the model comes only from ModernRootOverlayView.
#include "native/product/modern_native_destination_presenter.hpp"

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::vector<std::string> text_seen;
struct PaintedText { int x, y, size; std::size_t cells; std::uint32_t colour; };
std::vector<PaintedText> painted_text;
struct Rectangle {int x,y,w,h; std::uint32_t colour;};
std::vector<Rectangle> painted;
void fill(std::uint32_t*, int, int, int x, int y, int w, int h,
          std::uint32_t colour) { painted.push_back({x,y,w,h,colour}); }
void stroke(std::uint32_t*, int, int, int x, int y, int w, int h,
            std::uint32_t colour) { painted.push_back({x,y,w,h,colour}); }
void draw(std::uint32_t*, int, int, int x, int y, const char* str,
          std::uint32_t colour, int size) {
    // Preserve actual text/scale and catch glyph overdraw on both surfaces.
    text_seen.emplace_back(str);
    painted_text.push_back({x,y,size,std::string(str).size(),colour});
    assert(x >= 0 && y >= 0 && size > 0);
}
bool has(std::string_view text) {
    return std::find(text_seen.begin(), text_seen.end(),
                     std::string(text)) != text_seen.end();
}
bool has_at(std::string_view text, int x, int y, int scale,
            std::uint32_t colour) {
    for (std::size_t i = 0; i < text_seen.size(); ++i)
        if (text_seen[i] == text && painted_text[i].x == x &&
            painted_text[i].y == y && painted_text[i].size == scale &&
            painted_text[i].colour == colour)
            return true;
    return false;
}
void clear() { text_seen.clear(); painted.clear(); painted_text.clear(); }
void bounds(int width, int height) {
    for (const auto& rect : painted) {
        assert(rect.x >= 0 && rect.y >= 0);
        assert(rect.w > 0 && rect.h > 0);
        assert(rect.x + rect.w <= width);
        assert(rect.y + rect.h <= height);
    }
    for (const auto& label : painted_text) {
        assert(label.x + static_cast<int>(label.cells) *
                   8 * label.size <= width);
        assert(label.y + 8 * label.size <= height);
    }
}
} // namespace

int main() {
    std::uint32_t scratch[64]{};
    constexpr ModernRootOverlayPainter painter{&fill,&stroke,&draw};
    constexpr HostOverlayRect original{8,10,240,204};
    // 342x224 logical pixels with 7:6 PAR project to physical 16:9.
    constexpr HostOverlayRect wide{11,10,320,204};
    ModernRootOverlayView v{};
    // Screenshot QA consumes only real view-derived state names. No
    // alternate scene controller or guessed result metadata is permitted.
    ModernRootOverlayView state{};
    assert(std::string_view(modern_native_destination_stage(state)) == "root");
    state.options_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "options");
    state.options_controls_help = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "options-help");
    state = {};
    state.practice_picker_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "practice-picker");
    state.practice_launch_pending = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "practice-entering-stock");
    state = {};
    state.read_only_records_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "records-1p");
    state.read_only_records_two_player = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "records-2p");
    state = {};
    state.two_seat_join_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "multiplayer-join");
    state.join_p2_confirmed = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "multiplayer-p2-ready");
    state.join_p2_confirmed = false;
    state.join_p1_confirmed = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "multiplayer-p1-ready");
    state.join_p2_confirmed = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "multiplayer-both-ready");
    state = {};
    state.first_racer_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "profile-first");
    state.first_racer_failed = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "profile-first-refused");
    state.first_racer_failed = false;
    state.first_racer_is_second = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "profile-second");
    state.first_racer_is_switch = true;
    state.first_racer_created = true;
    assert(std::string_view(modern_native_destination_stage(state)) == "profile-switch-saved");
    state = {};
    state.unbound_two_player_warning_open = true;
    assert(std::string_view(modern_native_destination_stage(state)) ==
           "multiplayer-unrecorded-warning");
    state = {};
    state.quit_confirm = true;
    assert(std::string_view(modern_native_destination_stage(state)) ==
           "quit-confirm");
    state = {};
    state.root_notice = "SOURCE COURSE UNREACHABLE";
    assert(std::string_view(modern_native_destination_stage(state)) ==
           "root-notice");
    const auto narrow = modern_native_destination_canvas(256,224,1,240,original);
    const auto expanded = modern_native_destination_canvas(342,224,1,320,wide);
    assert(narrow.scale == 1 && !narrow.wide && narrow.w == 236);
    assert(expanded.scale == 1 && expanded.wide && expanded.w == 316);
    // Actual Windows SDL image comparison (integration PR #2053) found legacy
    // root selection stripes and root-only A/B footer escaping the child.
    // An opened destination now occludes the root interactive area from
    // beyond its cursor inset all the way to the original root bottom.
    for (auto c : {narrow, expanded}) {
        assert(c.x <= (c.wide ? wide.x : original.x) + 5 * c.scale);
        assert(c.y == (c.wide ? wide.y : original.y) + 50 * c.scale);
        assert(c.y + c.h ==
               (c.wide ? wide.y + wide.height
                       : original.y + original.height));
    }
    assert(!modern_native_destination_canvas(
        256,224,1,240,{8,10,240,203}).scale);
    assert(!modern_native_destination_canvas(256,224,1,320,original).scale);
    assert(!modern_native_destination_canvas(256,224,0,240,original).scale);
    assert(!modern_native_destination_canvas(256,224,2147483647,240,original).scale);
    assert(!modern_native_destination_canvas(342,224,1,100000,wide).scale);
    assert(!modern_native_destination_canvas(256,224,1,240,{40,10,240,204}).scale);
    // Public text primitive must refuse malformed canvases/scales before
    // dividing by c.scale or forwarding out-of-bounds glyphs to the host.
    clear();
    modern_native_destination_line(
        painter, scratch, 256, 224, {}, 20, "INVALID", 0xFFFFFFFFu);
    modern_native_destination_line(
        painter, scratch, 256, 224, narrow, 20, "INVALID",
        0xFFFFFFFFu, 9, 0);
    modern_native_destination_line(
        painter, scratch, 256, 224, narrow, 20, "INVALID",
        0xFFFFFFFFu, -1);
    modern_native_destination_line(
        painter, scratch, 256, 224, narrow, -1, "INVALID",
        0xFFFFFFFFu);
    auto outside = narrow;
    outside.x = 255;
    modern_native_destination_line(
        painter, scratch, 256, 224, outside, 20, "INVALID",
        0xFFFFFFFFu);
    assert(painted_text.empty() && painted.empty());
    modern_native_destination_line(
        painter, scratch, 256, 224, narrow, 20, "SAFE", 0xFFFFFFFFu);
    assert(has("SAFE"));
    bounds(256, 224);
    clear();
    // Source-backed last times are useful only if the suffix remains exact.
    assert(modern_native_destination_fit(
        "LAST: VERY LONG COURSE NAME 00:15.50", 25, true).substr(17)
        == "00:15.50");
    assert(modern_native_destination_fit(
        "LAST: VERY LONG COURSE NAME 00:15.50", 25, true).find("..")
        != std::string::npos);
    assert(modern_native_destination_fit(
        "UNEXPECTEDLY LONG STORAGE NOTICE", 25).back() == '.');
    assert(modern_native_destination_fit("A", 0).empty());
    assert(!modern_native_destination_is_open(v));
    assert(!render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(painted.empty());

    v.practice_picker_open = true;
    v.practice_course_name = "Zoom Zoo";
    v.practice_tour_name = "Crawler";
    v.practice_kind_label = "Circuit";
    assert(modern_native_display_caps(v.practice_course_name) == "ZOOM ZOO");
    assert(modern_native_display_caps("Down+Up / Boo!") == "DOWN+UP / BOO!");
    v.practice_courses_open = 5;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("PRACTICE") && has("ZOOM ZOO") && has("CRAWLER  /  CIRCUIT"));
    assert(has("5 COURSES UNLOCKED"));
    assert(!has("5 STOCK-UNLOCKED COURSES")); // never show engineering copy
    assert(!has("COURSES")); // compact has no redundant wide-only stage tag
    // Tour and course navigation are separate real native input actions.
    assert(has("UP/DN COURSE   L/R TOUR"));
    assert(has("A START   B BACK"));
    // Regression: real Win32 SDL frame used to leak the root's QUIT help
    // and focus sliver outside the destination panel. Both narrow and wide
    // modals must paint an opaque root-interaction scrim from below the
    // immutable racer identity line to the bottom of the root frame.
    auto has_body_scrim = [](HostOverlayRect root, int scale) {
        return std::any_of(painted.begin(), painted.end(),
            [root,scale](const Rectangle& box) {
                return box.x == root.x + scale &&
                    box.y == root.y + 46 * scale &&
                    box.w == root.width - 2 * scale &&
                    box.h == root.height - 47 * scale &&
                    box.colour == kModernStockMenuPalette.background;
            });
    };
    assert(has_body_scrim(original, 1));
    bounds(256,224);
    clear();
    // On a prepared 342-wide Practice frame the original course's tour and
    // race-kind fields use distinct columns, preserving their actual model
    // values rather than inventing a second course picker.
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("TOUR  CRAWLER") && has("CIRCUIT"));
    assert(!has("CRAWLER  /  CIRCUIT"));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 196 && t.y == 123 && t.cells == 7 &&
                   t.colour == 0xFFFFFFFFu;
        }));
    bounds(342,224);
    clear();
    v.practice_picker_open = false;
    v.practice_launch_pending = true;
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("STARTING PRACTICE"));
    assert(has("WAIT FOR GO") && has("B CANCEL"));
    assert(has("RACE STARTING"));
    assert(has("COURSES")); // the widescreen stage tag is not an implementation label
    // Source-grey #989898 fails normal small-text contrast on the real
    // #484848 header band. The derived brighter neutral must apply ONLY
    // to the optional native-wide tag, never original menu/gameplay pixels.
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.cells == 7 && t.colour == 0xFFC8C8C8u;
        }));
    assert(has_body_scrim(wide, 1));
    bounds(342,224);
    clear();

    // Presentation density is a strict integer transform, not a wider-font
    // guess. The same already-authoritative 342x224 layout also fits 4x.
    constexpr HostOverlayRect wide4{44,40,1280,816};
    assert(render_modern_native_destination(painter,scratch,1368,896,
                                             4,320,wide4,v));
    bounds(1368,896);
    clear();

    v.practice_launch_pending = false;
    v.read_only_records_open = true;
    v.read_only_records_pages_available = true;
    v.records_status = "VALID 2  UNAVAILABLE 1";
    v.records_recent = "LAST: course:02 00:15.50";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("1P RUNS") == false); // the selected row includes its cursor
    assert(has("> 1P RUNS"));
    assert(has("  2P MATCHES"));
    assert(has("LAST: course:02 00:15.50")); // untruncated hundredths
    clear();
    v.records_recent = "LAST: VERY LONG COURSE NAME 00:15.50";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    bool tail_preserved = false;
    for (const auto& label : text_seen)
        if (label.find("..") != std::string::npos &&
            label.size() >= 8 &&
            label.substr(label.size() - 8) == "00:15.50")
            tail_preserved = true;
    assert(tail_preserved);
    bounds(256,224);
    clear();
    v.records_recent = "LAST: course:02 00:15.50";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("UP/DOWN PAGE  B BACK"));
    assert(has("REPLAY UNAVAILABLE"));
    assert(!has("READ ONLY - NO REPLAY"));
    clear();
    v.read_only_records_two_player = true;
    v.records_status = "MY 2P 1  UNAVAILABLE 3";
    v.records_recent = "W 1  L 0  D 0";
    v.records_detail = "LAST 01 WIN 00:28.76";
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("> 2P MATCHES"));
    assert(has("LAST 01 WIN 00:28.76"));
    assert(has("ARCHIVE")); // context rail appears only in prepared native-wide
    clear();

    v.read_only_records_open = false;
    v.options_open = true;
    v.options_row_count = 99; // bounded, never dereference a sixth row
    v.options_selected = 1;
    v.options_rows[0] = {"DISPLAY","WINDOWED",true};
    v.options_rows[1] = {"VSYNC","ON",true};
    v.options_rows[2] = {"VOLUME","90",true};
    v.options_rows[3] = {"CONTROLS","OPEN",false};
    v.options_rows[4] = {"DEFAULTS","RESET",false};
    v.options_status = "SAVED";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("> VSYNC    < ON >"));
    // The 4:3 child uses the SAME stock-blue field / yellow selected label
    // visual contract as the native root, not the former cyan-black slab.
    assert(std::any_of(painted.begin(), painted.end(),
        [](const Rectangle& b) { return b.colour == 0xE0283058u; }));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) { return t.colour ==
            kModernStockMenuPalette.title_yellow && t.cells > 14; }));
    assert(has("SAVED") && has("OPTIONS"));
    assert(!has("SETTINGS")); // compact renderer keeps its source-width title
    assert(has("L/R CHANGE   B BACK"));
    clear();
    // Both a persisted-settings warning and a later action result must be
    // visible. The shared root painter already preserves both; the native
    // destination (also used by Pause) must not silently discard the warning.
    v.options_notice = "SAVED OPTIONS DAMAGED";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has_at("SAVED OPTIONS DAMAGED", 19, 169, 1,
                  kModernMenuCheckerLegibleGrey));
    assert(has_at("SAVED", 19, 180, 1,
                  kModernStockMenuPalette.title_yellow));
    assert(has_at("L/R CHANGE   B BACK", 19, 198, 1,
                  kModernStockMenuPalette.cursor_blue));
    bounds(256,224);
    clear();
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has_at("SAVED OPTIONS DAMAGED", 22, 169, 1,
                  kModernMenuCheckerLegibleGrey));
    assert(has_at("SAVED", 22, 180, 1,
                  kModernStockMenuPalette.title_yellow));
    assert(has_at("L/R CHANGE   B BACK", 22, 198, 1,
                  kModernStockMenuPalette.cursor_blue));
    bounds(342,224);
    clear();
    constexpr HostOverlayRect wide4{44,40,1280,816};
    assert(render_modern_native_destination(painter,scratch,1368,896,
                                             4,320,wide4,v));
    assert(has_at("SAVED OPTIONS DAMAGED", 88, 676, 4,
                  kModernMenuCheckerLegibleGrey));
    assert(has_at("SAVED", 88, 720, 4,
                  kModernStockMenuPalette.title_yellow));
    assert(has_at("L/R CHANGE   B BACK", 88, 792, 4,
                  kModernStockMenuPalette.cursor_blue));
    bounds(1368,896);
    clear();
    // Single-message geometry is unchanged, including the footer.
    v.options_notice = {};
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has_at("SAVED", 22, 172, 1,
                  kModernStockMenuPalette.title_yellow));
    assert(has_at("L/R CHANGE   B BACK", 22, 185, 1,
                  kModernStockMenuPalette.cursor_blue));
    assert(!has("SAVED OPTIONS DAMAGED"));
    clear();
    v.options_status = {};
    v.options_notice = "SAVED OPTIONS DAMAGED";
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has_at("SAVED OPTIONS DAMAGED", 22, 172, 1,
                  kModernMenuCheckerLegibleGrey));
    assert(has_at("L/R CHANGE   B BACK", 22, 185, 1,
                  kModernStockMenuPalette.cursor_blue));
    clear();
    v.options_status = "SAVED";
    v.options_notice = {};
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("SETTINGS"));
    // Native-wide Options uses the same authoritative five rows, but the
    // focus label and adjustable value occupy two stable presentation
    // columns instead of depending on whitespace padding.
    assert(has("> VSYNC") && has("< ON >"));
    assert(has("  DISPLAY") && has("WINDOWED"));
    assert(!has("> VSYNC    < ON >"));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 196 && t.y == 111 && t.cells == 6 &&
                   t.colour == kModernStockMenuPalette.title_yellow;
        }));
    bounds(342,224);
    clear();
    // The host glyph callback does not clip. A long future or localized
    // setting name must stop before the real value column instead of
    // drawing yellow text over the setting's authoritative ON/OFF value.
    v.options_rows[1].label =
        "PRESENTATION_MODE_WITH_MORE_CHARACTERS_THAN_THE_COLUMN";
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    const auto option_label = std::find_if(
        painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 22 && t.y == 111 &&
                   t.colour == kModernStockMenuPalette.title_yellow;
        });
    assert(option_label != painted_text.end());
    assert(option_label->cells == 20);
    assert(option_label->x + static_cast<int>(option_label->cells) *
               8 * option_label->size <= 188);
    assert(has("< ON >"));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 196 && t.y == 111 && t.cells == 6;
        }));
    bounds(342,224);
    clear();
    v.options_rows[1].label = "VSYNC";
    v.options_controls_help = true;
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("HELP") && !has("SETTINGS"));
    bounds(342,224);
    clear();
    v.options_controls_help = false;
    v.options_selected = 3; // Controls opens with A, not left/right
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("A SELECT   B BACK"));
    assert(!has("L/R CHANGE   B BACK"));
    clear();
    v.options_selected = 1;
    v.options_controls_help = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("LEFT/RIGHT  CHANGE") && has("B  CLOSE HELP"));
    assert(!has("X  RACER SETUP"));
    assert(!has("> VSYNC    < ON >"));
    clear();

    // Pause reuses the same OPTIONS state while leaving guest/pause routing
    // to the existing native owner; both 1x and 2x native pause geometries.
    v.options_controls_help = false;
    assert(render_modern_native_pause_destination(
        painter,scratch,256,256,224,v));
    assert(has("UNIRACERS"));
    assert(has("GAME PAUSED"));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 16 && t.y == 46 && t.cells == 11 &&
                   t.size == 1 &&
                   t.colour == kModernMenuCheckerLegibleGrey;
        }));
    assert(has("OPTIONS"));
    assert(has("> VSYNC    < ON >"));
    bounds(256,224);
    clear();
    // The pause header follows the same explicit regional flag as the root
    // presentation. Modern must never relabel European Unirally as USA art.
    v.europe = true;
    assert(render_modern_native_pause_destination(
        painter,scratch,256,256,224,v));
    assert(has("UNIRALLY") && !has("UNIRACERS"));
    assert(has("GAME PAUSED") && has("OPTIONS"));
    bounds(256,224);
    clear();
    v.europe = false;
    assert(render_modern_native_pause_destination(
        painter,scratch,512,512,448,v));
    assert(has("GAME PAUSED"));
    assert(has("OPTIONS"));
    bounds(512,448);
    clear();
    // Pause is a child of the real Modern framebuffer, not a fixed 4:3
    // island. Assert the first opaque root paint uses matching 320-logical
    // wide geometry, while 256-wide/four-times compact stays 240-logical.
    assert(render_modern_native_pause_destination(
        painter,scratch,342,342,224,v));
    assert(!painted.empty());
    assert(painted.front().x == 11 && painted.front().y == 10);
    assert(painted.front().w == 320 && painted.front().h == 204);
    assert(has("GAME PAUSED") && has("OPTIONS"));
    assert(std::any_of(painted_text.begin(), painted_text.end(),
        [](const PaintedText& t) {
            return t.x == 19 && t.y == 46 && t.cells == 11 &&
                   t.size == 1 &&
                   t.colour == kModernMenuCheckerLegibleGrey;
        }));
    bounds(342,224);
    clear();
    assert(render_modern_native_pause_destination(
        painter,scratch,684,684,448,v));
    assert(!painted.empty());
    assert(painted.front().x == 22 && painted.front().y == 20);
    assert(painted.front().w == 640 && painted.front().h == 408);
    bounds(684,448);
    clear();
    assert(render_modern_native_pause_destination(
        painter,scratch,1368,1368,896,v));
    assert(has("UNIRACERS") && has("GAME PAUSED"));
    assert(has("OPTIONS"));
    assert(!painted.empty());
    assert(painted.front().x == 44 && painted.front().y == 40);
    assert(painted.front().w == 1280 && painted.front().h == 816);
    bounds(1368,896);
    clear();
    assert(render_modern_native_pause_destination(
        painter,scratch,1024,1024,896,v));
    assert(!painted.empty());
    assert(painted.front().x == 32 && painted.front().y == 40);
    assert(painted.front().w == 960 && painted.front().h == 816);
    bounds(1024,896);
    clear();
    // SDL/output window dimensions alone never certify native 342x224
    // source preparation. These sizes previously selected a false 320px
    // root because width >= 342*scale; keep the 240px fallback instead.
    assert(render_modern_native_pause_destination(
        painter,scratch,1280,1280,720,v));
    assert(!painted.empty());
    assert(painted.front().x == 400 && painted.front().y == 156);
    assert(painted.front().w == 480 && painted.front().h == 408);
    assert(has("> VSYNC    < ON >") && !has("SETTINGS"));
    bounds(1280,720);
    clear();
    assert(render_modern_native_pause_destination(
        painter,scratch,1024,1024,768,v));
    assert(!painted.empty());
    assert(painted.front().x == 272 && painted.front().y == 180);
    assert(painted.front().w == 480 && painted.front().h == 408);
    bounds(1024,768);
    clear();
    assert(!render_modern_native_pause_destination(
        painter,scratch,240,240,224,v));
    assert(painted.empty());
    v.options_open = false;
    v.two_seat_join_open = true;
    v.join_p1_name = "MIKE";
    v.join_p2_name = "MARTIN";
    v.join_p1_stock = "MIKE";
    v.join_p2_stock = "MARTIN";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("TWO PLAYER"));
    assert(has("  P1  MIKE  ACTIVE"));
    assert(!has("> P1  MIKE  ACTIVE"));
    assert(has("> P2  MARTIN  CHOOSE"));
    assert(has("RACE AS: MIKE / MARTIN"));
    assert(std::count_if(painted.begin(), painted.end(),
        [](const Rectangle& box) {
            return box.colour == kModernStockMenuPalette.cursor_blue;
        }) == 1); // only P2 owns the selection band
    clear();
    v.join_p1_confirmed = true;
    v.join_p2_confirmed = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("  P1  MIKE  READY"));
    assert(has("  P2  MARTIN  READY"));
    assert(std::count_if(painted.begin(), painted.end(),
        [](const Rectangle& box) {
            return box.colour == kModernStockMenuPalette.cursor_blue;
        }) == 0);
    clear();
    v.join_p1_confirmed = false;
    v.join_p2_confirmed = false;
    // Long profile names must not consume the READY/CHOOSE status. The full
    // identity remains in the product catalog; compact copy marks overflow.
    v.join_p1_name = "ABCDEFGHIJKLMNOPQRST";
    v.join_p2_name = "QRSTUVWXYZABCDEFGHIJ";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("  P1  ABCDEFGHIJKL.  ACTIVE"));
    assert(has("> P2  QRSTUVWXYZAB.  CHOOSE"));
    bounds(256,224);
    clear();
    // In 342-wide composition both complete 20-character names fit.
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("  P1  ABCDEFGHIJKLMNOPQRST  ACTIVE"));
    assert(has("> P2  QRSTUVWXYZABCDEFGHIJ  CHOOSE"));
    bounds(342,224);
    clear();

    v.two_seat_join_open = false;
    v.first_racer_open = true;
    v.first_racer_preset_name = "ANDREW";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("RACERS") && has("> PRESET: ANDREW"));
    assert(has("FIRST RACER") && has("SEPARATE SAVED PROGRESS"));
    assert(has("A CREATE   B CANCEL"));
    clear();
    v.first_racer_is_second = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("SECOND RACER"));
    bounds(256,224);
    clear();
    v.first_racer_is_second = false;
    v.first_racer_is_switch = true;
    v.first_racer_created = true;
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,320,wide,v));
    assert(has("P1 CHANGES ON RESTART"));
    assert(!has("NO LIVE RACER CHANGE"));
    assert(has("SAVED FOR NEXT LAUNCH"));
    assert(has("QUIT AND RESTART GAME"));
    // Native B dismisses this child panel; quitting is a separate root B
    // action. Do not advertise a shortcut that does not exist.
    assert(has("B BACK  THEN QUIT"));
    assert(!has("B BACK / QUIT"));
    assert(has("PROFILE")); // native-wide stage identity, never a new route
    clear();

    v.first_racer_open = false;
    v.unbound_two_player_warning_open = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("LOCAL 2P STILL PLAYABLE"));
    assert(has("2P RESULTS NOT SAVED"));
    assert(!has("STOCK 2P STILL PLAYABLE"));
    assert(!has("NO MATCH HISTORY SAVED")); // replaced by clearer result policy
    assert(has("P1 A ANYWAY   B BACK"));
    clear();
    assert(!render_modern_native_destination({},scratch,256,224,
                                              1,240,original,v));
    assert(!render_modern_native_destination(painter,nullptr,256,224,
                                              1,240,original,v));
    assert(!render_modern_native_destination(painter,scratch,256,224,
                                              1,240,{40,10,240,204},v));
    assert(painted.empty()); // reject before touching any host pixel
    std::puts("PASS: Modern native destination views, 4:3 and 16:9 layouts");
}

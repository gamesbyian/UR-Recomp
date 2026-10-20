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
struct PaintedText { int x, y, size; std::size_t cells; };
std::vector<PaintedText> painted_text;
struct Rectangle {int x,y,w,h; std::uint32_t colour;};
std::vector<Rectangle> painted;
void fill(std::uint32_t*, int, int, int x, int y, int w, int h,
          std::uint32_t colour) { painted.push_back({x,y,w,h,colour}); }
void stroke(std::uint32_t*, int, int, int x, int y, int w, int h,
            std::uint32_t colour) { painted.push_back({x,y,w,h,colour}); }
void draw(std::uint32_t*, int, int, int x, int y, const char* str,
          std::uint32_t, int size) {
    // Preserve actual text/scale and catch glyph overdraw on both surfaces.
    text_seen.emplace_back(str);
    painted_text.push_back({x,y,size,std::string(str).size()});
    assert(x >= 0 && y >= 0 && size > 0);
}
bool has(std::string_view text) {
    return std::find(text_seen.begin(), text_seen.end(),
                     std::string(text)) != text_seen.end();
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
    constexpr HostOverlayRect wide{12,10,318,204};
    ModernRootOverlayView v{};
    const auto narrow = modern_native_destination_canvas(256,224,1,240,original);
    const auto expanded = modern_native_destination_canvas(342,224,1,318,wide);
    assert(narrow.scale == 1 && !narrow.wide && narrow.w == 218);
    assert(expanded.scale == 1 && expanded.wide && expanded.w == 296);
    assert(!modern_native_destination_canvas(256,224,1,320,original).scale);
    assert(!modern_native_destination_canvas(256,224,0,240,original).scale);
    assert(!modern_native_destination_canvas(256,224,1,240,{40,10,240,204}).scale);
    assert(!modern_native_destination_is_open(v));
    assert(!render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(painted.empty());

    v.practice_picker_open = true;
    v.practice_course_name = "ZOOM ZOO";
    v.practice_tour_name = "CRAWLER";
    v.practice_kind_label = "CIRCUIT";
    v.practice_courses_open = 5;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("PRACTICE") && has("ZOOM ZOO") && has("CRAWLER  /  CIRCUIT"));
    assert(has("5 STOCK-UNLOCKED COURSES"));
    // Tour and course navigation are separate real native input actions.
    assert(has("UP/DN COURSE   L/R TOUR"));
    assert(has("A START   B BACK"));
    bounds(256,224);
    clear();
    v.practice_picker_open = false;
    v.practice_launch_pending = true;
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,318,wide,v));
    assert(has("ENTERING ORIGINAL COURSE"));
    assert(has("WAIT FOR SOURCE GO") && has("B CANCEL"));
    bounds(342,224);
    clear();

    // Presentation density is a strict integer transform, not a wider-font
    // guess. The same already-authoritative 342x224 layout also fits 4x.
    constexpr HostOverlayRect wide4{48,40,1272,816};
    assert(render_modern_native_destination(painter,scratch,1368,896,
                                             4,318,wide4,v));
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
    assert(has("UP/DOWN PAGE  B BACK"));
    clear();
    v.read_only_records_two_player = true;
    v.records_status = "MY 2P 1  UNAVAILABLE 3";
    v.records_recent = "W 1  L 0  D 0";
    v.records_detail = "LAST 01 WIN 00:28.76";
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,318,wide,v));
    assert(has("> 2P MATCHES"));
    assert(has("LAST 01 WIN 00:28.76"));
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
    assert(has("SAVED") && has("OPTIONS"));
    clear();
    v.options_controls_help = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("LEFT/RIGHT  CHANGE") && has("X  RACER SETUP"));
    assert(!has("> VSYNC    < ON >"));
    clear();

    // Pause reuses the same OPTIONS state while leaving guest/pause routing
    // to the existing native owner; both 1x and 2x native pause geometries.
    v.options_controls_help = false;
    assert(render_modern_native_pause_destination(
        painter,scratch,256,256,224,v));
    assert(has("UNIRACERS"));
    assert(has("PAUSED - GUEST FROZEN"));
    assert(has("OPTIONS"));
    assert(has("> VSYNC    < ON >"));
    bounds(256,224);
    clear();
    assert(render_modern_native_pause_destination(
        painter,scratch,512,512,448,v));
    assert(has("PAUSED - GUEST FROZEN"));
    assert(has("OPTIONS"));
    bounds(512,448);
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
    assert(has("> P1  MIKE  ACTIVE"));
    assert(has("> P2  MARTIN  CHOOSE"));
    assert(has("STOCK: MIKE / MARTIN"));
    clear();

    v.two_seat_join_open = false;
    v.first_racer_open = true;
    v.first_racer_preset_name = "ANDREW";
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("RACERS") && has("> PRESET: ANDREW"));
    assert(has("A CREATE   B CANCEL"));
    clear();
    v.first_racer_is_switch = true;
    v.first_racer_created = true;
    assert(render_modern_native_destination(painter,scratch,342,224,
                                             1,318,wide,v));
    assert(has("ACTIVE P1 AT NEXT BOOT"));
    assert(has("SAVED FOR NEXT LAUNCH"));
    assert(has("QUIT AND RESTART GAME"));
    clear();

    v.first_racer_open = false;
    v.unbound_two_player_warning_open = true;
    assert(render_modern_native_destination(painter,scratch,256,224,
                                             1,240,original,v));
    assert(has("NO MATCH HISTORY SAVED"));
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

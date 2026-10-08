#include "modern_tour_overview_visual_style.hpp"
#include "modern_overlay_text_fit.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto classic = modern_tour_overview_visual_style(256);
    assert(classic.panel_width_logical == 240);
    assert(classic.title_glyph_scale == 2);
    assert(classic.title_x_logical + 13 * 8 * classic.title_glyph_scale
           <= classic.panel_width_logical - 8);
    assert(classic.title_y_logical + 8 * classic.title_glyph_scale <
           classic.header_height_logical);
    assert(modern_overlay_text_cells(classic.panel_width_logical) == 28u);

    // These host roles are derived from the ROM's BG2 menu palette:
    // title-yellow and detail-grey, never an invented unlocked medal.
    assert(classic.palette.title_yellow == 0xFFF8F800u);
    assert(classic.palette.secondary_grey == 0xFF989898u);
    assert(classic.palette.cursor_blue == 0xFFA0D0F8u);

    const auto narrow = modern_tour_overview_visual_style(200);
    assert(narrow.panel_width_logical == 184);
    assert(narrow.title_glyph_scale == 1);
    assert(narrow.title_x_logical + 13 * 8 <=
           narrow.panel_width_logical - 8);

    const auto wide = modern_tour_overview_visual_style(342);
    assert(wide.panel_width_logical == 318);
    assert(wide.title_glyph_scale == 2);
    assert(modern_overlay_text_cells(wide.panel_width_logical) == 37u);

    const auto ultrawide = modern_tour_overview_visual_style(480);
    assert(ultrawide.panel_width_logical == 324);
    assert(ultrawide.title_glyph_scale == 2);

    assert(modern_tour_overview_visual_style(32).panel_width_logical == 0);
    assert(modern_tour_overview_visual_style(0).panel_width_logical == 0);

    // Read-only rows are 16 logical pixels apart, never painted as active
    // cursor choices. The footer remains inside the 207px panel.
    constexpr int kRows = 8;
    constexpr int kRowStart = 51;
    constexpr int kRowPitch = 16;
    assert(kRowStart + (kRows - 1) * kRowPitch + 8 < 188);
    assert(188 + 8 < 207);

    // The medal/state column is anchored at the right edge rather than
    // shifting with each tour name. The primary name yields to status.
    const auto row_cells =
        modern_overlay_text_cells(classic.panel_width_logical);
    const auto bronze = modern_tour_overview_row(
        1, true, "Crawler", "BRONZE", row_cells);
    const auto silver = modern_tour_overview_row(
        2, true, "Jumper", "SILVER", row_cells);
    const auto gold = modern_tour_overview_row(
        8, true, "Sprinter", "GOLD", row_cells);
    const auto not_started = modern_tour_overview_row(
        3, true, "Shuffler", "NOT STARTED", row_cells);
    assert(bronze.size() == row_cells);
    assert(silver.size() == row_cells);
    assert(gold.size() == row_cells);
    assert(not_started.size() == row_cells);
    assert(bronze.substr(row_cells - 6) == "BRONZE");
    assert(silver.substr(row_cells - 6) == "SILVER");
    assert(gold.substr(row_cells - 4) == "GOLD");
    assert(not_started.substr(row_cells - 11) == "NOT STARTED");
    assert(bronze.substr(0, 10) == "1. Crawler");

    const auto compact = modern_tour_overview_row(
        5, true, "LONG TOUR NAME", "NOT STARTED", 19);
    assert(compact.size() == 19);
    assert(compact.substr(8) == "NOT STARTED");
    assert(compact.substr(0, 3) == "5. ");

    // Even a deliberately supplied hidden name/medal must not be rendered.
    const auto locked = modern_tour_overview_row(
        4, false, "Hunter", "GOLD", row_cells);
    assert(locked == "4. LOCKED TOUR");
    assert(locked.find("Hunter") == std::string::npos);
    assert(locked.find("GOLD") == std::string::npos);

    assert(modern_tour_overview_row(
        0, true, "Crawler", "GOLD", row_cells).empty());
    assert(modern_tour_overview_row(
        9, true, "Hunter", "GOLD", row_cells).empty());
    assert(modern_tour_overview_row(
        1, true, "Crawler", "GOLD", 0).empty());
    return 0;
}

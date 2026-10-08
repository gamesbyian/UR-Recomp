#include "modern_tour_overview_visual_style.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

int main() {
    const auto original = modern_tour_overview_visual_style(256);
    assert(original.panel_width_logical == 240);
    assert(original.title_glyph_scale == 2);
    assert(16 + 13 * 8 * original.title_glyph_scale <=
           original.panel_width_logical);
    assert(original.title_y_logical + 8 * original.title_glyph_scale < 26);
    assert(original.first_tour_y_logical + 7 * original.row_spacing_logical < 188);

    assert(original.title_yellow == 0xFFF8F800u);
    assert(original.secondary_grey == 0xFF989898u);
    assert(original.panel_outline == 0xFF989898u);

    const auto narrow = modern_tour_overview_visual_style(200);
    assert(narrow.panel_width_logical == 184);
    assert(narrow.title_glyph_scale == 1);
    const auto wide = modern_tour_overview_visual_style(342);
    assert(wide.panel_width_logical == 318);
    assert(wide.title_glyph_scale == 2);
    const auto ultrawide = modern_tour_overview_visual_style(480);
    assert(ultrawide.panel_width_logical == 324);
    assert(ultrawide.title_glyph_scale == 2);
    assert(modern_tour_overview_visual_style(32).panel_width_logical == 0);

    const auto cells = modern_overlay_text_cells(original.panel_width_logical);
    assert(cells == 28);
    const auto bronze = modern_tour_overview_visual_row(
        1, true, "Crawler", "BRONZE", cells);
    const auto silver = modern_tour_overview_visual_row(
        2, true, "Jumper", "SILVER", cells);
    const auto gold = modern_tour_overview_visual_row(
        8, true, "Sprinter", "GOLD", cells);
    const auto none = modern_tour_overview_visual_row(
        3, true, "Shuffler", "NOT STARTED", cells);
    assert(bronze.size() == cells && silver.size() == cells);
    assert(gold.size() == cells && none.size() == cells);
    assert(bronze.substr(cells - 6) == "BRONZE");
    assert(silver.substr(cells - 6) == "SILVER");
    assert(gold.substr(cells - 4) == "GOLD");
    assert(none.substr(cells - 11) == "NOT STARTED");
    assert(bronze.substr(0, 10) == "1. CRAWLER" ||
           bronze.substr(0, 10) == "1. Crawler");

    // Hidden tours must never display the supplied name/medal even when
    // both inputs contain a secret. Their numbered locked slot remains.
    const auto hidden = modern_tour_overview_visual_row(
        4, false, "HUNTER", "GOLD", cells);
    assert(hidden == "4. LOCKED TOUR");
    assert(hidden.find("HUNTER") == std::string::npos);
    assert(hidden.find("GOLD") == std::string::npos);

    // Unusually narrow panels truncate the name before the medal, keeping
    // the status visible and avoiding overflowing the game viewport.
    const auto compact = modern_tour_overview_visual_row(
        5, true, "LONG TOUR NAME", "NOT STARTED", 19);
    assert(compact.size() == 19);
    assert(compact.substr(8) == "NOT STARTED");
    assert(compact.substr(0, 3) == "5. ");
    assert(modern_tour_overview_visual_row(
        0, true, "Crawler", "GOLD", cells).empty());
    assert(modern_tour_overview_visual_row(
        9, true, "Hunter", "GOLD", cells).empty());
    assert(modern_tour_overview_visual_row(
        1, true, "Crawler", "GOLD", 0).empty());
    return 0;
}

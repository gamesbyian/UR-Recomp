#include "modern_onboarding_visual_style.hpp"
#include "modern_overlay_text_fit.hpp"

#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    constexpr std::string_view title = "HOW TO RIDE";
    constexpr int kTitleGlyphWidth = 8;

    const auto classic = modern_onboarding_visual_style(256);
    assert(classic.panel_width_logical == 240);
    assert(classic.panel_height_logical == 206);
    assert(classic.title_glyph_scale == 2);
    assert(classic.title_x_logical +
           static_cast<int>(title.size()) *
               kTitleGlyphWidth * classic.title_glyph_scale
           <= classic.panel_width_logical - 8);
    assert(classic.title_y_logical +
           8 * classic.title_glyph_scale <
           classic.header_height_logical);
    assert(classic.header_height_logical < classic.subtitle_y_logical);

    // Stock BG2 palette roles are already approved shared presentation
    // tokens; this helper must not invent new yellow/grey/blue colors.
    assert(classic.palette.title_yellow == 0xFFF8F800u);
    assert(classic.palette.secondary_grey == 0xFF989898u);
    assert(classic.palette.cursor_blue == 0xFFA0D0F8u);

    const auto narrow = modern_onboarding_visual_style(200);
    assert(narrow.panel_width_logical == 184);
    assert(narrow.title_glyph_scale == 1);
    assert(narrow.title_x_logical +
           static_cast<int>(title.size()) * kTitleGlyphWidth <=
           narrow.panel_width_logical - 8);

    const auto wide = modern_onboarding_visual_style(342);
    assert(wide.panel_width_logical == 324);
    assert(wide.title_glyph_scale == 2);
    const auto ultrawide = modern_onboarding_visual_style(480);
    assert(ultrawide.panel_width_logical == 324);

    // The fixed instruction/footer rows remain bounded by 206px height.
    constexpr int instruction_rows[] = {42, 57, 72, 87};
    constexpr int shortcut_rows[] = {142, 157, 172, 187};
    for (int y : instruction_rows)
        assert(y >= classic.subtitle_y_logical + 8 && y + 8 < 107);
    for (int y : shortcut_rows)
        assert(y >= 142 && y + 8 < classic.panel_height_logical);

    const auto classic_cells =
        modern_overlay_text_cells(classic.panel_width_logical);
    assert(classic_cells == 28u);
    const auto short_cells =
        modern_overlay_text_cells(narrow.panel_width_logical);
    assert(short_cells == 21u);
    const auto clipped = fit_modern_overlay_text(
        "F7/PAD L PROGRESS F1 HELP", short_cells);
    assert(clipped.size() == short_cells);

    assert(modern_onboarding_visual_style(0).panel_width_logical == 0);
    assert(modern_onboarding_visual_style(32).panel_width_logical == 0);
    return 0;
}

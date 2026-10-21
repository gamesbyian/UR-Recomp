// ROM-free executable contract for the shared Modern UI accessibility
// primitives in native/product/modern_ui_access.hpp.
#include "native/product/modern_ui_access.hpp"
#include "native/product/modern_menu_visual_grammar.hpp"

#include <cstdio>
#include <cstdlib>

using namespace ur::product;

#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d %s\n", \
    __FILE__, __LINE__, #c); std::exit(1); } } while (0)

// Contrast oracle: black/white is exactly 21:1; identical colours 1:1.
static_assert(modern_ui_contrast_x100(0xFF000000u, 0xFFFFFFFFu) >= 2099);
static_assert(modern_ui_contrast_x100(0xFF808080u, 0xFF808080u) == 100);
// Documented measured gap: stock grey fails on the bright checker cell,
// the shipped checker-legible grey passes on both cells.
static_assert(!modern_ui_text_legible(0xFF989898u, 0xFF505050u));
static_assert(modern_ui_text_legible(kModernMenuCheckerLegibleGrey, 0xFF505050u));
static_assert(modern_ui_text_legible_on_all(
    kModernMenuCheckerLegibleGrey,
    std::array<std::uint32_t, 2>{{0xFF2F2F2Fu, 0xFF505050u}}));
// Yellow title and cursor blue clear the 3:1 indicator floor on the panel.
static_assert(modern_ui_contrast_x100(0xFFF8F800u, 0xFF2F2F2Fu) >= kModernUiTextContrastX100);
static_assert(modern_ui_contrast_x100(kModernMenuCursorLight, 0xFF283058u) >= kModernUiFocusContrastX100);

static_assert(modern_ui_min_text_scale(8) == 1);
static_assert(modern_ui_min_text_scale(17) == 3);
static_assert(modern_ui_min_text_scale(40) == 0);

int main() {
    // Reference luminance cross-check against the float definition.
    CHECK(modern_ui_contrast_x100(0xFF989898u, 0xFF505050u) >= 270 &&
          modern_ui_contrast_x100(0xFF989898u, 0xFF505050u) <= 290);  // ~2.80

    // Scaling at the shipped outputs.
    auto s = modern_ui_integer_scale(342, 224, 1280, 720);
    CHECK(s.factor == 3 && s.viewport.width == 1026 && s.viewport.height == 672);
    CHECK(s.viewport.x == 127 && s.viewport.y == 24);
    CHECK(modern_ui_integer_scale(342, 224, 1920, 1080).factor == 4);
    CHECK(modern_ui_integer_scale(342, 224, 3840, 2160).factor == 9);
    CHECK(modern_ui_integer_scale(256, 224, 1024, 768).factor == 3);
    CHECK(modern_ui_integer_scale(342, 224, 300, 700).factor == 0);
    CHECK(modern_ui_integer_scale(0, 224, 1280, 720).factor == 0);

    // Safe areas stay inside the canvas, title inside action.
    for (const int w : {256, 342}) {
        const ModernUiRect canvas{0, 0, w, 224};
        const auto t = modern_ui_title_safe(w, 224);
        const auto a = modern_ui_action_safe(w, 224);
        CHECK(modern_ui_rect_contains(canvas, a));
        CHECK(modern_ui_rect_contains(a, t));
        CHECK(t.x >= 8 && t.y >= 11);
        CHECK(t.x * 2 + t.width == w);
    }
    CHECK(modern_ui_title_safe(0, 0).width == 0);
    CHECK(modern_ui_title_safe(100000, 224).width == 0);

    // Reduced motion resolves to the settled frame immediately.
    CHECK(modern_ui_motion_frame(3, 39, false) == 3);
    CHECK(modern_ui_motion_frame(3, 39, true) == 39);
    CHECK(modern_ui_motion_frame(100, 39, false) == 39);

    // Focus geometry: bar plus outline, fully inside the row.
    const ModernUiRect row{16, 40, 200, 24};
    const auto g = modern_ui_focus_geometry(row, 3);
    CHECK(g.valid && g.bar.width == 9);
    CHECK(modern_ui_rect_contains(row, g.bar));
    for (const auto& edge : g.outline) CHECK(modern_ui_rect_contains(row, edge));
    CHECK(!modern_ui_focus_geometry({0, 0, 4, 24}, 1).valid);
    CHECK(!modern_ui_focus_geometry(row, 0).valid);

    // Disabled semantics: skipped, wrap, fail closed, reason required.
    using R = ModernUiDisabledReason;
    const std::array<ModernUiRowState, 5> rows{{
        {true, R::None}, {false, R::Locked}, {true, R::None},
        {false, R::NoProfile}, {true, R::Busy} /* inconsistent */}};
    CHECK(modern_ui_next_enabled(rows, 0, 1) == 2);
    CHECK(modern_ui_next_enabled(rows, 2, 1) == 0);   // skips 3 and bad 4
    CHECK(modern_ui_next_enabled(rows, 0, -1) == 2);  // wraps past 4,3
    CHECK(modern_ui_next_enabled(rows, 99, 1) == 0);
    CHECK(modern_ui_next_enabled(rows, 0, 0) == -1);
    CHECK(!modern_ui_may_activate(rows[1]));
    CHECK(!modern_ui_may_activate(rows[4]));
    CHECK(modern_ui_may_activate(rows[0]));
    const std::array<ModernUiRowState, 2> none{{{false, R::Locked}, {false, R::Busy}}};
    CHECK(modern_ui_next_enabled(none, 0, 1) == -1);
    const std::array<ModernUiRowState, 1> only{{{true, R::None}}};
    CHECK(modern_ui_next_enabled(only, 0, 1) == 0);

    std::puts("PASS: Modern UI accessibility primitives");
    return 0;
}

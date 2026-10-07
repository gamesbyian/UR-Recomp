#include "modern_main_menu_strip.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    // Nothing to continue: no strip.
    assert(build_modern_main_menu_strip({}).row_count == 0);

    // Recent only.
    {
        ModernMainMenuStripInput input;
        input.recent_course = std::string_view("Skier");
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.row_count == 1);
        assert(strip.rows[0] == "F6/R RECENT Skier");
    }

    // Unique Next Event leads, Recent follows.
    {
        ModernMainMenuStripInput input;
        input.tour = ModernMainMenuTourEntry{"Monster", "Crawler", 4};
        input.recent_course = std::string_view("Skier");
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.row_count == 2);
        assert(strip.rows[0] == "F3/Y NEXT EVENT Monster");
        assert(strip.rows[1] == "F6/R RECENT Skier");
    }

    // Ambiguous tour shows the tour summary instead of guessing an event.
    {
        ModernMainMenuStripInput input;
        input.tour = ModernMainMenuTourEntry{{}, "Crawler", 2};
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.row_count == 1);
        assert(strip.rows[0] == "F3/Y TOUR Crawler 2/5");
    }

    // Every row fits the strip; long names truncate, progress never does.
    {
        ModernMainMenuStripInput input;
        input.tour = ModernMainMenuTourEntry{
            {}, "AVeryLongTourNameThatCannotFit", 9};
        input.recent_course =
            std::string_view("AnExtremelyLongCourseNameForTesting");
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.row_count == 2);
        for (std::size_t i = 0; i < strip.row_count; ++i) {
            assert(strip.rows[i].size() <= kModernMainMenuStripMaxChars);
        }
        assert(strip.rows[0].size() == kModernMainMenuStripMaxChars);
        assert(strip.rows[0].substr(strip.rows[0].size() - 4) == " 5/5");
        assert(strip.rows[1].rfind("F6/R RECENT ", 0) == 0);

        input.tour = ModernMainMenuTourEntry{
            "AnotherExtremelyLongCourseName", "Crawler", 4};
        const auto next = build_modern_main_menu_strip(input);
        assert(next.rows[0].size() == kModernMainMenuStripMaxChars);
        assert(next.rows[0].rfind("F3/Y NEXT EVENT ", 0) == 0);
    }

    // Every shipping course name fits without truncation.
    for (const char* name : {"Fire Escape", "Wario Paint", "Hairpin Hill", "Little Dipper"}) {
        ModernMainMenuStripInput input;
        input.tour = ModernMainMenuTourEntry{name, "Shuffler", 4};
        input.recent_course = std::string_view(name);
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.rows[0] == std::string("F3/Y NEXT EVENT ") + name);
        assert(strip.rows[1] == std::string("F6/R RECENT ") + name);
    }

    // The longest tour name keeps its progress without truncation.
    {
        ModernMainMenuStripInput input;
        input.tour = ModernMainMenuTourEntry{{}, "Shuffler", 3};
        const auto strip = build_modern_main_menu_strip(input);
        assert(strip.rows[0] == "F3/Y TOUR Shuffler 3/5");
    }

    return 0;
}

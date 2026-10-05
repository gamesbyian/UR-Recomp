#include "quick_practice_catalog.hpp"

#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    static_assert(kQuickPracticeCourses.size() == 45);
    static_assert(quick_practice_catalog_consistent());

    const auto* dragster = quick_practice_course(0);
    assert(dragster);
    assert(dragster->name == std::string_view("Dragster"));
    assert(dragster->tour_name == std::string_view("Crawler"));
    assert(dragster->kind == QuickPracticeCourseKind::Race);

    const auto* bowl = quick_practice_course(2);
    assert(bowl);
    assert(bowl->kind == QuickPracticeCourseKind::Stunt);

    const auto* hunter = quick_practice_course(44);
    assert(hunter);
    assert(hunter->name == std::string_view("To and Fro"));
    assert(hunter->tour_name == std::string_view("Hunter"));
    assert(hunter->tour_slot == 4);

    assert(quick_practice_course(45) == nullptr);
    assert(quick_practice_kind_label(QuickPracticeCourseKind::Race) == "RACE");
    assert(quick_practice_kind_label(QuickPracticeCourseKind::Circuit) == "CIRCUIT");
    assert(quick_practice_kind_label(QuickPracticeCourseKind::Stunt) == "STUNT");
    return 0;
}

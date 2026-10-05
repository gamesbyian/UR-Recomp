#include "quick_practice_selection_view.hpp"

#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    auto state = open_quick_practice_selection(0);
    auto view = quick_practice_selection_view(state);
    assert(view.valid);
    assert(view.course_name == std::string_view("Dragster"));
    assert(view.tour_name == std::string_view("Crawler"));
    assert(view.kind_label == std::string_view("RACE"));
    assert(view.course_number == 1 && view.course_count == 45);
    assert(view.tour_number == 1 && view.tour_count == 9);
    assert(view.slot_number == 1 && view.slot_count == 5);

    state = open_quick_practice_selection(37);
    view = quick_practice_selection_view(state);
    assert(view.valid);
    assert(view.course_name == std::string_view("Little Dipper"));
    assert(view.tour_name == std::string_view("Sprinter"));
    assert(view.kind_label == std::string_view("STUNT"));
    assert(view.course_number == 38);
    assert(view.tour_number == 8);
    assert(view.slot_number == 3);

    state = open_quick_practice_selection(44);
    view = quick_practice_selection_view(state);
    assert(view.valid);
    assert(view.course_name == std::string_view("To and Fro"));
    assert(view.tour_name == std::string_view("Hunter"));
    assert(view.kind_label == std::string_view("CIRCUIT"));
    assert(view.course_number == 45);
    assert(view.tour_number == 9);
    assert(view.slot_number == 5);

    const auto cancelled = quick_practice_selection_apply(
        state, QuickPracticeSelectionCommand::Cancel);
    view = quick_practice_selection_view(cancelled.state);
    assert(!view.valid);

    return 0;
}

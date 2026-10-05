#include "quick_practice_overlay_model.hpp"
#include "quick_practice_selection.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    auto selection = open_quick_practice_selection(0);
    auto rows = quick_practice_overlay_rows(
        quick_practice_selection_view(selection));
    assert(rows.valid);
    assert(rows.rows[0] == "QUICK PRACTICE");
    assert(rows.rows[1] == "Dragster");
    assert(rows.rows[2] == "Crawler  RACE");
    assert(rows.rows[3] == "COURSE 1 / 45");
    assert(rows.rows[4] == "TOUR 1 / 9  TRACK 1 / 5");
    assert(rows.rows[5] == "UP/DOWN COURSE  LEFT/RIGHT TOUR");
    assert(rows.rows[6] == "ENTER/A PLAY  ESC/B CANCEL");

    selection = open_quick_practice_selection(37);
    rows = quick_practice_overlay_rows(
        quick_practice_selection_view(selection));
    assert(rows.valid);
    assert(rows.rows[1] == "Little Dipper");
    assert(rows.rows[2] == "Sprinter  STUNT");
    assert(rows.rows[3] == "COURSE 38 / 45");
    assert(rows.rows[4] == "TOUR 8 / 9  TRACK 3 / 5");

    selection = open_quick_practice_selection(44);
    rows = quick_practice_overlay_rows(
        quick_practice_selection_view(selection));
    assert(rows.valid);
    assert(rows.rows[1] == "To and Fro");
    assert(rows.rows[2] == "Hunter  CIRCUIT");
    assert(rows.rows[3] == "COURSE 45 / 45");
    assert(rows.rows[4] == "TOUR 9 / 9  TRACK 5 / 5");

    const auto cancelled = quick_practice_selection_apply(
        selection, QuickPracticeSelectionCommand::Cancel);
    rows = quick_practice_overlay_rows(
        quick_practice_selection_view(cancelled.state));
    assert(!rows.valid);

    return 0;
}

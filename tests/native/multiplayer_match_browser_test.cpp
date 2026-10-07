#include "multiplayer_match_browser.hpp"

#include <cassert>
#include <string>
#include <vector>

using namespace ur::product;
using namespace ur::title;

namespace {

StoredMultiplayerMatch match(
    const char* path,
    const char* course,
    const char* p1,
    const char* p2,
    OrdinaryTwoPlayerRaceOutcome outcome) {
    StoredMultiplayerMatch stored;
    stored.run_path = path;
    stored.run.provenance.mode = "race-2p";
    stored.match.run_artifact_checksum = "0123456789abcdef";
    stored.match.context.course_id = course;
    stored.match.context.match.player1 = {
        p1, HostRacerIdentity{"MIKE", 0}};
    stored.match.context.match.player2 = {
        p2, HostRacerIdentity{"ANDREW", 1}};
    stored.match.context.match.result.player1_rider = 0;
    stored.match.context.match.result.player2_rider = 1;
    stored.match.context.match.result.player1_hundredths = 2876;
    stored.match.context.match.result.player2_hundredths = 3000;
    stored.match.context.match.result.outcome = outcome;
    return stored;
}

}  // namespace

int main() {
    MultiplayerMatchBrowser browser;
    assert(browser.empty());
    assert(browser.view() == MultiplayerMatchBrowserView::List);
    assert(!browser.move(1));
    assert(!browser.open_selected());
    assert(!browser.selected_row_presentation());
    assert(!browser.selected_detail_presentation());

    browser.set_matches({
        match("001.urrun", "course:01", "alpha", "beta",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
        match("002.urrun", "course:04", "gamma", "delta",
              OrdinaryTwoPlayerRaceOutcome::Player2Win),
    });
    assert(browser.size() == 2);
    assert(browser.selected_index() == 0);
    assert(browser.selected_match()->run_path == "001.urrun");
    assert(browser.selected_row_presentation()->course_text == "course:01");

    {
        const auto rows = browser.visible_rows(1);
        assert(rows.size() == 1);
        assert(rows[0].index == 0);
        assert(rows[0].selected);
        assert(rows[0].presentation.course_text == "course:01");
    }

    assert(browser.move(1));
    assert(browser.selected_index() == 1);
    assert(browser.selected_match()->run_path == "002.urrun");
    assert(browser.move(1));
    assert(browser.selected_index() == 0);
    assert(browser.move(-1));
    assert(browser.selected_index() == 1);

    assert(browser.open_selected());
    assert(browser.view() == MultiplayerMatchBrowserView::Detail);
    assert(!browser.move(1));
    assert(browser.visible_rows(4).empty());
    const auto detail = browser.selected_detail_presentation();
    assert(detail);
    assert(detail->summary.course_text == "course:04");
    assert(detail->outcome_text == "PLAYER 2 WIN");

    assert(browser.back());
    assert(browser.view() == MultiplayerMatchBrowserView::List);
    assert(!browser.back());

    // Replacing the catalog resets detail state and clamps selection.
    browser.open_selected();
    browser.set_matches({
        match("only.urrun", "course:02", "one", "two",
              OrdinaryTwoPlayerRaceOutcome::Draw),
    });
    assert(browser.view() == MultiplayerMatchBrowserView::List);
    assert(browser.selected_index() == 0);
    assert(browser.selected_match()->run_path == "only.urrun");

    // Larger catalogs expose a deterministic selected-centered window.
    browser.set_matches({
        match("001.urrun", "course:01", "a", "b",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
        match("002.urrun", "course:02", "a", "b",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
        match("003.urrun", "course:03", "a", "b",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
        match("004.urrun", "course:04", "a", "b",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
        match("005.urrun", "course:05", "a", "b",
              OrdinaryTwoPlayerRaceOutcome::Player1Win),
    });
    assert(browser.visible_rows(0).empty());

    {
        const auto rows = browser.visible_rows(3);
        assert(rows.size() == 3);
        assert(rows[0].index == 0);
        assert(rows[0].selected);
        assert(rows[2].index == 2);
    }

    browser.move(1);
    browser.move(1);
    {
        const auto rows = browser.visible_rows(3);
        assert(rows.size() == 3);
        assert(rows[0].index == 1);
        assert(rows[1].index == 2);
        assert(rows[1].selected);
        assert(rows[2].index == 3);
    }

    browser.move(1);
    browser.move(1);
    {
        const auto rows = browser.visible_rows(3);
        assert(rows.size() == 3);
        assert(rows[0].index == 2);
        assert(rows[2].index == 4);
        assert(rows[2].selected);
        assert(rows[2].presentation.course_text == "course:05");
    }

    browser.set_matches({});
    assert(browser.empty());
    assert(browser.selected_index() == 0);
    assert(!browser.selected_match());

    return 0;
}

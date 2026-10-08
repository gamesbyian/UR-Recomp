#include "local_tournament_panel.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

int g_failures = 0;

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        ++g_failures;
    }
}

std::vector<HostProfileCatalogEntry> catalog() {
    return {
        {"alpha", {"Alpha", 0}},
        {"bravo", {"Bravo", 1}},
        {"charlie", {"Charlie", 2}},
        {"delta", {"Delta", 3}},
    };
}

void test_course_presets() {
    check(local_tournament_course_id(0) == "course:01", "track 0 id");
    check(local_tournament_course_id(3) == "course:04", "track 3 id");
    check(local_tournament_course_name("course:01") == "Dragster",
        "course:01 name");
    check(local_tournament_course_name("course:02").empty(),
        "circuit is not an ordinary race");
    const auto first = local_tournament_course_preset(0);
    check(first.size() == 2 && first[0] == "course:01" &&
        first[1] == "course:04", "first tour preset is its two races");
    check(local_tournament_course_preset_label(0) == "CRAWLER",
        "first preset label");
    const auto all = local_tournament_course_preset(
        kLocalTournamentCoursePresetCount - 1);
    check(all.size() == 16, "all-tours preset has 16 races");
    for (const auto& id : all) {
        check(local_tournament_ordinary_race_course(id),
            "all-tours preset only ordinary races");
    }
    check(local_tournament_course_preset_label(
        kLocalTournamentCoursePresetCount - 1) == "ALL TOURS",
        "all-tours label");
    check(local_tournament_course_preset(
        kLocalTournamentCoursePresetCount).empty(), "out-of-range preset");
    for (std::size_t preset = 0;
         preset < kLocalTournamentCoursePresetCount; ++preset) {
        check(make_local_round_robin({"a", "b"},
            local_tournament_course_preset(preset)).has_value(),
            "every preset is an admissible course pool");
    }
}

void test_setup_flow() {
    auto state = make_local_tournament_setup(catalog(), "BRAVO", "alpha");
    check(state.page == LocalTournamentPanelPage::Setup, "opens on setup");
    check(state.selected == std::vector<bool>({true, true, false, false}),
        "seated pair preselected case-insensitively");
    check(local_tournament_setup_can_start(state), "pair can start");

    // Toggle charlie on.
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Down, 0);
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Down, 0);
    auto request = local_tournament_panel_navigate(
        state, LocalTournamentPanelNav::Confirm, 0);
    check(request.kind == LocalTournamentPanelRequestKind::None,
        "toggle is not a request");
    check(state.selected[2], "charlie toggled on");

    // Courses row cycles presets in both directions.
    state.cursor = state.candidates.size();
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Left, 0);
    check(state.course_preset == kLocalTournamentCoursePresetCount - 1,
        "left wraps to all tours");
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Right, 0);
    check(state.course_preset == 0, "right wraps back");

    // LEGS cycles 1..3 in both directions and with confirm.
    state.cursor = local_tournament_setup_legs_row(state);
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Left, 0);
    check(state.legs == kLocalTournamentMaxLegs, "legs left wraps to max");
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Right, 0);
    check(state.legs == 1, "legs right wraps to one");
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Confirm, 0);
    check(state.legs == 2, "confirm on legs steps");
    check(local_tournament_setup_race_count(state) == 6,
        "three racers x two legs = six races");

    // START emits the explicit roster in catalog order.
    state.cursor = local_tournament_setup_start_row(state);
    request = local_tournament_panel_navigate(
        state, LocalTournamentPanelNav::Confirm, 0);
    check(request.kind == LocalTournamentPanelRequestKind::Create,
        "start creates");
    check(request.roster ==
        std::vector<std::string>({"alpha", "bravo", "charlie"}),
        "roster in catalog order");
    check(request.courses == local_tournament_course_preset(0),
        "courses from preset");
    check(request.legs == 2, "legs carried into the create request");

    // Fewer than two entrants cannot start.
    state.selected = {true, false, false, false};
    request = local_tournament_panel_navigate(
        state, LocalTournamentPanelNav::Confirm, 0);
    check(request.kind == LocalTournamentPanelRequestKind::None,
        "single entrant refused");

    // Up from the top wraps to START.
    state.cursor = 0;
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Up, 0);
    check(state.cursor == local_tournament_setup_start_row(state), "up wraps");

    // Sideways off the courses row opens read-only history; back returns.
    local_tournament_panel_navigate(state, LocalTournamentPanelNav::Right, 0);
    check(state.page == LocalTournamentPanelPage::History,
        "setup reaches history");
    request = local_tournament_panel_navigate(
        state, LocalTournamentPanelNav::Back, 0);
    check(request.kind == LocalTournamentPanelRequestKind::None &&
        state.page == LocalTournamentPanelPage::Setup,
        "history back returns to setup without closing");

    request = local_tournament_panel_navigate(
        state, LocalTournamentPanelNav::Back, 0);
    check(request.kind == LocalTournamentPanelRequestKind::Close,
        "back closes");
}

void test_entrant_cap() {
    std::vector<HostProfileCatalogEntry> many;
    for (int i = 0; i < 10; ++i) {
        many.push_back({"p" + std::to_string(i), {"P", 0}});
    }
    auto state = make_local_tournament_setup(many, "p0", "p1");
    for (std::size_t i = 2; i < 10; ++i) {
        state.cursor = i;
        local_tournament_panel_navigate(
            state, LocalTournamentPanelNav::Confirm, 0);
    }
    check(local_tournament_setup_selected_count(state) ==
        kLocalTournamentMaxEntrants, "selection capped at eight");
}

void test_overview_and_fixtures() {
    auto made = make_local_round_robin(
        {"alpha", "bravo", "charlie"}, local_tournament_course_preset(0));
    check(made.has_value(), "three-way round robin");
    const auto& state = *made;
    check(state.fixtures.size() == 3, "three fixtures");

    const auto seated = local_tournament_seated_fixture(
        state, "CHARLIE", "alpha");
    check(seated.has_value(), "seated pair has a fixture");
    if (seated) {
        check(local_tournament_fixture_playable_by(
            state, *seated, "alpha", "charlie"), "playable either seat order");
        check(!local_tournament_fixture_playable_by(
            state, *seated, "alpha", "bravo"), "other pair cannot play it");
    }
    check(!local_tournament_seated_fixture(state, "alpha", "delta"),
        "non-entrant has no fixture");
    check(!local_tournament_complete(state), "not complete");

    LocalTournamentPanelState panel;
    panel.page = LocalTournamentPanelPage::Standings;
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Left, 3);
    check(panel.page == LocalTournamentPanelPage::History,
        "left from standings reaches history");
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Back, 3);
    check(panel.page == LocalTournamentPanelPage::Standings,
        "back from history returns to standings");
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Right, 3);
    check(panel.page == LocalTournamentPanelPage::Fixtures, "tab to fixtures");
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Right, 3);
    check(panel.page == LocalTournamentPanelPage::History,
        "right from fixtures reaches history");
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Right, 3);
    check(panel.page == LocalTournamentPanelPage::Standings,
        "history returns to standings");
    panel.page = LocalTournamentPanelPage::Fixtures;
    local_tournament_panel_navigate(panel, LocalTournamentPanelNav::Up, 3);
    check(panel.fixture_cursor == 2, "fixture cursor wraps up");
    const auto request = local_tournament_panel_navigate(
        panel, LocalTournamentPanelNav::Confirm, 3);
    check(request.kind == LocalTournamentPanelRequestKind::ArmFixture &&
        request.fixture_index == 2, "confirm requests the selected fixture");

    const auto row = local_tournament_fixture_row(state, 0, catalog(), false);
    check(row.size() <= 24, "fixture row fits 24 cells");
    check(row.rfind("R1 ", 0) == 0, "fixture row starts with round");
    const auto detail = local_tournament_fixture_detail(state, 0, catalog());
    check(detail == "DRAGSTER  UNPLAYED", "unplayed detail names course");

    auto played = state;
    played.results[0] = LocalTournamentRecordedResult{
        "sum", ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win, true};
    const auto& f = played.fixtures[0];
    // Seats swapped: the race's P2 was the scheduled first entrant.
    const auto winner = local_tournament_entrant_label(
        catalog(), played.entrants[f.player1], 8);
    check(local_tournament_fixture_detail(played, 0, catalog()) ==
        "DRAGSTER  " + winner + " WON", "swapped-seat winner orientation");
    check(local_tournament_fixture_row(played, 0, catalog(), false).back() ==
        '*', "played marker");
    check(local_tournament_fixture_row(played, 1, catalog(), true).back() ==
        '>', "armed marker");
    check(!local_tournament_fixture_playable_by(
        played, 0, played.entrants[f.player1], played.entrants[f.player2]),
        "played fixture is not playable");

    const auto standings = local_tournament_standings(played);
    for (const auto& standing : standings) {
        check(local_tournament_standing_row(standing, catalog()).size() <= 24,
            "standing row fits 24 cells");
    }
    check(standings.front().points == 3, "winner leads with 3 points");
    check(local_tournament_history_row(played, catalog()) ==
        winner + " WON  3 RACERS", "unique leader is champion");
    check(local_tournament_history_row(state, catalog()) == "TIE  3 RACERS",
        "no results is a shared lead");
    check(local_tournament_history_row(played, catalog()).size() <= 24,
        "history row fits 24 cells");
    check(local_tournament_result_notice(played, catalog()) ==
        "LEADS: " + winner + " 3 PTS 1/3", "in-progress leader notice");
    check(local_tournament_result_notice(state, catalog()) ==
        "LEAD SHARED 0 PTS 0/3", "nothing played is a shared lead");
    auto finished = played;
    finished.results[1] = LocalTournamentRecordedResult{
        "b", ur::title::OrdinaryTwoPlayerRaceOutcome::Draw, false};
    finished.results[2] = LocalTournamentRecordedResult{
        "c", ur::title::OrdinaryTwoPlayerRaceOutcome::Draw, false};
    const auto final_notice = local_tournament_result_notice(finished, catalog());
    check(final_notice.rfind("CHAMPION: ", 0) == 0 ||
        final_notice.rfind("EVENT TIED ON ", 0) == 0, "complete event notice");
    check(final_notice.size() <= 29, "notice fits the strip");
}

} // namespace

int main() {
    test_course_presets();
    test_setup_flow();
    test_entrant_cap();
    test_overview_and_fixtures();
    if (g_failures) {
        std::fprintf(stderr, "%d failure(s)\n", g_failures);
        return EXIT_FAILURE;
    }
    std::puts("local tournament panel: ok");
    return EXIT_SUCCESS;
}

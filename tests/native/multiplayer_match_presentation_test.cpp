#include "multiplayer_match_presentation.hpp"

#include <cassert>

using namespace ur::product;
using namespace ur::title;

int main() {
    StoredMultiplayerMatch stored;
    stored.run_path = "run-0000000000000000-0001.urrun";
    stored.run.provenance.mode = "race-2p";
    stored.match.run_artifact_checksum = "0123456789abcdef";
    stored.match.context.course_id = "course:01";
    stored.match.context.match.player1 = {
        "alpha", HostRacerIdentity{"MIKE", 0}};
    stored.match.context.match.player2 = {
        "beta", HostRacerIdentity{"ANDREW", 1}};
    stored.match.context.match.result.player1_rider = 0;
    stored.match.context.match.result.player2_rider = 1;
    stored.match.context.match.result.player1_hundredths = 2876;
    stored.match.context.match.result.player2_hundredths =
        kOrdinaryTwoPlayerNoTimeHundredths;
    stored.match.context.match.result.outcome =
        OrdinaryTwoPlayerRaceOutcome::Player1Win;

    assert(format_multiplayer_result_hundredths(2876) == "0:28.76");
    assert(format_multiplayer_result_hundredths(6105) == "1:01.05");
    assert(format_multiplayer_result_hundredths(
        kOrdinaryTwoPlayerNoTimeHundredths) == "NO TIME");

    const auto row = present_multiplayer_match_row(stored);
    assert(row.date_text.size() == 10);
    assert(row.date_text != "--");
    assert(row.course_text == "course:01");
    assert(row.player1_text == "MIKE / alpha");
    assert(row.player2_text == "ANDREW / beta");
    assert(row.result_text == "PLAYER 1 WIN");

    const auto detail = present_multiplayer_match_detail(stored);
    assert(detail.player1_result_text == "0:28.76");
    assert(detail.player2_result_text == "NO TIME");
    assert(detail.outcome_text == "PLAYER 1 WIN");

    return 0;
}

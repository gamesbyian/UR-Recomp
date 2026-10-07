#include "run_record_capture_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const auto one_player = resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::OnePlayer, false, true);
    assert(one_player.enabled());
    assert(one_player.kind == RunRecordCaptureKind::OnePlayerTimedRace);
    assert(one_player.provenance_mode == "race-1p");
    assert(one_player.capture_resolved_inputs);
    assert(one_player.enable_one_player_timing);
    assert(one_player.enable_one_player_ghosts);
    assert(!one_player.require_match_record);

    const auto two_player = resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::TwoPlayer, true, true);
    assert(two_player.enabled());
    assert(two_player.kind == RunRecordCaptureKind::OrdinaryTwoPlayerRace);
    assert(two_player.provenance_mode == "race-2p");
    assert(two_player.capture_resolved_inputs);
    assert(!two_player.enable_one_player_timing);
    assert(!two_player.enable_one_player_ghosts);
    assert(two_player.require_match_record);

    assert(!resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::TwoPlayer, false, true).enabled());
    assert(!resolve_run_record_capture_plan(
        true, true, HostRacePresentationMode::OnePlayer, false, true).enabled());
    assert(!resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::OnePlayer, false, false).enabled());
    assert(!resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::TwoPlayer, true, false).enabled());
    assert(!resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::Vs, true, true).enabled());
    assert(!resolve_run_record_capture_plan(
        true, false, HostRacePresentationMode::Unknown, true, true).enabled());
    assert(!resolve_run_record_capture_plan(
        false, false, HostRacePresentationMode::OnePlayer, false, true).enabled());
    assert(!resolve_run_record_capture_plan(
        false, false, HostRacePresentationMode::TwoPlayer, true, true).enabled());

    ur::title::OrdinaryTwoPlayerRaceResult p1_win;
    p1_win.player1_hundredths = 2876;
    p1_win.player2_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    assert(ordinary_two_player_carrier_elapsed_ticks60(p1_win) == 1726);

    ur::title::OrdinaryTwoPlayerRaceResult p2_win;
    p2_win.player1_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    p2_win.player2_hundredths = 3001;
    assert(ordinary_two_player_carrier_elapsed_ticks60(p2_win) == 1801);

    ur::title::OrdinaryTwoPlayerRaceResult timeout_draw;
    timeout_draw.player1_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    timeout_draw.player2_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    assert(ordinary_two_player_carrier_elapsed_ticks60(timeout_draw) == 36000);

    return 0;
}

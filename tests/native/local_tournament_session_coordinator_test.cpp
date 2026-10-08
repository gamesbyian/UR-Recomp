#include "local_tournament_session_coordinator.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

using namespace ur::product;
using namespace ur::title;
namespace fs = std::filesystem;
using Status = LocalTournamentCoordinatorStatus;

void check(bool ok, const char* why) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", why);
        std::exit(1);
    }
}

void write_real_pair(const LocalTournamentCoordinator& session,
                     const std::vector<HostProfileCatalogEntry>& catalog,
                     std::size_t fixture_index, std::uint16_t guest_input,
                     std::string* stored_path) {
    const auto& fixture = session.results.fixtures.at(fixture_index);
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        fixture.course_id,
        "race-2p",
    };
    run.elapsed_ticks60 = 1726;
    run.frame_count = 2;
    run.inputs = {{0, 2, guest_input, 0x001}};

    OrdinaryTwoPlayerRaceResult observed;
    const auto catalog_entry = [&](std::size_t slot) {
        const auto& expected = session.results.entrants[slot];
        for (const auto& entry : catalog) {
            if (entry.profile_id == expected) return entry;
        }
        check(false, "fixture entrant must stay bound to real catalog identity");
        return HostProfileCatalogEntry{};
    };
    const auto actual_p1 = catalog_entry(fixture.player1);
    const auto actual_p2 = catalog_entry(fixture.player2);
    observed.player1_rider = actual_p1.identity.rider_index;
    observed.player2_rider = actual_p2.identity.rider_index;
    observed.player1_hundredths = 2876;
    observed.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    observed.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    const int ordinal =
        (fixture.course_id[7] - '0') * 10 + (fixture.course_id[8] - '0');
    const auto bound = bind_local_multiplayer_match_context(
        observed,
        actual_p1, actual_p2,
        UrUniracersCourseIdentity{1, ordinal});
    check(bound.bound(), "stock 2P result binds actual scheduled identities");
    const auto record = make_multiplayer_match_record(run, *bound.context);
    check(bool(record), "canonical 2P metadata made from stored run");
    std::string detail;
    check(append_multiplayer_match_pair(
        session.paths.multiplayer_runs_directory,
        run, *record, stored_path, &detail),
        "authoritative run and match pair actually published");
}

int main() {
    const auto unique =
        std::chrono::steady_clock::now().time_since_epoch().count();
    const auto root = fs::temp_directory_path() /
        ("ur-tournament-coordinator-" + std::to_string(unique));
    const auto tour = root / "local-tournaments";
    const auto records = root / "multiplayer-runs";
    check(fs::create_directories(records), "multiplayer Records root");
    const LocalTournamentCoordinatorPaths paths{
        tour.string(), records.string()};
    const std::string instance = "0123456789abcdef0123456789abcdef";
    const std::string other_instance = "abcdef0123456789abcdef0123456789";
    const std::vector<HostProfileCatalogEntry> catalog{
        {"alpha", {"MIKE", 0}},
        {"beta", {"ANDREW", 1}},
        {"gamma", {"ANNA", 2}},
    };
    auto missing = restore_local_tournament_coordinator(paths, catalog);
    check(!missing.usable() && missing.status == Status::Unavailable,
          "no synthetic active tournament on a fresh install");
    auto created = create_local_tournament_coordinator(
        paths, instance, {"alpha", "beta", "gamma"}, catalog,
        {"course:01", "course:04"});
    check(created.usable() && created.status == Status::Created,
          "catalog-authorized tournament created explicitly");
    auto state = *created.session;
    check(state.results.fixtures.size() == 3 &&
          local_tournament_next_unplayed_fixture(state) == 0 &&
          !local_tournament_coordinator_complete(state),
          "three real pairings and no fabricated completed tournament");

    auto duplicate = create_local_tournament_coordinator(
        paths, other_instance, {"alpha", "beta"}, catalog, {"course:01"});
    check(!duplicate.usable() && duplicate.status == Status::AlreadyExists,
          "existing active tournament cannot be replaced without user intent");

    const std::string token0 = "11111111111111111111111111111111";
    const std::string token1 = "22222222222222222222222222222222";
    const std::string token2 = "33333333333333333333333333333333";

    const auto& first = state.results.fixtures[0];
    const std::string p1 = state.results.entrants[first.player1];
    const std::string p2 = state.results.entrants[first.player2];
    check(arm_local_tournament_fixture(state, 0, token0, "other", p2) ==
            Status::InvalidRequest && !state.launch.pending,
          "wrong Modern profile cannot preauthorize fixture launch");
    check(arm_local_tournament_fixture(state, 0, token0, p1, p2) ==
            Status::Armed && state.launch.pending,
          "explicit selected fixture persisted BEFORE guest route");
    check(!local_tournament_capture_attempt_for(
        state, p1, p2, "course:04") &&
          !local_tournament_capture_attempt_for(
              state, "unrelated", p2, first.course_id),
          "guest course and Modern participant mismatch never tags capture");
    const auto live = local_tournament_capture_attempt_for(
        state, p2, p1, first.course_id);
    check(live && *live == token0,
          "real capture owns exact pre-race token even when seats reversed");
    auto pending_restart = restore_local_tournament_coordinator(paths, catalog);
    check(pending_restart.usable() &&
          !pending_restart.session->launch.pending &&
          !pending_restart.session->results.results[0],
          "relaunching process never invents points or resumes stale race");

    std::string stored0;
    write_real_pair(state, catalog, 0, 0x080, &stored0);
    check(commit_local_tournament_capture(state, token1, stored0) ==
            Status::InvalidRequest &&
          state.launch.pending && !state.results.results[0],
          "mismatched live capture token cannot award tournament points");
    check(commit_local_tournament_capture(state, token0, stored0) ==
            Status::Committed &&
          !state.launch.pending && state.results.results[0],
          "exact saved 2P pair credits only the attempted fixture");
    check(!fs::exists(tour / instance / "pending.urlaunch"),
          "completed fixture retires exact launch checkpoint");

    const auto fresh = restore_local_tournament_coordinator(paths, catalog);
    check(fresh.usable() && fresh.session->results.results[0] &&
          !fresh.session->results.results[1],
          "fresh load restores only exact persisted receipt-linked result");
    check(local_tournament_next_unplayed_fixture(*fresh.session) == 1,
          "continuation exposes first genuinely unfinished fixture");
    auto standings = local_tournament_standings(fresh.session->results);
    std::size_t points = 0;
    for (const auto& row : standings) points += row.points;
    check(points == 3, "validated stock win awards exactly 3 Modern points");

    state = *fresh.session;
    const auto& second = state.results.fixtures[1];
    const auto a = state.results.entrants[second.player1];
    const auto b = state.results.entrants[second.player2];
    check(arm_local_tournament_fixture(state, 1, token1, a, b) == Status::Armed,
          "next fixture opens with distinct attempt ID");
    check(cancel_local_tournament_capture(state, token0) ==
            Status::InvalidRequest && state.launch.pending,
          "stale cancellation cannot abort another fixture");
    check(cancel_local_tournament_capture(state, token1) ==
            Status::Cancelled && !state.launch.pending &&
          !state.results.results[1],
          "cancel retires checkpoint and makes no points");
    check(!fs::exists(tour / instance / "pending.urlaunch"),
          "cancel actually retires durable launch checkpoint");

    check(arm_local_tournament_fixture(state, 1, token1, a, b) == Status::Armed,
          "same incomplete fixture can be explicitly retried");
    std::string stored1;
    write_real_pair(state, catalog, 1, 0x100, &stored1);
    check(commit_local_tournament_capture(state, token1, stored0) ==
            Status::EvidenceRejected && !state.results.results[1] &&
          state.launch.pending,
          "a different already-saved race cannot inherit new fixture authority");
    check(commit_local_tournament_capture(state, token1, stored1) ==
            Status::Committed && state.results.results[1],
          "second exact saved pair committed with its own attempt");

    const auto& third = state.results.fixtures[2];
    check(arm_local_tournament_fixture(
        state, 2, token2,
        state.results.entrants[third.player1],
        state.results.entrants[third.player2]) == Status::Armed,
        "final unplayed fixture explicitly armed");
    std::string stored2;
    write_real_pair(state, catalog, 2, 0x200, &stored2);
    check(commit_local_tournament_capture(state, token2, stored2) ==
            Status::Committed, "final saved stock match committed");
    check(local_tournament_coordinator_complete(state) &&
          !local_tournament_next_unplayed_fixture(state),
          "completed tournament is based on ALL validated fixture results");

    auto completed = restore_local_tournament_coordinator(paths, catalog);
    check(completed.usable() &&
          local_tournament_coordinator_complete(*completed.session) &&
          local_tournament_standings(completed.session->results).size() == 3,
          "fresh process has complete ranked tournament after real disk loading");
    const fs::path fixture_directory = tour / instance / "fixtures";
    check(fs::exists(fixture_directory), "instance receipt directory exists");
    const fs::path hidden_directory = tour / instance / "hidden-fixtures";
    fs::rename(fixture_directory, hidden_directory);
    const auto missing_evidence = restore_local_tournament_coordinator(
        paths, catalog);
    check(!missing_evidence.usable() &&
          missing_evidence.status == Status::EvidenceRejected,
          "missing receipt directory cannot present phantom empty standings");
    fs::rename(hidden_directory, fixture_directory);
    check(restore_local_tournament_coordinator(paths, catalog).usable(),
          "restored instance-owned receipt directory is readable again");

    // An old completed tournament must not leak receipts into a newly
    // requested one even when it uses the same roster and ordinary courses.
    auto replacement = create_local_tournament_coordinator(
        paths, other_instance, {"alpha", "beta", "gamma"}, catalog,
        {"course:01", "course:04"}, true);
    check(replacement.usable() &&
          replacement.session->definition.instance_id == other_instance &&
          !replacement.session->results.results[0],
          "explicit replacement selects independent instance directory");
    auto replaced_reload = restore_local_tournament_coordinator(paths, catalog);
    check(replaced_reload.usable() &&
          replaced_reload.session->definition.instance_id == other_instance &&
          !replaced_reload.session->results.results[0],
          "old completed tournament never grants new-instance standings");

    fs::remove_all(root);
    std::puts("local_tournament_session_coordinator_test: ok");
    return 0;
}

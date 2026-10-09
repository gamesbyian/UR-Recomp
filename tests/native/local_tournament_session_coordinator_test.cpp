#include "local_tournament_session_coordinator.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
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
    // Once a tournament's instance ID owns an archived plan, an unrelated
    // creator must not overwrite that durable schedule through a stale
    // exists() preflight. The coordinator now uses this exact create-only
    // store operation for its *first* immutable archive publication.
    const auto archive_path =
        (tour / instance / "session.urtournament").string();
    const auto incumbent_archive =
        load_historical_local_tournament_session_definition(archive_path);
    check(incumbent_archive.loaded(), "new tournament has a full archive");
    const auto conflicting_plan = make_local_tournament_session_definition(
        instance, {"alpha", "beta"}, catalog, {"course:01"});
    check(bool(conflicting_plan), "construct alternative valid same-ID plan");
    check(save_local_tournament_session_definition_if_current(
              archive_path, std::nullopt, *conflicting_plan) ==
              LocalTournamentSessionFileStatus::Conflict,
          "immutable instance archive rejects another valid creator");
    const auto preserved_archive =
        load_historical_local_tournament_session_definition(archive_path);
    check(preserved_archive.loaded() &&
          encode_local_tournament_session_definition(
              *preserved_archive.session) ==
          encode_local_tournament_session_definition(
              *incumbent_archive.session),
          "conflicting archive claim preserves original bytes and schedule");
    // Old builds could have a valid active pointer without an instance
    // archive. Migration must create-only claim that absent archive, and
    // must fail closed on a foreign/malformed archive rather than replace it.
    check(fs::remove(archive_path), "simulate pre-archive old build");
    const auto migrated = restore_local_tournament_coordinator(paths, catalog);
    check(migrated.usable(), "valid historical active session migrates archive");
    const auto migrated_archive =
        load_historical_local_tournament_session_definition(archive_path);
    check(migrated_archive.loaded() &&
          encode_local_tournament_session_definition(*migrated_archive.session) ==
          encode_local_tournament_session_definition(*incumbent_archive.session),
          "migration restores exact canonical session, not new results");
    // Another restorer may have won the exact same create-only claim.
    // A later normal restore must accept that identical complete archive.
    check(restore_local_tournament_coordinator(paths, catalog).usable(),
          "subsequent restorer accepts identical archive");
    check(fs::remove(archive_path), "prepare foreign archive migration denial");
    check(save_local_tournament_session_definition(
              archive_path, *conflicting_plan) ==
              LocalTournamentSessionFileStatus::Saved,
          "store alternative valid archive for migration refusal");
    check(restore_local_tournament_coordinator(paths, catalog).status ==
              Status::EvidenceRejected,
          "foreign archived schedule does not inherit current active result");
    const auto still_foreign =
        load_historical_local_tournament_session_definition(archive_path);
    check(still_foreign.loaded() &&
          encode_local_tournament_session_definition(*still_foreign.session) ==
              encode_local_tournament_session_definition(*conflicting_plan),
          "migration refuses to clobber the foreign archive");
    check(fs::remove(archive_path), "prepare corrupt archive migration denial");
    {
        std::ofstream damaged(archive_path, std::ios::binary);
        damaged << "corrupt-future-archive\n";
        check(bool(damaged), "write unsupported archive bytes");
    }
    const auto prior_corrupt_bytes = fs::file_size(archive_path);
    check(restore_local_tournament_coordinator(paths, catalog).status ==
              Status::EvidenceRejected,
          "corrupt archive is not silently overwritten by migration");
    check(fs::file_size(archive_path) == prior_corrupt_bytes,
          "corrupt existing archive preserved for salvage");
    check(fs::remove(archive_path), "remove corrupt fixture before continuation");
    check(save_local_tournament_session_definition_if_current(
              archive_path, std::nullopt, *incumbent_archive.session) ==
              LocalTournamentSessionFileStatus::Saved,
          "restore known canonical archive before fixture gameplay");
    check(state.results.fixtures.size() == 3 &&
          local_tournament_next_unplayed_fixture(state) == 0 &&
          !local_tournament_coordinator_complete(state),
          "three real pairings and no fabricated completed tournament");

    auto duplicate = create_local_tournament_coordinator(
        paths, other_instance, {"alpha", "beta"}, catalog, {"course:01"});
    check(!duplicate.usable() && duplicate.status == Status::AlreadyExists,
          "existing active tournament cannot be replaced without user intent");
    const auto reused = create_local_tournament_coordinator(
        paths, instance, {"alpha", "beta", "gamma"}, catalog,
        {"course:01", "course:04"}, true);
    check(!reused.usable() && reused.status == Status::AlreadyExists,
          "even explicit replacement cannot reuse receipt-bearing instance ID");

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
    const auto prior_checkpoint = *state.launch.pending;
    const auto checkpoint_file = (tour / instance / "pending.urlaunch").string();
    auto newer_checkpoint = prior_checkpoint;
    newer_checkpoint.attempt_id = token1;
    check(save_local_tournament_launch_file(checkpoint_file, newer_checkpoint) ==
              LocalTournamentLaunchFileStatus::Saved,
          "second process replaced disk launch checkpoint while owner raced");
    check(commit_local_tournament_capture(state, token0, stored0) ==
              Status::EvidenceRejected &&
          state.launch.pending && !state.results.results[0],
          "stale live attempt cannot claim receipt after checkpoint superseded");
    check(restore_local_tournament_coordinator(paths, catalog).usable() &&
          !restore_local_tournament_coordinator(paths, catalog)
               .session->results.results[0],
          "fresh recovery does not falsely credit superseded attempt");
    check(save_local_tournament_launch_file(checkpoint_file, prior_checkpoint) ==
              LocalTournamentLaunchFileStatus::Saved,
          "restore originally authorized checkpoint for next native test");
    const auto after_pair_before_receipt =
        restore_local_tournament_coordinator(paths, catalog);
    check(after_pair_before_receipt.usable() &&
          !after_pair_before_receipt.session->launch.pending &&
          !after_pair_before_receipt.session->results.results[0],
          "C14: saved run and match without fixture receipt award zero points");
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
    const auto prior_fixture1_checkpoint = *state.launch.pending;
    // C15 crash cut: commit the real immutable fixture receipt without
    // calling coordinator's exact checkpoint retirement. This is the same
    // production receipt-publish operation at the boundary before cleanup.
    check(commit_saved_local_tournament_fixture(
              (tour / instance / "fixtures").string(), records.string(),
              stored1, instance, token1, state.launch, state.results) ==
              LocalTournamentResultLinkStatus::Committed &&
          state.results.results[1] &&
          fs::exists(tour / instance / "pending.urlaunch"),
          "C15: receipt is authoritative before pending retirement");
    const auto after_receipt_before_retire =
        restore_local_tournament_coordinator(paths, catalog);
    check(after_receipt_before_retire.usable() &&
          after_receipt_before_retire.session->results.results[1] &&
          !after_receipt_before_retire.session->launch.pending,
          "C15: restart credits exactly the receipt and never rearms old token");
    const auto restore_twice = restore_local_tournament_coordinator(paths, catalog);
    check(restore_twice.usable() &&
          restore_twice.session->results.results[1] &&
          !restore_twice.session->launch.pending,
          "C15: repeated restarts cannot duplicate the fixture result");
    check(retire_local_tournament_launch_file(
              checkpoint_file, prior_fixture1_checkpoint) ==
              LocalTournamentLaunchFileStatus::Saved,
          "retiring exact checkpoint after receipt preserves credit");


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
    const auto initial_history =
        load_completed_local_tournament_history(paths);
    check(initial_history.scanned && !initial_history.truncated &&
          initial_history.completed.size() == 1 &&
          initial_history.completed[0].definition.instance_id == instance &&
          local_tournament_coordinator_complete(initial_history.completed[0]),
          "completed tournament is explicitly archived before any successor");
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

    const auto after_replacement =
        load_completed_local_tournament_history(paths);
    check(after_replacement.scanned && !after_replacement.truncated &&
          after_replacement.completed.size() == 1 &&
          after_replacement.incomplete_instances == 1 &&
          after_replacement.completed[0].definition.instance_id == instance &&
          after_replacement.completed[0].results.results[0] &&
          after_replacement.completed[0].results.results[1] &&
          after_replacement.completed[0].results.results[2],
          "old completed event stays restorable after active instance changes");
    const auto deleted_profiles_history =
        load_completed_local_tournament_history(paths);
    check(deleted_profiles_history.scanned &&
          deleted_profiles_history.completed.size() == 1 &&
          deleted_profiles_history.completed[0].definition.instance_id == instance &&
          deleted_profiles_history.completed[0].results.results[0] &&
          deleted_profiles_history.completed[0].results.results[1] &&
          deleted_profiles_history.completed[0].results.results[2],
          "archived completed results remain visible after profile deletion");
    check(!restore_local_tournament_coordinator(paths, {}).usable(),
          "active tournament still requires current authorized profiles");
    // A valid stored plan moved under another random instance name cannot
    // give that instance somebody else's completed tournament result.
    const fs::path wrong_instance =
        tour / "ffffffffffffffffffffffffffffffff";
    fs::create_directories(wrong_instance / "fixtures");
    fs::copy_file(
        tour / instance / "session.urtournament",
        wrong_instance / "session.urtournament");
    const auto mislabeled = load_completed_local_tournament_history(paths);
    check(mislabeled.scanned && mislabeled.completed.size() == 1 &&
          mislabeled.unavailable_instances == 1,
          "archive directory must match its canonical embedded instance ID");
    fs::remove_all(wrong_instance);

    // A damaged immutable plan must remove that whole completed event from
    // visible history even though underlying general Multiplayer Records
    // still contain the old (otherwise valid) run/match pairs.
    {
        std::ofstream damaged(
            tour / instance / "session.urtournament",
            std::ios::binary | std::ios::trunc);
        damaged << "damaged tournament identity\n";
        check(bool(damaged), "damage test archived session");
    }
    const auto rejected_history =
        load_completed_local_tournament_history(paths);
    check(rejected_history.scanned &&
          rejected_history.completed.empty() &&
          rejected_history.unavailable_instances == 1 &&
          rejected_history.incomplete_instances == 1,
          "corrupt archive cannot receive retrospective standings credit");
    check(restore_local_tournament_coordinator(paths, catalog).usable(),
          "unrelated active tournament remains readable after archive damage");

    fs::remove_all(root);
    std::puts("local_tournament_session_coordinator_test: ok");
    return 0;
}

// QA-02: kill actual host tournament persistence at C14 and C15.
// Every invocation is an independent OS process; no global game state is
// carried across launch. Only canonical files on disk authorize standings.
#include "local_tournament_session_coordinator.hpp"
#include "local_multiplayer_match_binding.hpp"
#include "multiplayer_match_record.hpp"
#include "completed_run_store.hpp"

#include <cstdlib>
#include <cstdio>
#include <chrono>
#include <fstream>
#include <thread>
#include <filesystem>
#include <string>
#include <vector>

using namespace ur::product;
using namespace ur::title;
namespace fs = std::filesystem;
using Status = LocalTournamentCoordinatorStatus;

namespace {
const std::string kInstance(32, 'a');
const std::string kAttemptC14(32, '1');
const std::string kAttemptC15(32, '2');
const std::string kAttemptC09(32, '3');
const std::string kAttemptOld(32, '4');
const std::string kAttemptNew(32, '5');
void terminate_after_sidecar_claim() { std::_Exit(79); }

void require(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "QA02_FAULT_FAIL %s\n", message);
        std::exit(12);
    }
}

std::vector<HostProfileCatalogEntry> catalog() {
    return {{"alpha", {"MIKE", 0}}, {"beta", {"ANDREW", 1}},
            {"gamma", {"ANNA", 2}}};
}

LocalTournamentCoordinatorPaths paths(const fs::path& root) {
    return {(root / "local-tournaments").string(),
            (root / "multiplayer-runs").string()};
}

std::string publish_real_pair(const LocalTournamentCoordinator& session,
                              std::uint16_t input,
                              void (*after_sidecar_for_test)() = nullptr,
                              std::size_t fixture_index = 0) {
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
    run.inputs = {{0, 2, input, 0x001}};

    const auto roster = catalog();
    const auto find_entry = [&](std::size_t slot) -> HostProfileCatalogEntry {
        const auto& id = session.results.entrants.at(slot);
        for (const auto& entry : roster) {
            if (entry.profile_id == id) return entry;
        }
        require(false, "scheduled profile not in authoritative catalog");
        return {};
    };
    const auto p1 = find_entry(fixture.player1);
    const auto p2 = find_entry(fixture.player2);

    OrdinaryTwoPlayerRaceResult observed;
    observed.player1_rider = p1.identity.rider_index;
    observed.player2_rider = p2.identity.rider_index;
    observed.player1_hundredths = 2876;
    observed.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    observed.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    const int ordinal =
        (fixture.course_id[7] - '0') * 10 + (fixture.course_id[8] - '0');
    const auto bound = bind_local_multiplayer_match_context(
        observed, p1, p2, UrUniracersCourseIdentity{1, ordinal});
    require(bound.bound(), "real 2P match context");
    const auto match = make_multiplayer_match_record(run, *bound.context);
    require(bool(match), "canonical checksum-bound match");

    std::string saved;
    std::string detail;
    require(append_multiplayer_match_pair(
                session.paths.multiplayer_runs_directory,
                run, *match, &saved, &detail, after_sidecar_for_test),
            "durably publish actual run and match pair");
    return saved;
}

void signal(const fs::path& file) {
    std::ofstream marker(file, std::ios::binary);
    require(bool(marker), "create cross-process fixture barrier marker");
}

void await_signal(const fs::path& file) {
    for (unsigned attempt = 0; attempt < 10000; ++attempt) {
        if (fs::exists(file)) return;
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    require(false, "timed out waiting for other process's checkpoint");
}

void arm_first(LocalTournamentCoordinator& session,
               const std::string& attempt) {
    const auto& fixture = session.results.fixtures.at(0);
    require(arm_local_tournament_fixture(
                session, 0, attempt,
                session.results.entrants.at(fixture.player1),
                session.results.entrants.at(fixture.player2)) ==
            Status::Armed, "durable exact fixture launch");
}
} // namespace

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    const std::string action(argv[1]);
    const fs::path root(argv[2]);
    const auto layout = paths(root);
    if (action == "seed-overlap") {
        std::error_code ec;
        fs::create_directories(layout.multiplayer_runs_directory, ec);
        require(!ec, "overlap save root");
        fs::create_directories(root / "barrier", ec);
        require(!ec, "overlap coordination barrier");
        const auto created = create_local_tournament_coordinator(
            layout, kInstance, {"alpha", "beta", "gamma"}, catalog(),
            {"course:01", "course:04"});
        require(created.usable(), "overlap event creation");
        return 0;
    }
    if (action == "contend-old") {
        const auto restored =
            restore_local_tournament_coordinator(layout, catalog());
        require(restored.usable(), "older live window restores event");
        auto session = *restored.session;
        arm_first(session, kAttemptOld);
        const auto saved = publish_real_pair(session, 0x080);
        signal(root / "barrier" / "old-ready");
        await_signal(root / "barrier" / "new-blocked");
        // B is genuinely alive but cannot steal the OS-held fixture lease.
        // A's exact on-disk token must still be authoritative.
        const auto status = commit_local_tournament_capture(
            session, kAttemptOld, saved);
        require(status == Status::Committed &&
                session.results.results.at(0),
                "live owner must complete safely without checkpoint theft");
        signal(root / "barrier" / "old-committed");
        std::puts("QA02_LIVE_OWNER_COMMITTED");
        return 0;
    }
    if (action == "contend-new") {
        await_signal(root / "barrier" / "old-ready");
        const auto restored =
            restore_local_tournament_coordinator(layout, catalog());
        require(restored.usable() && !restored.session->launch.pending &&
                !restored.session->results.results.at(0),
                "second game process starts with unplayed event");
        auto session = *restored.session;
        const auto& fixture = session.results.fixtures.at(0);
        const auto blocked = arm_local_tournament_fixture(
            session, 0, kAttemptNew,
            session.results.entrants.at(fixture.player1),
            session.results.entrants.at(fixture.player2));
        require(blocked == Status::Busy && !session.launch.pending,
                "second live game must fail fast without stealing checkpoint");
        signal(root / "barrier" / "new-blocked");
        await_signal(root / "barrier" / "old-committed");
        // Even after A releases the lease, B's stale in-memory event must
        // detect the credited receipt before attempting a new arm.
        const auto stale = arm_local_tournament_fixture(
            session, 0, kAttemptNew,
            session.results.entrants.at(fixture.player1),
            session.results.entrants.at(fixture.player2));
        require(stale == Status::EvidenceRejected &&
                !session.launch.pending,
                "released lease does not authorize re-arming completed fixture");
        std::puts("QA02_BUSY_AND_STALE_RETRY_REJECTED");
        return 0;
    }
    if (action == "owner-crash" || action == "owner-hold") {
        std::error_code ec;
        fs::create_directories(layout.multiplayer_runs_directory, ec);
        require(!ec, "crash-owner records root");
        const auto created = create_local_tournament_coordinator(
            layout, kInstance, {"alpha", "beta", "gamma"}, catalog(),
            {"course:01", "course:04"});
        require(created.usable(), "crash-owner event created");
        auto session = *created.session;
        arm_first(session, kAttemptOld);
        const auto saved = publish_real_pair(session, 0x080);
        require(fs::exists(saved), "old run saved before process death");
        if (action == "owner-hold") {
            fs::create_directories(root / "barrier", ec);
            require(!ec, "owner hold barrier root");
            signal(root / "barrier" / "owner-live");
            // The test controller must terminate this still-running process
            // with an OS hard kill. Do not let normal C++ destructors release
            // the live fixture lease before the owner actually dies.
            std::this_thread::sleep_for(std::chrono::seconds(30));
            require(false, "owner hold should have been hard-killed");
        }
        std::_Exit(81); // OS releases live lease; pending remains durable
    }
    if (action == "retry-owner-crash") {
        const auto restored =
            restore_local_tournament_coordinator(layout, catalog());
        require(restored.usable() &&
                !restored.session->results.results.at(0) &&
                !restored.session->launch.pending,
                "dead owner leaves only uncredited, inert pending checkpoint");
        auto session = *restored.session;
        arm_first(session, kAttemptNew); // explicit new attempt, new token
        const auto saved = publish_real_pair(session, 0x100);
        require(commit_local_tournament_capture(
                session, kAttemptNew, saved) == Status::Committed,
                "OS-released lease permits new explicit valid fixture attempt");
        std::puts("QA02_CRASH_RELEASED_AND_RETRIED");
        return 0;
    }

    // Each action below is invoked by an independent executable. Together
    // they finish actual canonical persisted 2P-pair fixtures across game-store
    // lifetimes, rather than merely constructing a schedule in memory.
    if (action == "qa03-create-duel" ||
        action == "qa03-create-round-robin") {
        const bool duel = action == "qa03-create-duel";
        std::error_code ec;
        fs::create_directories(layout.multiplayer_runs_directory, ec);
        require(!ec, "QA03 records root");
        const auto created = create_local_tournament_coordinator(
            layout, kInstance,
            duel ? std::vector<std::string>{"alpha", "beta"} :
                   std::vector<std::string>{"alpha", "beta", "gamma"},
            catalog(), {"course:01", "course:04"}, false, duel ? 3 : 2);
        require(created.usable() &&
                created.session->results.fixtures.size() == (duel ? 3u : 6u),
                "QA03 exact three-leg duel or two-leg three-entrant event");
        const auto history = load_completed_local_tournament_history(layout);
        require(history.scanned && history.completed.empty() &&
                history.incomplete_instances == 1,
                "unplayed event is not forged into completed history");
        std::puts("QA03_CREATED_UNPLAYED");
        return 0;
    }
    if (action == "qa03-cancel-next") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable() && !restored.session->results.results.at(0),
                "QA03 cancellation starts without credit");
        auto session = *restored.session;
        arm_first(session, kAttemptC09);
        require(cancel_local_tournament_capture(session, kAttemptC09) ==
                    Status::Cancelled && !session.results.results.at(0),
                "explicit cancellation cannot fabricate fixture result");
        std::puts("QA03_CANCELLED_WITHOUT_CREDIT");
        return 0;
    }

    if (action == "qa03-kill-midseries") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable(), "QA03 midseries owner starts intact");
        auto session = *restored.session;
        const auto next = local_tournament_next_unplayed_fixture(session);
        require(next && *next == 1 && session.results.results.at(0),
                "QA03 durable fixture zero survives before owner death");
        const auto& fixture = session.results.fixtures.at(*next);
        const std::string abandoned_attempt(32, 'e');
        require(arm_local_tournament_fixture(
                    session, *next, abandoned_attempt,
                    session.results.entrants.at(fixture.player1),
                    session.results.entrants.at(fixture.player2)) ==
                    Status::Armed, "QA03 midseries owner takes exact lease");
        const auto saved = publish_real_pair(
            session, 0x700, nullptr, *next);
        require(fs::exists(saved) && fs::exists(saved + ".urmatch"),
                "QA03 midseries saved pair survives owner hard exit");
        // Kill *before* the fixture receipt. The already credited first
        // fixture must remain legitimate, but this pair stays Records-only.
        std::_Exit(82);
    }
    if (action == "qa03-credit-next") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable() && !restored.session->launch.pending,
                "QA03 fresh process reads active event without live attempt");
        auto session = *restored.session;
        const auto index = local_tournament_next_unplayed_fixture(session);
        require(index.has_value() && *index < 6,
                "QA03 next scheduled fixture remains uncredited");
        const auto& fixture = session.results.fixtures.at(*index);
        const std::string attempt(32, static_cast<char>('1' + *index));
        require(arm_local_tournament_fixture(
                    session, *index, attempt,
                    session.results.entrants.at(fixture.player1),
                    session.results.entrants.at(fixture.player2)) ==
                    Status::Armed, "QA03 independently armed scheduled fixture");
        const auto bound = local_tournament_capture_attempt_for(
            session, session.results.entrants.at(fixture.player1),
            session.results.entrants.at(fixture.player2),
            fixture.course_id);
        require(bound && *bound == attempt,
                "QA03 source course and exact participants tag live attempt");
        const auto saved = publish_real_pair(
            session, static_cast<std::uint16_t>(0x300 + *index),
            nullptr, *index);
        require(commit_local_tournament_capture(session, attempt, saved) ==
                    Status::Committed && session.results.results.at(*index),
                "QA03 exact saved pair earns exactly one scheduled credit");
        const auto reread = restore_local_tournament_coordinator(
            layout, catalog());
        require(reread.usable() && reread.session->results.results.at(*index),
                "QA03 newly published result survives fresh store reload");
        std::printf("QA03_CREDITED_FIXTURE %zu\n", *index);
        return 0;
    }
    if (action == "qa03-verify-duel" ||
        action == "qa03-verify-round-robin" ||
        action == "qa03-verify-round-robin-interrupted") {
        const bool duel = action == "qa03-verify-duel";
        const bool interrupted =
            action == "qa03-verify-round-robin-interrupted";
        const std::size_t expected = duel ? 3 : 6;
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable() &&
                restored.session->results.fixtures.size() == expected &&
                !restored.session->launch.pending &&
                local_tournament_coordinator_complete(*restored.session) &&
                !local_tournament_next_unplayed_fixture(*restored.session),
                "QA03 all scheduled fixtures fully credited after restart");
        const auto standings = local_tournament_standings(
            restored.session->results);
        require(standings.size() == (duel ? 2u : 3u),
                "QA03 complete persisted roster");
        unsigned points = 0;
        for (const auto& row : standings) {
            require(row.played == (duel ? 3u : 4u),
                    "QA03 every entrant played all their scheduled legs");
            points += row.points;
        }
        require(points == 3u * expected,
                "QA03 no phantom, lost or duplicated fixture points");
        const auto history = load_completed_local_tournament_history(layout);
        require(history.scanned && !history.truncated &&
                history.completed.size() == 1 &&
                history.incomplete_instances == 0 &&
                history.unavailable_instances == 0 &&
                local_tournament_coordinator_complete(history.completed[0]),
                "QA03 completed event appears in strict archived history");
        std::size_t runs = 0, matches = 0;
        for (const auto& entry : fs::directory_iterator(
                 layout.multiplayer_runs_directory)) {
            if (entry.path().extension() == ".urrun") ++runs;
            if (entry.path().extension() == ".urmatch") ++matches;
        }
        // C14 crash intentionally leaves one additional uncredited but
        // valid Records pair. It cannot become a phantom fixture receipt.
        const std::size_t expected_pairs = expected + (interrupted ? 1u : 0u);
        require(runs == expected_pairs && matches == expected_pairs,
                "QA03 exact Records pairs include retained uncredited crash run");
        const auto& fixture = restored.session->results.fixtures.at(0);
        auto stale = *restored.session;
        require(arm_local_tournament_fixture(
                    stale, 0, kAttemptNew,
                    stale.results.entrants.at(fixture.player1),
                    stale.results.entrants.at(fixture.player2)) ==
                    Status::InvalidRequest,
                "QA03 completed fixture cannot be rearmed or recredited");
        std::puts("QA03_COMPLETED_RESTORED_STANDINGS_HISTORY_RECORDS");
        return 0;
    }
    if (action == "qa03-replace-completed") {
        const auto old = restore_local_tournament_coordinator(
            layout, catalog());
        require(old.usable() && local_tournament_coordinator_complete(
                    *old.session), "QA03 predecessor must be finished");
        const auto replacement = create_local_tournament_coordinator(
            layout, std::string(32, 'b'), {"alpha", "beta"}, catalog(),
            {"course:01"}, true);
        require(replacement.usable() &&
                !local_tournament_coordinator_complete(*replacement.session),
                "QA03 explicit successor starts without inherited credits");
        const auto fresh = restore_local_tournament_coordinator(
            layout, catalog());
        require(fresh.usable() &&
                fresh.session->definition.instance_id == std::string(32, 'b') &&
                !fresh.session->results.results.at(0),
                "QA03 fresh process restores successor as active");
        const auto history = load_completed_local_tournament_history(layout);
        require(history.scanned && history.completed.size() == 1 &&
                history.incomplete_instances == 1 &&
                history.completed[0].definition.instance_id == kInstance,
                "QA03 predecessor remains in Records after event replacement");
        std::puts("QA03_REPLACED_WITH_COMPLETED_HISTORY_PRESERVED");
        return 0;
    }
    if (action == "kill-c09") {
        std::error_code ec;
        fs::create_directories(layout.multiplayer_runs_directory, ec);
        require(!ec, "create records root");
        const auto created = create_local_tournament_coordinator(
            layout, kInstance, {"alpha", "beta", "gamma"}, catalog(),
            {"course:01", "course:04"});
        require(created.usable(), "C09 created tournament");
        auto session = *created.session;
        arm_first(session, kAttemptC09);
        (void)publish_real_pair(session, 0x180, &terminate_after_sidecar_claim);
        require(false, "C09 callback must terminate after sidecar claim");
    }
    if (action == "verify-c09") {
        const auto restored =
            restore_local_tournament_coordinator(layout, catalog());
        require(restored.usable(), "C09 restore active tournament");
        require(!restored.session->launch.pending,
                "C09 pending is not a resumed race");
        require(!restored.session->results.results.at(0),
                "C09 orphan sidecar does not grant fixture credit");
        std::size_t runs = 0;
        std::size_t sidecars = 0;
        for (const auto& entry : fs::directory_iterator(
                 layout.multiplayer_runs_directory)) {
            if (entry.path().extension() == ".urrun") ++runs;
            if (entry.path().extension() == ".urmatch") ++sidecars;
        }
        require(runs == 0 && sidecars == 1,
                "C09 only orphan immutable .urmatch publicly visible");
        const auto& fixture = restored.session->results.fixtures.at(0);
        const RunPlaybackTarget target{
            "uniracers-usa",
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "native-sim-v1", fixture.course_id, "race-2p",
        };
        const auto admitted = load_compatible_run_records(
            layout.multiplayer_runs_directory, target);
        require(admitted.empty(), "C09 no ghost/PB-admissible run");
        std::puts("QA02_C09_NO_RUN_NO_CREDIT");
        return 0;
    }
    if (action == "recover-c09") {
        const auto restored =
            restore_local_tournament_coordinator(layout, catalog());
        require(restored.usable() && !restored.session->results.results.at(0),
                "C09 recovery cannot invent old result");
        auto session = *restored.session;
        arm_first(session, kAttemptC15);
        const auto saved = publish_real_pair(session, 0x200);
        require(commit_local_tournament_capture(session, kAttemptC15, saved) ==
                    Status::Committed, "C09 later honest fixture committed");
        std::puts("QA02_C09_LATER_VALID_RETRY");
        return 0;
    }
    if (action == "kill-c14") {
        std::error_code ec;
        fs::create_directories(layout.multiplayer_runs_directory, ec);
        require(!ec, "create original run records root");
        const auto created = create_local_tournament_coordinator(
            layout, kInstance, {"alpha", "beta", "gamma"}, catalog(),
            {"course:01", "course:04"});
        require(created.usable(), "create real archived active tournament");
        auto session = *created.session;
        arm_first(session, kAttemptC14);
        const auto saved = publish_real_pair(session, 0x080);
        require(fs::exists(saved), "C14 run exists before kill");
        require(fs::exists(saved + ".urmatch"), "C14 pair sidecar exists");
        require(!fs::exists(
            root / "local-tournaments" / kInstance / "fixtures" /
            "fixture-0.urfixture"), "C14 receipt still absent");
        std::_Exit(77);  // process dies after actual paired publication
    }
    if (action == "verify-c14") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable(), "C14 active event restore");
        require(!restored.session->launch.pending,
                "C14 interrupted guest launch not resurrected");
        require(!restored.session->results.results.at(0),
                "C14 saved pair alone never earns fixture credit");
        require(!fs::exists(
            root / "local-tournaments" / kInstance / "fixtures" /
            "fixture-0.urfixture"), "C14 no invented receipt");
        std::puts("QA02_C14_ZERO_CREDIT");
        return 0;
    }
    if (action == "kill-c15") {
        auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable(), "C15 restore uncredited event");
        auto session = *restored.session;
        require(!session.results.results.at(0), "no prior fixture credit");
        arm_first(session, kAttemptC15);
        const auto saved = publish_real_pair(session, 0x100);
        const auto status = commit_saved_local_tournament_fixture(
            (root / "local-tournaments" / kInstance / "fixtures").string(),
            layout.multiplayer_runs_directory, saved, kInstance,
            kAttemptC15, session.launch, session.results);
        require(status == LocalTournamentResultLinkStatus::Committed,
                "C15 authoritative immutable receipt publication");
        require(session.results.results.at(0).has_value(),
                "C15 fixture credited at receipt boundary");
        require(fs::exists(
            root / "local-tournaments" / kInstance / "pending.urlaunch"),
            "C15 old checkpoint remains before retirement");
        std::_Exit(78);  // no checkpoint retirement
    }
    if (action == "verify-c15") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable(), "C15 active event restore");
        require(!restored.session->launch.pending,
                "C15 stale checkpoint not promoted to live capture");
        const auto& results = restored.session->results.results;
        require(results.size() == 3 && bool(results.at(0)) &&
                !results.at(1) && !results.at(2),
                "C15 exactly one credited fixture on fresh process");
        unsigned points = 0;
        for (const auto& row :
             local_tournament_standings(restored.session->results)) {
            points += row.points;
        }
        require(points == 3, "C15 single stock victory awards 3 points");
        std::puts("QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD");
        return 0;
    }
    if (action == "verify-corrupt") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(!restored.usable() &&
                restored.status == Status::EvidenceRejected,
                "damaged immutable receipt never grants guessed winner");
        std::puts("QA02_CORRUPT_RECEIPT_REJECTED");
        return 0;
    }
    return 2;
}

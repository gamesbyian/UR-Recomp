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
                              void (*after_sidecar_for_test)() = nullptr) {
    const auto& fixture = session.results.fixtures.at(0);
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
        await_signal(root / "barrier" / "new-armed");
        // A new game instance has superseded the canonical pending attempt.
        // The old window must fail to publish a fixture credit, even though
        // its own .urrun/.urmatch are complete and locally playable.
        const auto status = commit_local_tournament_capture(
            session, kAttemptOld, saved);
        require(status == Status::EvidenceRejected &&
                !session.results.results.at(0),
                "superseded old process must never credit its result");
        signal(root / "barrier" / "old-rejected");
        std::puts("QA02_OLD_ATTEMPT_REJECTED");
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
        arm_first(session, kAttemptNew);
        const auto saved = publish_real_pair(session, 0x100);
        signal(root / "barrier" / "new-armed");
        await_signal(root / "barrier" / "old-rejected");
        require(commit_local_tournament_capture(
                session, kAttemptNew, saved) == Status::Committed,
                "current durable attempt earns exactly one result");
        std::puts("QA02_NEW_ATTEMPT_COMMITTED");
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

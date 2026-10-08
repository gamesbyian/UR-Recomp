#include "local_tournament_result_link_store.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

using namespace ur::product;
using namespace ur::title;
namespace fs = std::filesystem;
using Status = LocalTournamentResultLinkStatus;

void check(bool ok, const char* why) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", why);
        std::exit(1);
    }
}

CompletedRunRecord make_run(std::string course, std::uint16_t inputs) {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        std::move(course),
        "race-2p",
    };
    run.elapsed_ticks60 = 1726;
    run.frame_count = 2;
    run.inputs = {{0, 2, inputs, 0x001}};
    return run;
}

MultiplayerMatchRecord make_match(
    const CompletedRunRecord& run,
    const LocalTournamentState& tournament,
    std::size_t fixture_index) {
    const auto& fixture = tournament.fixtures[fixture_index];
    OrdinaryTwoPlayerRaceResult observed;
    observed.player1_rider = 0;
    observed.player2_rider = 1;
    observed.player1_hundredths = 2876;
    observed.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    observed.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    const auto context = bind_local_multiplayer_match_context(
        observed,
        {tournament.entrants[fixture.player1], {"MIKE", 0}},
        {tournament.entrants[fixture.player2], {"ANDREW", 1}},
        UrUniracersCourseIdentity{
            1, static_cast<int>((fixture.course_id[7] - '0') * 10 +
                                (fixture.course_id[8] - '0'))});
    check(context.bound(), "real bound match from fixture identities");
    const auto match = make_multiplayer_match_record(run, *context.context);
    check(bool(match), "valid 2P pair metadata");
    return *match;
}

int main() {
    const auto initial = make_local_round_robin(
        {"alpha", "beta", "gamma"}, {"course:01", "course:04"});
    check(bool(initial), "canonical 3-entrant round robin");
    const std::string instance = "0123456789abcdef0123456789abcdef";
    const std::string first_attempt = "11111111111111111111111111111111";
    const std::string second_attempt = "22222222222222222222222222222222";
    const auto unique =
        std::chrono::steady_clock::now().time_since_epoch().count();
    const auto root = fs::temp_directory_path() /
        ("ur-local-fixture-link-test-" + std::to_string(unique));
    const auto run_root = root / "multiplayer-runs";
    const auto link_root = root / "fixtures";
    fs::create_directories(run_root);
    fs::create_directories(link_root);
    const auto run0 = make_run(initial->fixtures[0].course_id, 0x080);
    const auto match0 = make_match(run0, *initial, 0);
    std::string path0;
    std::string detail;
    check(append_multiplayer_match_pair(
        run_root.string(), run0, match0, &path0, &detail),
        "authoritative pair published to actual disk");

    // A validated general-Records pair alone cannot confer tournament points.
    auto no_links = restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial);
    check(no_links.restored() && !no_links.state->results[0],
          "fresh process does not infer tournament membership from race history");

    auto active = *initial;
    LocalTournamentLaunchState launch;
    check(local_tournament_arm_fixture(
        launch, active, instance, first_attempt, 0) ==
        LocalTournamentLaunchStatus::Armed, "explicit fixture launch token");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(), path0, instance,
        second_attempt, launch, active) == Status::MatchRejected &&
        launch.pending && !active.results[0],
        "other live capture attempt cannot steal a saved result");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(),
        (root / "outside.urrun").string(), instance,
        first_attempt, launch, active) == Status::InvalidInput &&
        launch.pending && !active.results[0],
        "outside run path rejected before evidence admission");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(), path0, instance,
        first_attempt, launch, active) == Status::Committed &&
        !launch.pending && active.results[0],
        "exact live attempt + real admitted pair commits one fixture link");
    const auto link0 = link_root / "fixture-0.urfixture";
    check(fs::exists(link0) && !fs::exists(link0.string() + ".tmp"),
          "durable fixture link committed and no temporary residue");

    // A second, separately valid process attempt for the same scheduled
    // fixture must NEVER overwrite the already published receipt. A prior
    // exists() check is not a concurrency transaction, so publication itself
    // must atomically reject an occupied final name.
    const auto alternate_run = make_run(initial->fixtures[0].course_id, 0x040);
    const auto alternate_match = make_match(alternate_run, *initial, 0);
    std::string alternate_path;
    check(append_multiplayer_match_pair(
        run_root.string(), alternate_run, alternate_match,
        &alternate_path, &detail), "competing valid pair published");
    std::ifstream before_link(link0, std::ios::binary);
    const std::string incumbent_bytes{
        std::istreambuf_iterator<char>(before_link),
        std::istreambuf_iterator<char>()};
    check(!incumbent_bytes.empty(), "incumbent receipt byte witness");
    auto competing = *initial;
    LocalTournamentLaunchState competitor_launch;
    const std::string competitor_attempt =
        "33333333333333333333333333333333";
    check(local_tournament_arm_fixture(
        competitor_launch, competing, instance, competitor_attempt, 0) ==
            LocalTournamentLaunchStatus::Armed,
        "independent second process could arm the same earlier fixture");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(), alternate_path, instance,
        competitor_attempt, competitor_launch, competing) ==
            Status::Conflict && competitor_launch.pending &&
            !competing.results[0],
        "second valid fixture result cannot replace first, or commit memory");
    std::ifstream after_link(link0, std::ios::binary);
    const std::string preserved_bytes{
        std::istreambuf_iterator<char>(after_link),
        std::istreambuf_iterator<char>()};
    check(preserved_bytes == incumbent_bytes,
          "immutable published receipt remains byte exact after conflict");

    // A process killed before the atomic final-name claim can leave staging
    // debris. It must never become evidence or poison a valid fixture restore.
    const auto abandoned = link_root / ".pending-urfixture-abandoned";
    fs::create_directory(abandoned);
    {
        std::ofstream pending(abandoned / "fixture.tmp", std::ios::binary);
        pending << "unfinished alternate receipt";
    }

    const auto restored = restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial);
    check(restored.restored() && restored.state->results[0] &&
          !restored.state->results[1] && !restored.state->results[2],
          "fresh filesystem restoration credits exact fixture only");
    const auto rankings = local_tournament_standings(*restored.state);
    std::size_t points = 0;
    for (const auto& row : rankings) points += row.points;
    check(points == 3, "standings award actual validated result once");

    const auto run1 = make_run(initial->fixtures[1].course_id, 0x100);
    const auto match1 = make_match(run1, *initial, 1);
    std::string path1;
    check(append_multiplayer_match_pair(
        run_root.string(), run1, match1, &path1, &detail),
        "second ordinary 2P pair published");
    check(local_tournament_arm_fixture(
        launch, active, instance, second_attempt, 1) ==
        LocalTournamentLaunchStatus::Armed, "next incomplete fixture armed");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(), path0, instance,
        second_attempt, launch, active) == Status::MatchRejected &&
        launch.pending && !active.results[1],
        "old fixture result cannot be credited to a new fixture");
    check(commit_saved_local_tournament_fixture(
        link_root.string(), run_root.string(), path1, instance,
        second_attempt, launch, active) == Status::Committed &&
        active.results[1], "second actual 2P pair captured");
    const auto two = restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial);
    check(two.restored() && two.state->results[0] && two.state->results[1] &&
          !two.state->results[2], "multiple receipts restored all or nothing");
    check(restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(),
        "abcdef0123456789abcdef0123456789", *initial).status ==
            Status::MatchRejected,
        "wrong active tournament ID cannot inherit saved fixture links");

    // Independently validated match history remains valid, but a damaged
    // receipt cannot silently be skipped in otherwise valid standings.
    const auto link1 = link_root / "fixture-1.urfixture";
    {
        std::ofstream bad(link1, std::ios::binary | std::ios::trunc);
        bad << "corrupt receipt\n";
    }
    const auto failed = restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial);
    check(!failed.restored() && !failed.state &&
          failed.status == Status::MatchRejected,
          "corrupt later fixture invalidates entire standings restore");
    fs::remove(link1);
    const auto first_only = restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial);
    check(first_only.restored() && first_only.state->results[0] &&
          !first_only.state->results[1],
          "absent receipt cannot gain points from matching general Records");
    fs::remove(path0 + ".urmatch");
    check(restore_saved_local_tournament_fixtures(
        link_root.string(), run_root.string(), instance, *initial).status ==
            Status::MatchRejected,
        "missing bound match sidecar invalidates receipt");

    fs::remove_all(root);
    std::puts("local_tournament_result_link_store_test: ok");
    return 0;
}

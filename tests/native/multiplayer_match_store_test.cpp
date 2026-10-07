#include "multiplayer_match_store.hpp"

#include <cassert>
#include <filesystem>
#include <string>

using namespace ur::product;
using namespace ur::title;

namespace {

HostProfileCatalogEntry profile(
    const char* id,
    const char* name,
    std::uint8_t rider) {
    return {id, HostRacerIdentity{name, rider}};
}

CompletedRunRecord two_player_run() {
    CompletedRunRecord run;
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-2p",
    };
    run.elapsed_ticks60 = 1800;
    run.frame_count = 3;
    run.inputs = {
        {0, 1, 0x080, 0x001},
        {1, 2, 0x040, 0x002},
    };
    return run;
}

BoundOrdinaryTwoPlayerMatchContext match_context() {
    OrdinaryTwoPlayerRaceResult result;
    result.player1_rider = 0;
    result.player2_rider = 1;
    result.player1_hundredths = 2876;
    result.player2_hundredths = 3012;
    result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;

    const auto bound = bind_local_multiplayer_match_context(
        result,
        profile("ian", "MIKE", 0),
        profile("friend", "ANDREW", 1),
        UrUniracersCourseIdentity{1, 1});
    assert(bound.bound());
    return *bound.context;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path directory = argv[1];
    const auto run = two_player_run();
    const auto context = match_context();

    StoredMultiplayerMatchArtifacts stored;
    std::string detail;
    assert(append_multiplayer_match_artifacts(
        directory.string(), run, context, &stored, &detail));
    assert(!stored.run_path.empty());
    assert(stored.match_path == stored.run_path + ".urmatch");
    assert(std::filesystem::is_regular_file(stored.run_path));
    assert(std::filesystem::is_regular_file(stored.match_path));

    const auto fresh_run =
        load_completed_run_record_file(stored.run_path);
    assert(fresh_run.loaded());
    assert(fresh_run.record->provenance.mode == "race-2p");
    const auto fresh_match =
        load_multiplayer_match_record_for_run(
            stored.run_path, *fresh_run.record);
    assert(fresh_match);
    assert(fresh_match.record->context.match.player1.profile_id == "ian");
    assert(fresh_match.record->context.match.player2.profile_id == "friend");

    const auto valid_runs =
        load_valid_run_records(directory.string());
    assert(valid_runs.size() == 1);
    assert(valid_runs[0].path == stored.run_path);

    // Semantic rejection happens before another run artifact is appended.
    auto one_player = run;
    one_player.provenance.mode = "race-1p";
    assert(!append_multiplayer_match_artifacts(
        directory.string(), one_player, context, nullptr, &detail));
    assert(load_valid_run_records(directory.string()).size() == 1);

    auto wrong_course = context;
    wrong_course.course_id = "course:02";
    assert(!append_multiplayer_match_artifacts(
        directory.string(), run, wrong_course, nullptr, &detail));
    assert(load_valid_run_records(directory.string()).size() == 1);

    return 0;
}

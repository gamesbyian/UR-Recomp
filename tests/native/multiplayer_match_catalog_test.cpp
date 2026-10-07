#include "multiplayer_match_catalog.hpp"

#include "completed_run_store.hpp"
#include "local_multiplayer_match_binding.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
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

CompletedRunRecord run(std::string mode, std::string course = "course:01") {
    CompletedRunRecord value;
    value.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        std::move(course),
        std::move(mode),
    };
    value.elapsed_ticks60 = 1726;
    value.frame_count = 2;
    value.inputs = {{0, 2, 0x080, 0x001}};
    return value;
}

MultiplayerMatchRecord match_for(const CompletedRunRecord& value) {
    OrdinaryTwoPlayerRaceResult result;
    result.player1_rider = 0;
    result.player2_rider = 1;
    result.player1_hundredths = 2876;
    result.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;

    const auto context = bind_local_multiplayer_match_context(
        result,
        profile("alpha", "MIKE", 0),
        profile("beta", "ANDREW", 1),
        UrUniracersCourseIdentity{1, 1});
    assert(context.bound());
    const auto match = make_multiplayer_match_record(value, *context.context);
    assert(match);
    return *match;
}

}  // namespace

int main() {
    const auto root =
        std::filesystem::temp_directory_path() / "ur-multiplayer-catalog-test";
    std::filesystem::remove_all(root);
    std::filesystem::create_directories(root);

    const auto valid = run("race-2p");
    const auto valid_path = root / "001-valid.urrun";
    assert(save_completed_run_record_file(valid_path.string(), valid));
    const auto match = match_for(valid);
    assert(save_multiplayer_match_record_for_run(
        valid_path.string(), valid, match));

    const auto missing_sidecar = run("race-2p");
    const auto missing_path = root / "002-missing.urrun";
    assert(save_completed_run_record_file(
        missing_path.string(), missing_sidecar));

    const auto wrong_mode = run("race-1p");
    const auto wrong_mode_path = root / "003-wrong-mode.urrun";
    assert(save_completed_run_record_file(
        wrong_mode_path.string(), wrong_mode));

    {
        std::ofstream corrupt(
            root / "004-corrupt.urrun",
            std::ios::binary | std::ios::trunc);
        corrupt << "not a completed run\n";
    }

    const auto inspected =
        inspect_multiplayer_match_artifacts(root.string());
    assert(inspected.size() == 4);
    assert(inspected[0].loaded());
    assert(inspected[0].stored->match.context.match.player1.profile_id ==
           "alpha");
    assert(inspected[1].status ==
           MultiplayerMatchArtifactStatus::MatchMissingOrUnreadable);
    assert(inspected[2].status ==
           MultiplayerMatchArtifactStatus::WrongRunMode);
    assert(inspected[3].status ==
           MultiplayerMatchArtifactStatus::RunUnreadable);

    const auto health =
        summarize_multiplayer_match_artifact_health(inspected);
    assert(health.total_run_artifacts == 4);
    assert(health.loaded_pairs == 1);
    assert(health.unavailable_pairs() == 3);
    assert(health.unavailable_match_metadata == 1);
    assert(health.wrong_mode_runs == 1);
    assert(health.unreadable_runs == 1);

    const auto loaded = load_valid_multiplayer_matches(root.string());
    assert(loaded.size() == 1);
    assert(loaded[0].run_path == valid_path.string());
    assert(loaded[0].run.provenance.mode == "race-2p");

    const auto alpha =
        filter_multiplayer_matches_for_profile(loaded, "alpha");
    assert(alpha.size() == 1);
    assert(filter_multiplayer_matches_for_profile(loaded, "missing").empty());

    const auto course =
        filter_multiplayer_matches_for_course(loaded, "course:01");
    assert(course.size() == 1);
    assert(filter_multiplayer_matches_for_course(
        loaded, "course:02").empty());

    std::filesystem::remove_all(root);
    return 0;
}

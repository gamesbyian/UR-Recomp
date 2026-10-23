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

    // Live and dangling run aliases remain visible as UNAVAILABLE instead
    // of being read as another archive's valid run, or silently omitted.
    std::filesystem::create_symlink(
        valid_path, root / "005-redirected.urrun");
    std::filesystem::create_symlink(
        root / "missing-run.urrun", root / "006-dangling.urrun");
    // A direct run with a symlinked *matching* sidecar must also remain
    // unavailable: matching bytes outside this directory grant no record.
    const auto sidecar_alias = root / "007-sidecar-alias.urrun";
    assert(save_completed_run_record_file(sidecar_alias.string(), valid));
    const auto real_sidecar =
        multiplayer_match_record_path_for_run(valid_path.string());
    const auto aliased_sidecar =
        multiplayer_match_record_path_for_run(sidecar_alias.string());
    std::filesystem::create_symlink(real_sidecar, aliased_sidecar);
    const auto rejected = inspect_multiplayer_match_artifacts(root.string());
    assert(rejected.size() == 7);
    assert(rejected[4].status == MultiplayerMatchArtifactStatus::RunUnreadable);
    assert(rejected[5].status == MultiplayerMatchArtifactStatus::RunUnreadable);
    assert(rejected[6].status ==
           MultiplayerMatchArtifactStatus::MatchMissingOrUnreadable);
    const auto rejected_health =
        summarize_multiplayer_match_artifact_health(rejected);
    assert(rejected_health.total_run_artifacts == 7);
    assert(rejected_health.loaded_pairs == 1);
    assert(rejected_health.unreadable_runs == 3);
    assert(rejected_health.unavailable_match_metadata == 2);
    assert(rejected_health.wrong_mode_runs == 1);
    assert(load_valid_multiplayer_matches(root.string()).size() == 1);

    {
        const auto unicode_root = std::filesystem::temp_directory_path() /
            std::filesystem::u8path(u8"ur-multiplayer-catalog-\u8DEF\u5F84-\U0001F308");
        std::filesystem::remove_all(unicode_root);
        std::string stored_path;
        assert(append_multiplayer_match_pair(
            unicode_root.u8string(), valid, match, &stored_path));
        const auto found = inspect_multiplayer_match_artifacts(
            unicode_root.u8string());
        assert(found.size() == 1 && found[0].loaded());
        assert(found[0].run_path == stored_path);
        assert(found[0].stored->run_path == stored_path);
        const auto loaded_unicode = load_valid_multiplayer_matches(
            unicode_root.u8string());
        assert(loaded_unicode.size() == 1);
        assert(loaded_unicode[0].run_path == stored_path);
        std::filesystem::remove_all(unicode_root);
    }

    std::filesystem::remove_all(root);
    return 0;
}

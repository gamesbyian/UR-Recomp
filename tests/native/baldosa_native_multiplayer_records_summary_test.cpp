#include "baldosa_native_multiplayer_records_summary.hpp"
#include "completed_run_store.hpp"
#include "local_multiplayer_match_binding.hpp"
#include "multiplayer_match_record.hpp"

#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <unistd.h>

using namespace ur::product;
using namespace ur::title;

int main() {
    namespace fs = std::filesystem;
    const auto root = fs::temp_directory_path() /
        ("ur-baldosa-native-two-player-records-" + std::to_string(getpid()));
    const auto directory = root / "multiplayer-runs";
    fs::create_directories(root);
    const auto absent =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "alpha");
    assert(absent.directory_available && absent.validated_pairs == 0);
    assert(absent.selected_profile_matches == 0);
    assert(!inspect_baldosa_native_two_player_records_archive(
        directory.string(), "").directory_available);

    fs::create_directories(directory);
    CompletedRunRecord run{};
    run.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-unit-not-played",
        "course:01", "race-2p",
    };
    run.elapsed_ticks60 = 1400;
    run.frame_count = 2;
    run.inputs = {{0, 2, 0x80, 0x10}};
    const auto first = directory / "001-match.urrun";
    assert(save_completed_run_record_file(first.string(), run));
    OrdinaryTwoPlayerRaceResult source{};
    source.player1_rider = 0;
    source.player2_rider = 1;
    source.player1_hundredths = 2876;
    source.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    source.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    const auto context = bind_local_multiplayer_match_context(
        source,
        HostProfileCatalogEntry{"alpha", HostRacerIdentity{"MIKE", 0}},
        HostProfileCatalogEntry{"beta", HostRacerIdentity{"ANDREW", 1}},
        UrUniracersCourseIdentity{1, 1});
    assert(context.bound());
    const auto pair = make_multiplayer_match_record(run, *context.context);
    assert(pair);
    assert(save_multiplayer_match_record_for_run(first.string(), run, *pair));

    // Inert incomplete pair and unrelated 1P artifact cannot mint wins.
    const auto second = directory / "002-no-sidecar.urrun";
    assert(save_completed_run_record_file(second.string(), run));
    auto wrong = run;
    wrong.provenance.mode = "race-1p";
    assert(save_completed_run_record_file(
        (directory / "003-not-2p.urrun").string(), wrong));
    // An otherwise valid sidecar with a damaged integrity checksum must
    // remain unavailable, not silently count as another result.
    const auto corrupted = directory / "004-damaged-match.urrun";
    assert(save_completed_run_record_file(corrupted.string(), run));
    assert(save_multiplayer_match_record_for_run(
        corrupted.string(), run, *pair));
    {
        const auto sidecar = multiplayer_match_record_path_for_run(
            corrupted.string());
        std::ofstream overwrite(sidecar, std::ios::binary | std::ios::trunc);
        assert(overwrite);
        overwrite << "UR-MULTIPLAYER-MATCH/1\\ncorrupt\\n";
    }

    const auto view =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "ALPHA");
    assert(view.directory_available);
    assert(view.validated_pairs == 1);
    assert(view.unavailable_pairs == 3);
    assert(view.selected_profile_matches == 1);
    assert(view.wins == 1 && view.losses == 0 && view.draws == 0);

    const auto uninvolved =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "unrelated");
    assert(uninvolved.validated_pairs == 1);
    assert(uninvolved.selected_profile_matches == 0);
    assert(uninvolved.wins == 0 && uninvolved.losses == 0);

    // Never enumerate a substituted foreign archive directory, including
    // broken symlinks that exists() would wrongly classify as missing.
    const auto redirected = root / "redirected";
    fs::create_directory_symlink(directory, redirected);
    assert(!inspect_baldosa_native_two_player_records_archive(
        redirected.string(), "alpha").directory_available);
    const auto broken = root / "broken";
    fs::create_directory_symlink(root / "missing", broken);
    assert(!inspect_baldosa_native_two_player_records_archive(
        broken.string(), "alpha").directory_available);
    fs::remove_all(root);
    std::puts("PASS: Baldosa native Records reads only paired ordinary-2P matches for the selected profile");
}

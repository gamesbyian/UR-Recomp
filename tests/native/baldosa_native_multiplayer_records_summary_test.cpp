#include "baldosa_native_multiplayer_records_summary.hpp"
#include "completed_run_store.hpp"
#include "local_multiplayer_match_binding.hpp"
#include "multiplayer_match_record.hpp"
#include "multiplayer_match_catalog.hpp"

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
    assert(view.latest_match_line == "LAST 01 WIN 00:28.76");
    const auto beta =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "BeTa");
    assert(beta.selected_profile_matches == 1);
    assert(beta.latest_match_line == "LAST 01 LOSS DNF");

    const auto uninvolved =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "unrelated");
    assert(uninvolved.validated_pairs == 1);
    assert(uninvolved.selected_profile_matches == 0);
    assert(uninvolved.wins == 0 && uninvolved.losses == 0);
    assert(uninvolved.latest_match_line.empty());

    // The newest run may belong to OTHER profiles; it must not replace the
    // selected profile's last valid result. An unrelated corrupt sidecar also
    // cannot change the displayed source outcome or course.
    const auto later = directory / "005-other.urrun";
    assert(save_completed_run_record_file(later.string(), run));
    OrdinaryTwoPlayerRaceResult outside = source;
    outside.player1_rider = 2;
    outside.player2_rider = 3;
    const auto outside_context = bind_local_multiplayer_match_context(
        outside,
        HostProfileCatalogEntry{"gamma", HostRacerIdentity{"MARTIN", 2}},
        HostProfileCatalogEntry{"delta", HostRacerIdentity{"MELISSA", 3}},
        UrUniracersCourseIdentity{1, 1});
    assert(outside_context.bound());
    const auto outside_pair =
        make_multiplayer_match_record(run, *outside_context.context);
    assert(outside_pair);
    assert(save_multiplayer_match_record_for_run(
        later.string(), run, *outside_pair));
    const auto still_selected =
        inspect_baldosa_native_two_player_records_archive(
            directory.string(), "alpha");
    assert(still_selected.latest_match_line == "LAST 01 WIN 00:28.76");
    assert(still_selected.selected_profile_matches == 1);

    {
        // The player-visible two-player summary must admit the same UTF-8
        // archive root that the pair writer and catalog successfully use.
        const auto unicode_root = fs::temp_directory_path() /
            fs::u8path(u8"ur-two-player-summary-\u8DEF\u5F84-\U0001F308");
        fs::remove_all(unicode_root);
        std::string stored_path;
        assert(append_multiplayer_match_pair(
            unicode_root.u8string(), run, *pair, &stored_path));
        const auto unicode_view =
            inspect_baldosa_native_two_player_records_archive(
                unicode_root.u8string(), "alpha");
        assert(unicode_view.directory_available);
        assert(unicode_view.validated_pairs == 1);
        assert(unicode_view.unavailable_pairs == 0);
        assert(unicode_view.selected_profile_matches == 1);
        assert(unicode_view.wins == 1);
        assert(unicode_view.latest_match_line == "LAST 01 WIN 00:28.76");
        fs::remove_all(unicode_root);
    }

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
#if !defined(_WIN32)
    // Existing 2P archive directories can refuse enumeration after a
    // successful symlink_status check. Never show zero matches as truth.
    const auto unreadable = root / "unreadable-multiplayer-runs";
    fs::create_directory(unreadable);
    fs::permissions(unreadable, fs::perms::none);
    bool scan_succeeded = true;
    const auto refused_scan = inspect_multiplayer_match_artifacts(
        unreadable.string(), &scan_succeeded);
    if (geteuid() != 0) assert(!scan_succeeded);
    if (!scan_succeeded) {
        assert(refused_scan.empty());
        const auto refused = inspect_baldosa_native_two_player_records_archive(
            unreadable.string(), "alpha");
        assert(!refused.directory_available);
        assert(refused.validated_pairs == 0);
        assert(refused.selected_profile_matches == 0);
        assert(refused.latest_match_line.empty());
    }
    fs::permissions(unreadable, fs::perms::owner_all);
#endif
    fs::remove_all(root);
    std::puts("PASS: Baldosa native Records reads only paired ordinary-2P matches for the selected profile");
}

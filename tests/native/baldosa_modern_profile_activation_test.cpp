/* Native profile activation must read the existing Modern product codec and
 * fail closed before any guest SRAM is touched. Uses fake RTL save-root APIs,
 * but real product state / profile file codecs, not fake profile records. */
#include "host_product_state.hpp"
#include "host_profile_store.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_catalog.hpp"
#include "baldosa_native_profile_sram_checkpoint.hpp"
#include "baldosa_native_run_record_admission.hpp"
#include "completed_run_store.hpp"
#include "multiplayer_match_catalog.hpp"
#include "multiplayer_match_record.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <sys/wait.h>
#include <unistd.h>

extern "C" int ur_baldosa_modern_try_activate_profile(void);
extern "C" int ur_baldosa_modern_profile_before_native_save(void);
extern "C" int ur_baldosa_modern_publish_settled_one_player_run(
    const ur::product::BaldosaSettledResult*);
extern "C" int ur_baldosa_modern_publish_settled_two_player_match(
    const ur::product::BaldosaSettledResult*,
    const ur::product::HostProfileCatalogEntry*,
    const ur::product::HostProfileCatalogEntry*);
extern "C" int ur_baldosa_modern_profile_can_join_opponent(
    const ur::product::HostProfileCatalogEntry*);
extern "C" int ur_baldosa_modern_profile_can_begin_race(void);
extern "C" int ur_baldosa_modern_profile_finish_native_save(int);

/* Real pinned framework provides these. Keep the unit executable's tiny RTL
 * shim link-complete after adding the read-only first-frame SRAM witness. */
extern "C" {
unsigned char* g_sram = nullptr;
int g_sram_size = 0;
}

namespace {
std::string root = "saves";
std::string selected_racer;
}

extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name) {
    selected_racer = name ? name : "";
}

// The real native root is linked only into Baldosa's production runtime.
// This standalone codec/profile admission fixture deliberately has NO
// Practice/renderer/SDL root. Its inert stubs represent an ordinary guest
// and exercise the actual activation/save/record authority unchanged.
extern "C" int ur_baldosa_modern_root_practice_active(void) { return 0; }
extern "C" int ur_baldosa_modern_root_restore_practice_on_shutdown(void) {
    return 1;
}

extern "C" void RtlSetSaveRoot(const char* value) {
    root = value && *value ? value : "saves";
}
extern "C" const char* RtlSaveRoot(void) { return root.c_str(); }
extern "C" void RtlEnsureSaveDir(void) {
    std::filesystem::create_directories(root);
}

int main(int argc, char** argv) {
    namespace fs = std::filesystem;
    using namespace ur::product;

    // This reader is a new executable process, not the writer's live state.
    // Decode the two independently persisted Records types through the
    // existing real store/catalog codecs; never synthesize a guest result.
    if (argc == 3 && std::string(argv[1]) == "--verify-fresh-records") {
        const fs::path root = argv[2];
        const auto runs = load_valid_run_records(
            (root / "runs/rider-1").string());
        const auto matches = load_valid_multiplayer_matches(
            (root / "multiplayer-runs").string());
        if (runs.size() != 1 || matches.size() != 1) return 31;
        if (runs[0].record.provenance.mode != "race-1p" ||
            runs[0].record.provenance.course_id != "course:01" ||
            runs[0].record.elapsed_ticks60 != 740 ||
            runs[0].record.inputs.size() != 2) return 32;
        const auto& pair = matches[0];
        if (pair.run.provenance.mode != "race-2p" ||
            pair.run.provenance.course_id != "course:01" ||
            pair.run.inputs.size() != 1 ||
            pair.run.inputs[0].p1_mask != 0x10u ||
            pair.run.inputs[0].p2_mask != 0x20u ||
            pair.match.context.match.player1.profile_id != "rider-1" ||
            pair.match.context.match.player2.profile_id != "rider-2" ||
            pair.match.context.match.result.player1_hundredths != 2866 ||
            pair.match.context.match.result.player2_hundredths != 2977)
            return 33;
        std::puts("PASS: fresh-process native Modern 1P and paired 2P Records readback");
        return 0;
    }
    assert(argc == 1);

    const auto dir = fs::temp_directory_path() /
        ("ur-baldosa-real-modern-profile-" + std::to_string(getpid()));
    fs::create_directories(dir);
    assert(chdir(dir.c_str()) == 0);
    assert(setenv("SNESRECOMP_USER_DATA_DIR", dir.c_str(), 1) == 0);
    assert(setenv("UR_BALDOSA_MODERN_PROFILE_SELECT", "1", 1) == 0);
    assert(unsetenv("UR_HOST_STATE_PATH") == 0);
    assert(unsetenv("UR_EXECUTION_MODE") == 0);

    // A missing state is a new Modern installation, not an unnamed profile.
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves");

    HostProductState state{};
    state.active_profile_id = "rider-1";
    {
        std::ofstream output("host-state-v1.txt", std::ios::binary);
        assert(output << encode_host_product_state(state));
    }

    // A registered active name with no actual profile state must NOT silently
    // create (or initialize from) another player's generic save.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");

    fs::create_directories("saves/profile-rider-1");
    auto profile = make_default_host_profile_state("rider-1");
    assert(profile.has_value());
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);

    // Initializing guest SRAM is the existing frontend's job, not this
    // read-only selector. We must not create a blank 8 KiB save here.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");
    std::array<std::uint8_t, kStockSramBytes> initialized{};
    initialized.fill(0x31u);
    {
        std::ofstream save("saves/profile-rider-1/save.srm", std::ios::binary);
        save.write(reinterpret_cast<const char*>(initialized.data()),
                   initialized.size());
        assert(save.good());
    }

    // An identity-less named file is not an authorized Modern player, even
    // when a valid 8 KiB native SRAM happens to exist beside it.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");

    const auto identity = make_legacy_racer_identity(0);
    assert(identity.has_value());
    profile->racer_identity = *identity;
    assert(capture_stock_sram_for_profile(
        ExecutionMode::Modern, *profile, initialized.data(),
        initialized.size()) == HostProfileTransferStatus::Applied);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);

    // Even complete metadata remains untrusted until registered in the
    // original Modern catalog. Do not infer roster membership from filename.
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");
    assert(save_host_profile_catalog_file(
        "profiles-v1.txt", {{"rider-1", *identity}}));
    // A full-length but mismatched raw image is not permission to boot a
    // different snapshot from the typed selected Modern profile.
    {
        auto wrong = initialized;
        wrong[0x30] ^= 0x55u;
        std::ofstream raw("saves/profile-rider-1/save.srm",
                          std::ios::binary | std::ios::trunc);
        raw.write(reinterpret_cast<const char*>(wrong.data()), wrong.size());
        assert(raw.good());
    }
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    {
        std::ofstream raw("saves/profile-rider-1/save.srm",
                          std::ios::binary | std::ios::trunc);
        raw.write(reinterpret_cast<const char*>(initialized.data()),
                  initialized.size());
        assert(raw.good());
    }
    // Matching typed/raw bytes reached through a redirected parent must
    // never authorize native boot, even when all file contents are valid.
    const fs::path selected_dir = "saves/profile-rider-1";
    const fs::path redirected_dir = dir / "moved-selected-profile";
    fs::rename(selected_dir, redirected_dir);
    fs::create_directory_symlink(redirected_dir, selected_dir);
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves");
    fs::remove(selected_dir);
    fs::create_directory_symlink(dir / "missing-selected-profile", selected_dir);
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    fs::remove(selected_dir);
    fs::rename(redirected_dir, selected_dir);
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves/profile-rider-1");
    assert(selected_racer == identity->name);
    assert(fs::file_size("saves/profile-rider-1/save.srm") == kStockSramBytes);
    assert(!fs::exists("saves/save.srm"));

    // Real native guest has already loaded its selected SRAM before the
    // after-frame publisher runs. This isolated fixture must model that
    // existing precondition explicitly.
    g_sram = initialized.data();
    g_sram_size = static_cast<int>(initialized.size());
    assert(ur_baldosa_modern_profile_can_begin_race());
    // Synthetic fixture tests the profile authorization/publisher only;
    // this does NOT stand in for a live guest-finished Windows event.
    BaldosaSettledResult witnessed{};
    witnessed.kind = BaldosaSettledResultKind::TimedOnePlayerRace;
    witnessed.first_race_host_frame = 100;
    witnessed.observed_result_host_frame = 104;
    witnessed.p1_finish_ticks60 = 740;
    witnessed.course_index = 1;
    witnessed.captured_input_frames = 4;
    witnessed.mapped_inputs = {{0, 2, 0x10u, 0}, {3, 1, 0x20u, 0}};
    const fs::path run_root = dir / "runs/rider-1";
    // Redirect the same selected path AFTER native boot. Refuse both 1P
    // immutable Records publication and post-guest SRAM save preflight.
    fs::rename(selected_dir, redirected_dir);
    fs::create_directory_symlink(redirected_dir, selected_dir);
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&witnessed));
    assert(!ur_baldosa_modern_profile_before_native_save());
    assert(!ur_baldosa_modern_profile_can_begin_race());
    assert(!fs::exists(run_root));
    fs::remove(selected_dir);
    fs::rename(redirected_dir, selected_dir);
    assert(ur_baldosa_modern_profile_can_begin_race());
    assert(!ur_baldosa_modern_publish_settled_one_player_run(nullptr));
    assert(ur_baldosa_modern_publish_settled_one_player_run(&witnessed) == 1);
    auto recorded = load_valid_run_records(run_root.string());
    assert(recorded.size() == 1);
    assert(recorded[0].record.provenance.course_id == "course:01");
    assert(recorded[0].record.provenance.mode == "race-1p");
    assert(recorded[0].record.provenance.build_compat_id ==
           kBaldosaNativeRunCompatId);
    assert(recorded[0].record.elapsed_ticks60 == 740);
    assert(recorded[0].record.frame_count == 4);
    assert(recorded[0].record.inputs.size() == 2);
    // A duplicated post-result poll must not mint a second .urrun.
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&witnessed));
    assert(load_valid_run_records(run_root.string()).size() == 1);
    auto bad_result = witnessed;
    bad_result.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    bad_result = witnessed;
    bad_result.course_index = 2; // Circuit cannot mint 1P Race
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));

    // An untrusted symlinked run directory may not redirect the append to
    // another user's path, even if the typed selector still matches.
    const fs::path foreign = dir / "foreign-runs";
    fs::create_directories(foreign);
    const auto original_run = run_root;
    fs::rename(original_run, dir / "moved-runs");
    fs::create_directory_symlink(foreign, original_run);
    bad_result = witnessed;
    bad_result.first_race_host_frame = 200;
    bad_result.observed_result_host_frame = 204;
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    assert(fs::is_empty(foreign));
    fs::remove(original_run);
    // Broken symlinks are filesystem entries too. The product preflight
    // must reject them before canonical Records append is even attempted.
    fs::create_directory_symlink(dir / "missing-run-target", original_run);
    bad_result.first_race_host_frame = 220;
    bad_result.observed_result_host_frame = 224;
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    assert(fs::is_symlink(original_run));
    assert(!fs::exists(dir / "missing-run-target"));
    fs::remove(original_run);
    fs::rename(dir / "moved-runs", original_run);

    // The shared parent directory also must not be a dangling symlink.
    fs::rename(dir / "runs", dir / "moved-parent");
    fs::create_directory_symlink(dir / "missing-parent", dir / "runs");
    bad_result.first_race_host_frame = 240;
    bad_result.observed_result_host_frame = 244;
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    assert(!fs::exists(dir / "missing-parent"));
    fs::remove(dir / "runs");
    fs::rename(dir / "moved-parent", dir / "runs");
    assert(load_valid_run_records(run_root.string()).size() == 1);



    // This is a SYNTHETIC provider/persistence unit contract, not a played
    // native guest result. Both explicitly named identities must exist in
    // the existing Modern catalog and have independent, matching 8-KiB SRAM.
    const auto identity2 = make_legacy_racer_identity(1);
    assert(identity2);
    const HostProfileCatalogEntry p1{"rider-1", *identity};
    const HostProfileCatalogEntry p2{"rider-2", *identity2};
    fs::create_directories("saves/profile-rider-2");
    auto other_profile = make_default_host_profile_state("rider-2");
    assert(other_profile);
    other_profile->racer_identity = *identity2;
    std::array<std::uint8_t, kStockSramBytes> opponent_sram{};
    opponent_sram.fill(0x52u);
    assert(capture_stock_sram_for_profile(
        ExecutionMode::Modern, *other_profile,
        opponent_sram.data(), opponent_sram.size()) ==
        HostProfileTransferStatus::Applied);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-2/host-profile.txt", *other_profile) ==
        HostProfileSaveStatus::Saved);
    {
        std::ofstream raw("saves/profile-rider-2/save.srm", std::ios::binary);
        assert(raw);
        raw.write(reinterpret_cast<const char*>(opponent_sram.data()),
                  opponent_sram.size());
        assert(raw.good());
    }
    assert(save_host_profile_catalog_file(
        "profiles-v1.txt", {p1, p2}));
    assert(ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p1));
    assert(!ur_baldosa_modern_profile_can_join_opponent(nullptr));
    BaldosaSettledResult observed_2p{};
    observed_2p.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    observed_2p.first_race_host_frame = 500;
    observed_2p.observed_result_host_frame = 504;
    observed_2p.course_index = 1;
    observed_2p.captured_input_frames = 4;
    observed_2p.mapped_inputs = {{0, 2, 0x10u, 0x20u}};
    ur::title::OrdinaryTwoPlayerRaceResult title_result{};
    title_result.player1_rider = 0;
    title_result.player2_rider = 1;
    title_result.player1_hundredths = 2866;
    title_result.player2_hundredths = 2977;
    title_result.outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    observed_2p.two_player = title_result;
    const auto multiplayer_root = dir / "multiplayer-runs";
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        nullptr, &p1, &p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &observed_2p, &p1, nullptr));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &observed_2p, &p1, &p1));
    {
        auto mismatch = p2;
        mismatch.identity.rider_index = 2;
        assert(!ur_baldosa_modern_publish_settled_two_player_match(
            &observed_2p, &p1, &mismatch));
    }
    const std::string selector_path = (dir / "host-state-v1.txt").string();
    {
        TournamentLaunchPathLock blocked(selector_path, true);
        assert(blocked.acquired());
        assert(!ur_baldosa_modern_publish_settled_two_player_match(
            &observed_2p, &p1, &p2));
        assert(!fs::exists(multiplayer_root));
    }
    assert(ur_baldosa_modern_publish_settled_two_player_match(
        &observed_2p, &p1, &p2));
    auto pairs = load_valid_multiplayer_matches(multiplayer_root.string());
    assert(pairs.size() == 1);
    assert(pairs[0].match.context.match.player1.profile_id == "rider-1");
    assert(pairs[0].match.context.match.player2.profile_id == "rider-2");
    assert(pairs[0].run.provenance.mode == "race-2p");
    assert(pairs[0].run.provenance.course_id == "course:01");
    assert(pairs[0].run.inputs[0].p1_mask == 0x10u);
    assert(pairs[0].run.inputs[0].p2_mask == 0x20u);
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &observed_2p, &p1, &p2));
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // A new process image must reopen the canonical 1P run and both linked
    // 2P match artifacts; same-process loads above are insufficient proof.
    const auto child = fork();
    assert(child >= 0);
    if (child == 0) {
        const auto executable = fs::absolute(argv[0]).string();
        execl(executable.c_str(), executable.c_str(),
              "--verify-fresh-records", dir.c_str(),
              static_cast<char*>(nullptr));
        _exit(127);
    }
    int fresh_status = 0;
    assert(waitpid(child, &fresh_status, 0) == child);
    assert(WIFEXITED(fresh_status) && WEXITSTATUS(fresh_status) == 0);

    // The canonical shared match writer must reject both live and broken
    // symlink substitutions before creating any stage/public run outside
    // the authorized user root. An already published pair survives intact.
    const auto moved_pairs = dir / "moved-multiplayer-runs";
    const auto foreign_pairs = dir / "foreign-multiplayer-runs";
    fs::create_directories(foreign_pairs);
    fs::rename(multiplayer_root, moved_pairs);
    fs::create_directory_symlink(foreign_pairs, multiplayer_root);
    auto redirected_event = observed_2p;
    redirected_event.first_race_host_frame = 540;
    redirected_event.observed_result_host_frame = 544;
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(fs::is_empty(foreign_pairs));
    fs::remove(multiplayer_root);
    fs::create_directory_symlink(dir / "missing-multiplayer", multiplayer_root);
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(!fs::exists(dir / "missing-multiplayer"));
    fs::remove(multiplayer_root);
    fs::rename(moved_pairs, multiplayer_root);
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // The inactive P2 SRAM is checked against the fully persisted typed
    // profile, not against any guessed seat, original result or shared save.
    {
        auto wrong = opponent_sram;
        wrong[0x20] ^= 0x44;
        std::ofstream raw("saves/profile-rider-2/save.srm",
                          std::ios::binary | std::ios::trunc);
        assert(raw);
        raw.write(reinterpret_cast<const char*>(wrong.data()), wrong.size());
        assert(raw.good());
    }
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    {
        std::ofstream raw("saves/profile-rider-2/save.srm",
                          std::ios::binary | std::ios::trunc);
        assert(raw);
        raw.write(reinterpret_cast<const char*>(opponent_sram.data()),
                  opponent_sram.size());
        assert(raw.good());
    }
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // Even a byte-identical off-root raw SRAM is not an authorized P2
    // profile. Reject live and broken file symlinks BEFORE opening the
    // canonical publisher leases, not merely after comparing their bytes.
    const fs::path p2_raw = "saves/profile-rider-2/save.srm";
    const fs::path p2_typed = "saves/profile-rider-2/host-profile.txt";
    const fs::path parked_raw = dir / "parked-p2-raw.srm";
    const fs::path parked_typed = dir / "parked-p2-typed.txt";
    const fs::path foreign_raw = dir / "foreign-p2-raw.srm";
    const fs::path foreign_typed = dir / "foreign-p2-typed.txt";
    fs::copy_file(p2_raw, foreign_raw);
    fs::copy_file(p2_typed, foreign_typed);
    fs::rename(p2_raw, parked_raw);
    fs::create_symlink(foreign_raw, p2_raw);
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(fs::file_size(foreign_raw) == kStockSramBytes);
    fs::remove(p2_raw);
    fs::create_symlink(dir / "missing-p2-raw.srm", p2_raw);
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(!fs::exists(dir / "missing-p2-raw.srm"));
    fs::remove(p2_raw);
    fs::rename(parked_raw, p2_raw);
    assert(ur_baldosa_modern_profile_can_join_opponent(&p2));

    fs::rename(p2_typed, parked_typed);
    fs::create_symlink(foreign_typed, p2_typed);
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    fs::remove(p2_typed);
    fs::create_symlink(dir / "missing-p2-typed.txt", p2_typed);
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(!fs::exists(dir / "missing-p2-typed.txt"));
    fs::remove(p2_typed);
    fs::rename(parked_typed, p2_typed);
    assert(ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // A substituted P2 profile directory may NOT be used even to create
    // an OS lockfile: redirecting the profile would escape the native
    // user's original Modern save namespace before post-lock validation.
    const fs::path second_dir = "saves/profile-rider-2";
    const fs::path moved_second = dir / "moved-second-profile";
    const fs::path redirected_second = dir / "outside-second-profile";
    fs::create_directories(redirected_second);
    fs::rename(second_dir, moved_second);
    fs::create_directory_symlink(redirected_second, second_dir);
    assert(!ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(fs::is_empty(redirected_second));
    fs::remove(second_dir);
    fs::create_directory_symlink(dir / "missing-second-profile", second_dir);
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &redirected_event, &p1, &p2));
    assert(!fs::exists(dir / "missing-second-profile"));
    fs::remove(second_dir);
    fs::rename(moved_second, second_dir);
    assert(ur_baldosa_modern_profile_can_join_opponent(&p2));
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // An out-of-band profile identity change makes the confirmed P2
    // catalog entry stale. No match may be minted against the old rider.
    auto changed = *other_profile;
    const auto new_identity = make_legacy_racer_identity(3);
    assert(new_identity);
    changed.racer_identity = *new_identity;
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-2/host-profile.txt", changed) ==
        HostProfileSaveStatus::Saved);
    auto new_event = observed_2p;
    new_event.first_race_host_frame = 520;
    new_event.observed_result_host_frame = 524;
    assert(!ur_baldosa_modern_publish_settled_two_player_match(
        &new_event, &p1, &p2));
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);
    assert(save_host_profile_state_file(
        ExecutionMode::Modern,
        "saves/profile-rider-2/host-profile.txt", *other_profile) ==
        HostProfileSaveStatus::Saved);
    assert(load_valid_multiplayer_matches(multiplayer_root.string()).size() == 1);

    // The original framework write MUST be preceded by a compatible typed
    // selection check under the canonical OS lock, retained until CAS.
    g_sram = initialized.data();
    g_sram_size = static_cast<int>(initialized.size());
    const std::string global_path = (dir / "host-state-v1.txt").string();
    const std::string typed_profile_path =
        (dir / "saves/profile-rider-1/host-profile.txt").string();
    const std::string catalog_path = (dir / "profiles-v1.txt").string();
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    {
        TournamentLaunchPathLock competing_global(global_path, true);
        TournamentLaunchPathLock competing_catalog(catalog_path, true);
        TournamentLaunchPathLock competing_profile(typed_profile_path, true);
        assert(!competing_global.acquired());
        assert(!competing_catalog.acquired());
        assert(!competing_profile.acquired());
    }
    assert(ur_baldosa_modern_profile_finish_native_save(1) == 1);
    {
        TournamentLaunchPathLock released_global(global_path, true);
        TournamentLaunchPathLock released_catalog(catalog_path, true);
        TournamentLaunchPathLock released_profile(typed_profile_path, true);
        assert(released_global.acquired());
        assert(released_catalog.acquired());
        assert(released_profile.acquired());
    }

    // An external Modern instance can change selector/profile while this
    // native process runs; shutdown must refuse BEFORE writing raw SRAM.
    const fs::path selected_raw = "saves/profile-rider-1/save.srm";
    const auto original_raw_size = fs::file_size(selected_raw);
    const auto assert_raw_unchanged = [&] {
        std::array<std::uint8_t, kStockSramBytes> raw{};
        std::ifstream in(selected_raw, std::ios::binary);
        assert(in);
        in.read(reinterpret_cast<char*>(raw.data()), raw.size());
        assert(in.gcount() == static_cast<std::streamsize>(raw.size()));
        assert(raw == initialized);
    };
    HostProductState different_selector = state;
    different_selector.active_profile_id.reset();
    assert(save_host_product_state_file(global_path, different_selector) ==
           HostProductSaveStatus::Saved);
    assert(!ur_baldosa_modern_profile_can_begin_race());
    bad_result = witnessed;
    bad_result.first_race_host_frame = 300;
    bad_result.observed_result_host_frame = 304;
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    assert(load_valid_run_records(run_root.string()).size() == 1);
    assert(ur_baldosa_modern_profile_before_native_save() == 0);
    assert(fs::file_size("saves/profile-rider-1/save.srm") ==
           original_raw_size);
    assert_raw_unchanged();
    assert(save_host_product_state_file(global_path, state) ==
           HostProductSaveStatus::Saved);
    assert(ur_baldosa_modern_profile_can_begin_race());

    auto newer_profile = *profile;
    newer_profile.recent_track = 7;
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        newer_profile) == HostProfileSaveStatus::Saved);
    assert(!ur_baldosa_modern_profile_can_begin_race());
    assert(ur_baldosa_modern_profile_before_native_save() == 0);
    assert(fs::file_size("saves/profile-rider-1/save.srm") ==
           original_raw_size);
    assert_raw_unchanged();
    assert(save_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        *profile) == HostProfileSaveStatus::Saved);
    assert(ur_baldosa_modern_profile_can_begin_race());

    // A second process (or filesystem manipulation) changed the raw save
    // without publishing a matching typed profile. Reject before overwriting.
    {
        auto wrong = initialized;
        wrong[0x31] ^= 0x6au;
        std::ofstream raw(selected_raw, std::ios::binary | std::ios::trunc);
        raw.write(reinterpret_cast<const char*>(wrong.data()), wrong.size());
        assert(raw.good());
    }
    assert(ur_baldosa_modern_profile_before_native_save() == 0);
    {
        std::ofstream raw(selected_raw, std::ios::binary | std::ios::trunc);
        raw.write(reinterpret_cast<const char*>(initialized.data()),
                  initialized.size());
        assert(raw.good());
    }
    assert_raw_unchanged();

    // Real canonical writer recovery: transient selector contention refuses
    // the first attempt without creating a partial .urrun. The exact same
    // source-settled event may succeed after lease release, but a third poll
    // must not publish its result twice. The in-memory retry policy has its
    // own timing/session test; this exercises the actual persistence seam.
    bad_result = witnessed;
    bad_result.first_race_host_frame = 400;
    bad_result.observed_result_host_frame = 404;
    const auto previous_runs = load_valid_run_records(run_root.string()).size();
    {
        TournamentLaunchPathLock blocked_selector(global_path, true);
        assert(blocked_selector.acquired());
        assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
        assert(load_valid_run_records(run_root.string()).size() ==
               previous_runs);
    }
    assert(ur_baldosa_modern_publish_settled_one_player_run(&bad_result) == 1);
    assert(load_valid_run_records(run_root.string()).size() ==
           previous_runs + 1);
    assert(!ur_baldosa_modern_publish_settled_one_player_run(&bad_result));
    assert(load_valid_run_records(run_root.string()).size() ==
           previous_runs + 1);

    // Failed upstream SRAM I/O must also release the selector lease.
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    assert(ur_baldosa_modern_profile_finish_native_save(0) == 0);
    {
        TournamentLaunchPathLock released_global(global_path, true);
        TournamentLaunchPathLock released_catalog(catalog_path, true);
        TournamentLaunchPathLock released_profile(typed_profile_path, true);
        assert(released_global.acquired());
        assert(released_catalog.acquired());
        assert(released_profile.acquired());
    }

    // The successful path still delegates the actual guest bytes to the
    // framework save, then publishes only the validated typed Modern CAS.
    std::array<std::uint8_t, kStockSramBytes> advanced = initialized;
    advanced[0x0748] ^= 0xC3u;
    g_sram = advanced.data();
    assert(ur_baldosa_modern_profile_before_native_save() == 1);
    {
        std::ofstream raw(selected_raw, std::ios::binary | std::ios::trunc);
        assert(raw);
        raw.write(reinterpret_cast<const char*>(advanced.data()),
                  advanced.size());
        assert(raw.good());
    }
    assert(ur_baldosa_modern_profile_finish_native_save(1) == 1);
    const auto after_real_save = load_host_profile_state_file(
        ExecutionMode::Modern, "saves/profile-rider-1/host-profile.txt",
        "rider-1");
    assert(after_real_save.loaded());
    assert(after_real_save.state->stock_sram &&
           *after_real_save.state->stock_sram == advanced);
    assert(fs::file_size(selected_raw) == original_raw_size);

    // An invalid loaded selector must NEVER downgrade to default saves.
    state.active_profile_id = "../other-player";
    {
        std::ofstream output("host-state-v1.txt", std::ios::binary | std::ios::trunc);
        output << "not-a-valid-modern-host-state\n";
    }
    assert(ur_baldosa_modern_try_activate_profile() == 0);
    assert(root == "saves/profile-rider-1");

    // The existing Authentic mode has no Modern profile authority.
    assert(setenv("UR_EXECUTION_MODE", "authentic", 1) == 0);
    assert(ur_baldosa_modern_try_activate_profile() == 1);
    assert(root == "saves/profile-rider-1");

    assert(chdir("/") == 0);
    fs::remove_all(dir);
    std::puts("PASS: native Modern pre-SRAM profile root respects exact stored state and fails closed");
}

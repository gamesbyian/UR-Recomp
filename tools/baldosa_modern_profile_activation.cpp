/* Existing Modern product state -> pinned Baldosa host's own SRAM root.
 *
 * No new profile store, loader, router, or file format. The exact
 * after_config hook runs after framework cwd is anchored to the existing
 * per-user root, before RtlReadSram or guest initialization.
 *
 * This is an opt-in native backend integration seam until the existing
 * visible Modern root launches Baldosa itself. It deliberately refuses an
 * incomplete or invalid selected profile instead of silently loading the
 * default/another player's save. New-profile seeding still belongs to the
 * full existing Modern activation transaction.
 */
#include "host_product_store.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_store.hpp"
#include "host_profile_catalog.hpp"
#include "baldosa_native_profile_sram_checkpoint.hpp"
#include "baldosa_native_profile_path_guard.hpp"
#include "baldosa_native_run_record_admission.hpp"
#include "completed_run_store.hpp"
#include "local_multiplayer_match_binding.hpp"
#include "multiplayer_match_record.hpp"
extern "C" void ur_baldosa_modern_root_set_racer_name(const char* name);

#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <optional>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <system_error>

extern "C" void RtlSetSaveRoot(const char*);
extern "C" const char* RtlSaveRoot(void);
extern "C" void RtlEnsureSaveDir(void);
extern "C" unsigned char* g_sram;
extern "C" int g_sram_size;

namespace {

std::string g_verified_native_profile_id;
std::filesystem::path g_native_user_root;
std::optional<ur::product::HostProductState> g_launch_global;
std::optional<ur::product::HostProfileState> g_launch_profile;
std::optional<std::pair<std::uint64_t, std::uint64_t>>
    g_last_published_one_player_event;
std::optional<std::pair<std::uint64_t, std::uint64_t>>
    g_last_published_two_player_event;
// Shutdown-scoped owners of the existing selector, catalog, profile locks.
// Never hold them across gameplay or reacquire them inside the typed CAS.
std::unique_ptr<ur::product::TournamentLaunchPathLock>
    g_native_shutdown_selector_lock;
std::unique_ptr<ur::product::TournamentLaunchPathLock>
    g_native_shutdown_profile_lock;
std::unique_ptr<ur::product::TournamentLaunchPathLock>
    g_native_shutdown_catalog_lock;

int reject(const char* why) {
    std::fprintf(stderr, "UR_BALDOSA_NATIVE_PROFILE REJECTED reason=%s\n", why);
    std::fflush(stderr);
    return 0;
}

bool activated() {
    const char* enabled = std::getenv("UR_BALDOSA_MODERN_PROFILE_SELECT");
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return enabled && std::strcmp(enabled, "1") == 0 &&
        !(mode && std::strcmp(mode, "authentic") == 0);
}

}  // namespace

/* Return 1 only when it is safe to enter the normal upstream native host.
 * Callers must fail closed on 0; the guest has not started at this point.
 */
extern "C" int ur_baldosa_modern_try_activate_profile(void) {
    if (!activated()) return 1;

    // The same root the existing portable Windows launcher validates.
    // Do not interpret an executable-relative host-state file as a profile.
    const char* user_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!user_root || !*user_root)
        return reject("modern_user_root_absent");

    const std::filesystem::path native_root(user_root);
    if (!native_root.is_absolute())
        return reject("modern_user_root_not_absolute");

    // The post-save writer uses the canonical selector in this exact root.
    // An alternate selector pathname cannot authorize a native publication.
    const char* override_path = std::getenv("UR_HOST_STATE_PATH");
    if (override_path && *override_path &&
        std::string_view(override_path) != "host-state-v1.txt")
        return reject("noncanonical_selector_override");
    const std::string state_path =
        override_path && *override_path ? override_path : "host-state-v1.txt";
    const auto global =
        ur::product::load_host_product_state_file(state_path);
    if (global.status == ur::product::HostProductLoadStatus::Missing) {
        // Identical to the old Modern host's fresh-install default root.
        RtlSetSaveRoot(nullptr);
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n");
        return 1;
    }
    if (!global.loaded()) return reject("host_state_invalid");

    const auto& id = global.state->active_profile_id;
    if (!id) {
        RtlSetSaveRoot(nullptr);
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_active_profile=1\n");
        return 1;
    }

    const auto decision = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern, id);
    if (!decision.isolated())
        return reject("active_profile_id_invalid");

    // A regular SRAM file can still be reached through a symlinked parent.
    // Admit the complete existing Modern profile path before reading data.
    if (!ur::product::baldosa_native_selected_profile_paths_are_real(
            native_root, decision.save_root))
        return reject("selected_profile_path_redirected_or_incomplete");
    const std::string profile_path = decision.save_root + "/host-profile.txt";
    const auto profile = ur::product::load_host_profile_state_file(
        ur::product::ExecutionMode::Modern, profile_path, *id);
    if (!profile.loaded())
        return reject("selected_profile_state_missing_or_invalid");

    // A named Modern profile is not a legacy anonymous SRAM slot.
    // The existing visible Modern frontend ALWAYS requires a catalog
    // membership backed by both a racer identity and a stock SRAM snapshot.
    // A partially created, unregistered or identity-less file must not be
    // launched as though it were an authorized active player.
    const auto roster = ur::product::load_host_profile_catalog_file(
        "profiles-v1.txt");
    if (!roster || !ur::product::profile_catalog_authorizes_state(
            *roster, *profile.state))
        return reject("selected_profile_catalog_mismatch");

    // First-activation seeding and profile SRAM synchronization are NOT
    // exposed by this seam yet. Refuse to boot a fresh named profile from
    // empty SRAM or to overwrite an existing progression file by accident.
    // Use only a durable 8 KiB native SRAM image from Modern's real store.
    std::error_code ec;
    const std::filesystem::path sram_path =
        decision.save_root + "/save.srm";
    if (std::filesystem::is_symlink(sram_path, ec) || ec)
        return reject("selected_profile_sram_not_initialized");
    if (!ur::product::baldosa_sram_file_matches_exact(
            sram_path, profile.state->stock_sram->data(),
            ur::product::kStockSramBytes)) {
        // A missing/short initial save is not the same as a full-size raw
        // image contradicting the previously committed Modern profile.
        // Never silently make the raw copy authoritative or repair it:
        // a crash after RtlWriteSram and before typed CAS can cause this,
        // but so can corruption or an out-of-band writer.
        ec.clear();
        if (std::filesystem::is_regular_file(sram_path, ec) && !ec &&
            std::filesystem::file_size(sram_path, ec) ==
                ur::product::kStockSramBytes && !ec) {
            std::fprintf(stderr,
                "UR-BALDOSA-SAVE-MISMATCH: Named racer SRAM differs from "
                "committed profile data. Preserve both files; recovery "
                "requires an explicit decision. No guest started.\n");
            std::fflush(stderr);
        }
        return reject("selected_profile_sram_not_initialized");
    }

    RtlSetSaveRoot(decision.save_root.c_str());
    if (!RtlSaveRoot() ||
        std::string_view(RtlSaveRoot()) != decision.save_root)
        return reject("native_save_root_mismatch");
    RtlEnsureSaveDir();
    g_verified_native_profile_id = *id;
    g_native_user_root = native_root;
    g_launch_global = *global.state;
    g_launch_profile = *profile.state;
    ur_baldosa_modern_root_set_racer_name(
        g_launch_profile->racer_identity->name.c_str());
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=%s root=%s\n",
        id->c_str(), RtlSaveRoot());
    std::fflush(stderr);
    return 1;
}


// Read-only admission used solely to display P2 profile choices in the
// real native root. A catalog name is not enough: the opponent must have
// independently initialized typed identity and exactly matching raw SRAM.
// This does not authorize a future result or cache a file capability; the
// pair writer must revalidate under its own selector/profile OS locks.
extern "C" int ur_baldosa_modern_profile_can_join_opponent(
    const ur::product::HostProfileCatalogEntry* entry) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    if (!entry || !activated() || !g_launch_global ||
        !g_launch_profile || g_verified_native_profile_id.empty() ||
        g_native_user_root.empty() ||
        entry->profile_id == g_verified_native_profile_id ||
        !is_safe_profile_storage_id(entry->profile_id) ||
        !valid_racer_identity(entry->identity))
        return 0;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, entry->profile_id);
    if (!location.isolated()) return 0;
    const auto root = g_native_user_root / location.save_root;
    // Same canonical profile-path admission as P1 native boot and writer.
    if (!baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, location.save_root)) return 0;
    const auto profile = load_host_profile_state_file(
        ExecutionMode::Modern, (root / "host-profile.txt").string(),
        entry->profile_id);
    if (!profile.loaded() ||
        !catalog_entry_matches_profile_state(*entry, *profile.state) ||
        !profile.state->stock_sram)
        return 0;
    return baldosa_sram_file_matches_exact(
        root / "save.srm", profile.state->stock_sram->data(),
        kStockSramBytes) ? 1 : 0;
}

// A named Modern player is not safe to start another race if an external
// instance changed the selected catalog, typed profile or raw SRAM after
// this native process booted. Reuse the original canonical CAS preflight and
// nonblocking OS leases; never write/save anything during this check.
// Anonymous and Authentic stock play retain their existing execution path.
extern "C" int ur_baldosa_modern_profile_can_begin_race(void) {
    using namespace ur::product;
    if (!activated() || g_verified_native_profile_id.empty()) return 1;
    if (!g_launch_global || !g_launch_profile ||
        !g_launch_profile->stock_sram || g_native_user_root.empty() ||
        !g_sram || g_sram_size != static_cast<int>(kStockSramBytes))
        return 0;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, g_verified_native_profile_id);
    if (!location.isolated() ||
        !baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, location.save_root)) return 0;
    const auto typed_path = g_native_user_root / location.save_root /
                            "host-profile.txt";
    TournamentLaunchPathLock selector(
        (g_native_user_root / "host-state-v1.txt").string(), true);
    if (!selector.acquired()) return 0;
    TournamentLaunchPathLock roster(
        (g_native_user_root / "profiles-v1.txt").string(), true);
    if (!roster.acquired()) return 0;
    TournamentLaunchPathLock profile(typed_path.string(), true);
    if (!profile.acquired() ||
        !baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, location.save_root)) return 0;
    const BaldosaSramCheckpoint source{
        g_native_user_root, *g_launch_global, *g_launch_profile,
        g_sram, static_cast<std::size_t>(g_sram_size)};
    if (baldosa_sram_checkpoint_preflight_under_lock(source))
        return 0;
    return baldosa_sram_file_matches_exact(
        g_native_user_root / location.save_root / "save.srm",
        g_launch_profile->stock_sram->data(), kStockSramBytes) ? 1 : 0;
}

// Read-only native Modern root adapter: expose only the verified profile's
// canonical archive directory. Never infer identity from a display name or
// enumerate a different root. Records inspection has NO write authority.
// Source-authenticated P1 result -> existing immutable Records writer.
// A synthetic result, default save, stale selector or lost profile must not
// acquire a write capability. Guest result and input sampling remain elsewhere.
extern "C" int ur_baldosa_modern_publish_settled_one_player_run(
    const ur::product::BaldosaSettledResult* result) {
    namespace fs = std::filesystem;
    if (!result || !activated() || g_verified_native_profile_id.empty() ||
        !g_launch_global || !g_launch_profile || g_native_user_root.empty() ||
        !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes))
        return 0;
    if (result->kind !=
        ur::product::BaldosaSettledResultKind::TimedOnePlayerRace)
        return 0;
    const auto event = std::make_pair(
        result->first_race_host_frame, result->observed_result_host_frame);
    if (g_last_published_one_player_event == event) return 0;
    const auto run = ur::product::assemble_baldosa_native_run_record(
        *result, {true, false});
    if (!run || g_verified_native_profile_id != g_launch_profile->profile_id ||
        !ur::product::is_safe_profile_storage_id(g_verified_native_profile_id))
        return 0;

    const auto selected_root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern, g_verified_native_profile_id);
    if (!selected_root.isolated()) return 0;
    const fs::path profile_root = g_native_user_root / selected_root.save_root;
    const fs::path profile_path = profile_root / "host-profile.txt";
    // Refuse redirected P1 profile path before acquiring any lock handles.
    if (!ur::product::baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, selected_root.save_root)) return 0;
    ur::product::TournamentLaunchPathLock selector(
        (g_native_user_root / "host-state-v1.txt").string(), true);
    if (!selector.acquired()) return 0;
    ur::product::TournamentLaunchPathLock roster(
        (g_native_user_root / "profiles-v1.txt").string(), true);
    if (!roster.acquired()) return 0;
    ur::product::TournamentLaunchPathLock profile(profile_path.string(), true);
    if (!profile.acquired()) return 0;
    if (!ur::product::baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, selected_root.save_root)) return 0;

    // Recheck all three typed sources while their existing nonblocking OS
    // leases remain owned across immutable run publication.
    const ur::product::BaldosaSramCheckpoint selected{
        g_native_user_root, *g_launch_global, *g_launch_profile,
        g_sram, static_cast<std::size_t>(g_sram_size)};
    if (ur::product::baldosa_sram_checkpoint_preflight_under_lock(selected))
        return 0;
    if (!ur::product::baldosa_sram_file_matches_exact(
            profile_root / "save.srm",
            g_launch_profile->stock_sram->data(),
            ur::product::kStockSramBytes))
        return 0;

    // Refuse preexisting symlinked Records roots or profile directories.
    // This is an explicit no-follow preflight atop the canonical append
    // writer; it does not claim race-free path opening against malicious
    // directory replacements by an uncooperating process.
    const fs::path parent = g_native_user_root / "runs";
    const fs::path directory = parent / g_verified_native_profile_id;
    const auto safe_directory = [](const fs::path& candidate) {
        std::error_code ec;
        // Inspect the entry, not its target: exists() follows a dangling
        // symlink and wrongly accepts it as an absent first-run directory.
        const auto status = fs::symlink_status(candidate, ec);
        if (status.type() == fs::file_type::not_found)
            return !ec || ec == std::errc::no_such_file_or_directory;
        return !ec && !fs::is_symlink(status) &&
               fs::is_directory(status);
    };
    if (!safe_directory(parent) || !safe_directory(directory)) return 0;

    std::string path, detail;
    if (!ur::product::append_completed_run_record(
            directory.string(), *run, &path, &detail)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_RUN PUBLISH_REJECTED reason=%s\n",
            detail.c_str());
        std::fflush(stderr);
        return 0;
    }
    g_last_published_one_player_event = event;
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
        "profile=%s course=%s input_frames=%llu inputs=%zu path=%s\n",
        g_verified_native_profile_id.c_str(),
        run->provenance.course_id.c_str(),
        static_cast<unsigned long long>(run->frame_count),
        run->inputs.size(), path.c_str());
    std::fflush(stderr);
    return 1;
}

// Publish only an actual stock 2P Race result that belongs to two named
// profiles explicitly confirmed by distinct real host gamepad seats.
// The root's borrowed entries are NEVER sufficient authority by themselves:
// re-read all current persisted identities under the same canonical OS locks
// used by the existing 1P run and native SRAM publication paths.
extern "C" int ur_baldosa_modern_publish_settled_two_player_match(
    const ur::product::BaldosaSettledResult* result,
    const ur::product::HostProfileCatalogEntry* p1,
    const ur::product::HostProfileCatalogEntry* p2) {
    namespace fs = std::filesystem;
    using namespace ur::product;
    if (!result || !p1 || !p2 || !activated() || !g_launch_global ||
        !g_launch_profile || g_native_user_root.empty() ||
        g_verified_native_profile_id.empty() ||
        result->kind != BaldosaSettledResultKind::OrdinaryTwoPlayerRace ||
        !result->two_player || !g_sram ||
        g_sram_size != static_cast<int>(kStockSramBytes) ||
        p1->profile_id != g_verified_native_profile_id ||
        p1->profile_id != g_launch_profile->profile_id ||
        !g_launch_profile->racer_identity ||
        !(p1->identity == *g_launch_profile->racer_identity))
        return 0;
    const auto event = std::make_pair(
        result->first_race_host_frame, result->observed_result_host_frame);
    if (g_last_published_two_player_event == event) return 0;
    const auto course = UrUniracersCourseIdentity{1, result->course_index};
    const auto bound = bind_local_multiplayer_match_context(
        *result->two_player, *p1, *p2, course);
    if (!bound.bound()) return 0;
    const auto run = assemble_baldosa_native_run_record(
        *result, {true, true});
    if (!run) return 0;
    const auto match = make_multiplayer_match_record(
        *run, *bound.context);
    if (!match) return 0;

    const auto first = resolve_host_profile_save_root(
        ExecutionMode::Modern, p1->profile_id);
    const auto second = resolve_host_profile_save_root(
        ExecutionMode::Modern, p2->profile_id);
    if (!first.isolated() || !second.isolated()) return 0;
    const fs::path first_root = g_native_user_root / first.save_root;
    const fs::path second_root = g_native_user_root / second.save_root;
    const fs::path first_state = first_root / "host-profile.txt";
    const fs::path second_state = second_root / "host-profile.txt";
    // The common no-follow check covers both participants before any
    // profile lock handle is opened, including dangling parent symlinks.
    if (!baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, first.save_root) ||
        !baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, second.save_root))
        return 0;
    TournamentLaunchPathLock selector(
        (g_native_user_root / "host-state-v1.txt").string(), true);
    if (!selector.acquired()) return 0;
    TournamentLaunchPathLock catalog(
        (g_native_user_root / "profiles-v1.txt").string(), true);
    if (!catalog.acquired()) return 0;
    TournamentLaunchPathLock profile1(first_state.string(), true);
    if (!profile1.acquired()) return 0;
    TournamentLaunchPathLock profile2(second_state.string(), true);
    if (!profile2.acquired()) return 0;
    if (!baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, first.save_root) ||
        !baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, second.save_root))
        return 0;

    // Still-authorized P1 has the exact selector, catalog, typed profile and
    // raw named SRAM from process start. Do not replace it with new metadata.
    const BaldosaSramCheckpoint selected{
        g_native_user_root, *g_launch_global, *g_launch_profile,
        g_sram, static_cast<std::size_t>(g_sram_size)};
    if (baldosa_sram_checkpoint_preflight_under_lock(selected))
        return 0;
    if (!baldosa_sram_file_matches_exact(
            first_root / "save.srm",
            g_launch_profile->stock_sram->data(), kStockSramBytes))
        return 0;
    const auto roster = load_host_profile_catalog_file(
        (g_native_user_root / "profiles-v1.txt").string());
    const auto opponent = load_host_profile_state_file(
        ExecutionMode::Modern, second_state.string(), p2->profile_id);
    if (!roster || !opponent.loaded() ||
        !catalog_entry_matches_profile_state(*p1, *g_launch_profile) ||
        !catalog_entry_matches_profile_state(*p2, *opponent.state) ||
        !profile_catalog_authorizes_state(*roster, *g_launch_profile) ||
        !profile_catalog_authorizes_state(*roster, *opponent.state) ||
        !opponent.state->stock_sram ||
        !baldosa_sram_file_matches_exact(
            second_root / "save.srm",
            opponent.state->stock_sram->data(), kStockSramBytes))
        return 0;

    // One canonical namespace and one two-artifact atomic commit. Reject
    // substituted shared Records directories, including broken symlinks.
    const fs::path archive = g_native_user_root / "multiplayer-runs";
    std::error_code ec;
    const auto status = fs::symlink_status(archive, ec);
    if (ec && ec != std::errc::no_such_file_or_directory) return 0;
    if (status.type() != fs::file_type::not_found &&
        (fs::is_symlink(status) || !fs::is_directory(status))) return 0;
    std::string path, detail;
    if (!append_multiplayer_match_pair(
            archive.string(), *run, *match, &path, &detail)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_MATCH PUBLISH_REJECTED reason=%s\n",
            detail.c_str());
        return 0;
    }
    g_last_published_two_player_event = event;
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=%s profile2=%s "
        "course=%s frames=%llu path=%s\n",
        p1->profile_id.c_str(), p2->profile_id.c_str(),
        run->provenance.course_id.c_str(),
        static_cast<unsigned long long>(run->frame_count),
        path.c_str());
    return 1;
}

// The existing product's single shared ordinary-2P match archive is
// user-rooted (not inside either player's SRAM or 1P run directory).
// This is read-only from native Records; no 2P publication authority.
extern "C" const char*
ur_baldosa_modern_profile_multiplayer_records_directory(void) {
    static std::string path;
    if (!activated() || g_verified_native_profile_id.empty() ||
        g_native_user_root.empty()) return nullptr;
    path = (g_native_user_root / "multiplayer-runs").string();
    return path.c_str();
}

// The native Modern root must read the same absolute catalog already
// verified by profile activation. No cwd-relative second profile namespace.
extern "C" const char* ur_baldosa_modern_profile_catalog_path(void) {
    static std::string path;
    if (!activated() || g_verified_native_profile_id.empty() ||
        g_native_user_root.empty()) return nullptr;
    path = (g_native_user_root / "profiles-v1.txt").string();
    return path.c_str();
}

extern "C" const char* ur_baldosa_modern_profile_selected_id(void) {
    return activated() && !g_verified_native_profile_id.empty()
        ? g_verified_native_profile_id.c_str() : nullptr;
}

extern "C" const char* ur_baldosa_modern_profile_records_directory(void) {
    static std::string path;
    if (!activated() || g_verified_native_profile_id.empty() ||
        g_native_user_root.empty()) return nullptr;
    path = (g_native_user_root / "runs" /
            g_verified_native_profile_id).string();
    return path.c_str();
}


/* Called through the original game's optional title before_run_frame hook.
 * At this point the native host has called RtlReadSram from the selected
 * profile root, but has not run the first guest simulation frame yet.
 * Diagnostics only; zero guest writes, enabled solely by QA environment.
 */
extern "C" void ur_baldosa_modern_profile_before_run_frame(void) {
    static bool witnessed = false;
    const char* probe = std::getenv("UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS");
    if (witnessed || !probe || std::strcmp(probe, "1") != 0 ||
        !activated() || g_verified_native_profile_id.empty()) return;
    witnessed = true;
    if (!g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM_FAIL missing_or_wrong_size\n");
        std::abort();
    }
    std::uint32_t hash = 2166136261u;
    for (int i = 0; i < g_sram_size; ++i) {
        hash ^= g_sram[i];
        hash *= 16777619u;
    }
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=%s bytes=%d fnv=%08x\n",
        g_verified_native_profile_id.c_str(), g_sram_size,
        static_cast<unsigned>(hash));
    std::fflush(stderr);
}


// Called by the pinned framework immediately BEFORE its real RtlWriteSram.
// This eliminates the previous selector-change race where raw 8-KiB SRAM was
// written before the Modern CAS checked which profile still owned the slot.
// Successful preflight keeps the existing selector OS lock through the native
// write and the one typed post-save publication. No save or metadata mutation
// happens when selection/profile/catalog authority has been lost.
extern "C" int ur_baldosa_modern_profile_before_native_save(void) {
    if (!activated() || g_verified_native_profile_id.empty()) return 1;
    if (g_native_shutdown_selector_lock || g_native_shutdown_catalog_lock ||
        g_native_shutdown_profile_lock)
        return reject("save_lease_reentry");
    if (!g_launch_global || !g_launch_profile ||
        g_native_user_root.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes))
        return reject("save_preflight_missing_context");

    const auto profile_root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern, g_verified_native_profile_id);
    if (!profile_root.isolated())
        return reject("save_profile_root_invalid");
    if (!ur::product::baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, profile_root.save_root))
        return reject("save_profile_path_redirected_or_incomplete");
    auto candidate = std::make_unique<ur::product::TournamentLaunchPathLock>(
        (g_native_user_root / "host-state-v1.txt").string(), true);
    if (!candidate->acquired())
        return reject("save_selector_lock_unavailable");
    // The existing selector, catalog and profile CAS writers own distinct
    // persistent OS locks. Acquire nonblocking in canonical order and retain
    // all three until the raw SRAM write and typed publication have finished.
    auto catalog_candidate =
        std::make_unique<ur::product::TournamentLaunchPathLock>(
            (g_native_user_root / "profiles-v1.txt").string(), true);
    if (!catalog_candidate->acquired())
        return reject("save_catalog_lock_unavailable");
    const auto profile_path = g_native_user_root /
        profile_root.save_root / "host-profile.txt";
    auto profile_candidate =
        std::make_unique<ur::product::TournamentLaunchPathLock>(
            profile_path.string(), true);
    if (!profile_candidate->acquired())
        return reject("save_profile_lock_unavailable");
    if (!ur::product::baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, profile_root.save_root))
        return reject("save_profile_path_changed_under_lock");
    const ur::product::BaldosaSramCheckpoint request{
        g_native_user_root, *g_launch_global, *g_launch_profile,
        g_sram, static_cast<std::size_t>(g_sram_size)};
    if (const auto error =
            ur::product::baldosa_sram_checkpoint_preflight_under_lock(request)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=%u\n",
            static_cast<unsigned>(*error));
        std::fflush(stderr);
        return 0;
    }
    // The selected profile's raw 8-KiB disk image must still agree with its
    // launch-time typed baseline BEFORE the original RtlWriteSram overwrites
    // it. Neither an external raw writer nor a swapped symlink is trusted.
    // This is deliberately a pre-write check; post-write compares guest SRAM.
    const auto sram_path = g_native_user_root /
        profile_root.save_root / "save.srm";
    if (!ur::product::baldosa_sram_file_matches_exact(
            sram_path, g_launch_profile->stock_sram->data(),
            ur::product::kStockSramBytes))
        return reject("save_baseline_mismatch");
    g_native_shutdown_selector_lock = std::move(candidate);
    g_native_shutdown_catalog_lock = std::move(catalog_candidate);
    g_native_shutdown_profile_lock = std::move(profile_candidate);
    return 1;
}


// Invoked ONLY by the pinned native host immediately after a successful
// RtlWriteSram(), not from a frame, a guest result guess, or a destructor.
// The existing typed Modern CAS/selector lock remains the only publication
// authority. This cannot manufacture Records, a run, or a progression medal.
extern "C" int ur_baldosa_modern_profile_finish_native_save(int saved) {
    if (!activated() || g_verified_native_profile_id.empty()) return saved ? 1 : 0;
    // Release on EVERY path, including native write failure. This local RAII
    // owner holds the selector lease through the typed CAS below.
    auto selector_guard = std::move(g_native_shutdown_selector_lock);
    auto catalog_guard = std::move(g_native_shutdown_catalog_lock);
    auto profile_guard = std::move(g_native_shutdown_profile_lock);
    if (!selector_guard || !selector_guard->acquired() ||
        !catalog_guard || !catalog_guard->acquired() ||
        !profile_guard || !profile_guard->acquired()) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT status=missing_save_lease\n");
        return 0;
    }
    if (!saved) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE native_save_failed\n");
        return 0;
    }
    if (!g_launch_global || !g_launch_profile ||
        g_native_user_root.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT status=invalid_context\n");
        std::fflush(stderr);
        return 0;
    }
    const auto save_root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern, g_verified_native_profile_id);
    if (!save_root.isolated() ||
        !ur::product::baldosa_native_selected_profile_paths_are_real(
            g_native_user_root, save_root.save_root)) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT status=profile_path_redirected\n");
        return 0;
    }
    const ur::product::BaldosaSramCheckpoint request{
        g_native_user_root, *g_launch_global, *g_launch_profile,
        g_sram, static_cast<std::size_t>(g_sram_size)};
    const auto result = ur::product::checkpoint_baldosa_native_profile_sram_under_lock(
        request);
    const char* verdict = "rejected";
    switch (result) {
    case ur::product::BaldosaSramCheckpointStatus::Committed:
        verdict = "committed";
        break;
    case ur::product::BaldosaSramCheckpointStatus::Unchanged:
        verdict = "unchanged";
        break;
    case ur::product::BaldosaSramCheckpointStatus::InvalidContext:
        verdict = "invalid_context";
        break;
    case ur::product::BaldosaSramCheckpointStatus::SelectionConflict:
        verdict = "selection_conflict";
        break;
    case ur::product::BaldosaSramCheckpointStatus::UnauthorizedProfile:
        verdict = "unauthorized_profile";
        break;
    case ur::product::BaldosaSramCheckpointStatus::NativeSaveUnverified:
        verdict = "native_save_unverified";
        break;
    case ur::product::BaldosaSramCheckpointStatus::ProfileConflict:
        verdict = "profile_conflict";
        break;
    case ur::product::BaldosaSramCheckpointStatus::IoError:
        verdict = "io_error";
        break;
    }
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=%s status=%s\n",
        g_verified_native_profile_id.c_str(), verdict);
    std::fflush(stderr);
    return result == ur::product::BaldosaSramCheckpointStatus::Committed ||
           result == ur::product::BaldosaSramCheckpointStatus::Unchanged;
}

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
// Shutdown-scoped owners of the existing selector and profile OS locks.
// Never hold them across gameplay or reacquire them inside the typed CAS.
std::unique_ptr<ur::product::TournamentLaunchPathLock>
    g_native_shutdown_selector_lock;
std::unique_ptr<ur::product::TournamentLaunchPathLock>
    g_native_shutdown_profile_lock;

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
    if (!std::filesystem::is_regular_file(sram_path, ec) || ec ||
        std::filesystem::file_size(sram_path, ec) !=
            ur::product::kStockSramBytes || ec)
        return reject("selected_profile_sram_not_initialized");

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
    if (g_native_shutdown_selector_lock || g_native_shutdown_profile_lock)
        return reject("save_lease_reentry");
    if (!g_launch_global || !g_launch_profile ||
        g_native_user_root.empty() || !g_sram ||
        g_sram_size != static_cast<int>(ur::product::kStockSramBytes))
        return reject("save_preflight_missing_context");

    auto candidate = std::make_unique<ur::product::TournamentLaunchPathLock>(
        (g_native_user_root / "host-state-v1.txt").string(), true);
    if (!candidate->acquired())
        return reject("save_selector_lock_unavailable");
    // The ordinary typed CAS writer has a different per-profile OS lock.
    // Take it selector-first, then keep BOTH locks until the raw SRAM write
    // and typed metadata CAS have finished, so a second writer cannot change
    // profile bytes between preflight and raw publication.
    const auto profile_root = ur::product::resolve_host_profile_save_root(
        ur::product::ExecutionMode::Modern, g_verified_native_profile_id);
    if (!profile_root.isolated())
        return reject("save_profile_root_invalid");
    const auto profile_path = g_native_user_root /
        profile_root.save_root / "host-profile.txt";
    auto profile_candidate =
        std::make_unique<ur::product::TournamentLaunchPathLock>(
            profile_path.string(), true);
    if (!profile_candidate->acquired())
        return reject("save_profile_lock_unavailable");
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
    g_native_shutdown_selector_lock = std::move(candidate);
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
    auto profile_guard = std::move(g_native_shutdown_profile_lock);
    if (!selector_guard || !selector_guard->acquired() ||
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

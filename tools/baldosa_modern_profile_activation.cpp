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

#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>

extern "C" void RtlSetSaveRoot(const char*);
extern "C" const char* RtlSaveRoot(void);
extern "C" void RtlEnsureSaveDir(void);
extern "C" unsigned char* g_sram;
extern "C" int g_sram_size;

namespace {

std::string g_verified_native_profile_id;

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

    const char* override_path = std::getenv("UR_HOST_STATE_PATH");
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

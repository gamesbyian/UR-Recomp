#pragma once

// Typed Modern profile checkpoint for a native Baldosa session.
//
// This is deliberately an API for an acknowledged native *post-save*
// lifecycle boundary. It must never be called from a mere simulated frame,
// timer expiry, renderer, or a host-side invented event outcome. The native
// framework first persists the actual cartridge SRAM; only after that may
// the owning Modern host pass its exact guest bytes and original profile
// baseline here. We reuse the shipping product/profile/catalog codecs, the
// existing CAS store, and the existing per-selector OS lock. This helper is
// inert until a native lifecycle owner explicitly wires and admits that
// boundary. No new file format and no .urrun/.urghost/receipt production.

#include "host_product_store.hpp"
#include "host_profile_catalog.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_store.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <system_error>

namespace ur::product {

enum class BaldosaSramCheckpointStatus : std::uint8_t {
    Committed,
    Unchanged,
    InvalidContext,
    SelectionConflict,
    UnauthorizedProfile,
    NativeSaveUnverified,
    ProfileConflict,
    IoError,
};

struct BaldosaSramCheckpoint {
    // Validated existing Modern per-user root, never executable/package root.
    std::filesystem::path user_root;
    // Exact selection/profile snapshots captured when the native session
    // began. Re-read and compare them; do not accept a later selector change.
    HostProductState expected_global;
    HostProfileState expected_profile;
    // Actual guest 8192 bytes AFTER framework RtlWriteSram; still compare
    // all bytes with its on-disk native save before touching typed metadata.
    const std::uint8_t* guest_sram = nullptr;
    std::size_t guest_sram_size = 0;
};

inline bool baldosa_sram_file_matches_exact(
    const std::filesystem::path& path,
    const std::uint8_t* expected, std::size_t expected_size) {
    if (!expected || expected_size != kStockSramBytes) return false;
    std::error_code ec;
    if (std::filesystem::is_symlink(path, ec) || ec ||
        !std::filesystem::is_regular_file(path, ec) || ec ||
        std::filesystem::file_size(path, ec) != kStockSramBytes || ec)
        return false;
    std::ifstream file(path, std::ios::binary);
    if (!file) return false;
    std::array<std::uint8_t, kStockSramBytes> bytes{};
    file.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
    return file.gcount() == static_cast<std::streamsize>(bytes.size()) &&
           !file.bad() &&
           std::equal(bytes.begin(), bytes.end(), expected);
}

// Check original selected-profile authority. Caller MUST hold the existing
// selector, roster and profile OS locks, in that order, before this preflight.
// These three typed authorities cannot change before raw SRAM publication.
inline bool baldosa_sram_checkpoint_request_valid(
    const BaldosaSramCheckpoint& request) {
    const auto& id = request.expected_profile.profile_id;
    return request.user_root.is_absolute() &&
        is_safe_profile_storage_id(id) &&
        request.expected_global.active_profile_id &&
        *request.expected_global.active_profile_id == id &&
        request.expected_profile.stock_sram &&
        request.expected_profile.racer_identity &&
        request.guest_sram &&
        request.guest_sram_size == kStockSramBytes;
}

inline std::optional<BaldosaSramCheckpointStatus>
baldosa_sram_checkpoint_preflight_under_lock(
    const BaldosaSramCheckpoint& request) {
    namespace fs = std::filesystem;
    if (!baldosa_sram_checkpoint_request_valid(request))
        return BaldosaSramCheckpointStatus::InvalidContext;
    const auto& id = request.expected_profile.profile_id;
    const auto decision = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::optional<std::string>(id));
    if (!decision.isolated())
        return BaldosaSramCheckpointStatus::InvalidContext;
    const fs::path global_path = request.user_root / "host-state-v1.txt";
    const fs::path catalog_path = request.user_root / "profiles-v1.txt";
    const fs::path profile_path =
        request.user_root / decision.save_root / "host-profile.txt";
    const auto global = load_host_product_state_file(global_path.string());
    if (!global.loaded() || !(*global.state == request.expected_global))
        return BaldosaSramCheckpointStatus::SelectionConflict;
    const auto catalog = load_host_profile_catalog_file(catalog_path.string());
    if (!catalog ||
        !profile_catalog_authorizes_state(*catalog, request.expected_profile))
        return BaldosaSramCheckpointStatus::UnauthorizedProfile;
    const auto state = load_host_profile_state_file(
        ExecutionMode::Modern, profile_path.string(), id);
    if (!state.loaded() || !(*state.state == request.expected_profile))
        return BaldosaSramCheckpointStatus::ProfileConflict;
    return std::nullopt;
}

// Native host holds all three canonical OS locks, selector then roster then
// profile, from before the cartridge write through typed publication.
// Never recursively acquire a held lock here.
inline BaldosaSramCheckpointStatus checkpoint_baldosa_native_profile_sram_under_lock(
    const BaldosaSramCheckpoint& request) {
    namespace fs = std::filesystem;
    if (const auto failure =
            baldosa_sram_checkpoint_preflight_under_lock(request))
        return *failure;
    const auto& id = request.expected_profile.profile_id;
    const auto decision = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::optional<std::string>(id));
    const fs::path profile_root = request.user_root / decision.save_root;
    const fs::path profile_path = profile_root / "host-profile.txt";
    const fs::path native_sram_path = profile_root / "save.srm";
    // Framework save acknowledgment is NOT inferred from a filename, from
    // a zero return code, or from a guest timer. Every one of the persisted
    // 8192 guest-written bytes must match the actual SRAM passed by native
    // ownership. Never overwrite the raw save here or fabricate progress.
    if (!baldosa_sram_file_matches_exact(
            native_sram_path, request.guest_sram, request.guest_sram_size))
        return BaldosaSramCheckpointStatus::NativeSaveUnverified;

    if (std::equal(request.expected_profile.stock_sram->begin(),
                   request.expected_profile.stock_sram->end(),
                   request.guest_sram))
        return BaldosaSramCheckpointStatus::Unchanged;

    auto updated = request.expected_profile;
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, updated,
            request.guest_sram, request.guest_sram_size) !=
        HostProfileTransferStatus::Applied)
        return BaldosaSramCheckpointStatus::InvalidContext;

    const auto outcome = save_host_profile_state_file_if_current_under_lock(
        ExecutionMode::Modern, profile_path.string(),
        request.expected_profile, updated);
    if (outcome == HostProfileSaveStatus::Saved)
        return BaldosaSramCheckpointStatus::Committed;
    return outcome == HostProfileSaveStatus::Conflict
        ? BaldosaSramCheckpointStatus::ProfileConflict
        : BaldosaSramCheckpointStatus::IoError;
}

// Existing standalone post-save callers use the same validated path, with
// this wrapper acquiring its own interprocess selector lock.
inline BaldosaSramCheckpointStatus checkpoint_baldosa_native_profile_sram(
    const BaldosaSramCheckpoint& request) {
    if (!baldosa_sram_checkpoint_request_valid(request))
        return BaldosaSramCheckpointStatus::InvalidContext;
    const std::filesystem::path global_path =
        request.user_root / "host-state-v1.txt";
    TournamentLaunchPathLock global_lock(global_path.string(), true);
    if (!global_lock.acquired())
        return BaldosaSramCheckpointStatus::IoError;
    const auto decision = resolve_host_profile_save_root(
        ExecutionMode::Modern,
        std::optional<std::string>(request.expected_profile.profile_id));
    if (!decision.isolated())
        return BaldosaSramCheckpointStatus::InvalidContext;
    const std::filesystem::path profile_path =
        request.user_root / decision.save_root / "host-profile.txt";
    const std::filesystem::path catalog_path =
        request.user_root / "profiles-v1.txt";
    TournamentLaunchPathLock catalog_lock(catalog_path.string(), true);
    if (!catalog_lock.acquired())
        return BaldosaSramCheckpointStatus::IoError;
    TournamentLaunchPathLock profile_lock(profile_path.string(), true);
    if (!profile_lock.acquired())
        return BaldosaSramCheckpointStatus::IoError;
    return checkpoint_baldosa_native_profile_sram_under_lock(request);
}

}  // namespace ur::product

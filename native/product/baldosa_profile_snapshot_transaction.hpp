#pragma once

// Candidate Modern profile snapshot transaction for a *future acknowledged*
// Baldosa session boundary. This is deliberately NOT hooked to a guest frame,
// shutdown or event inference. All existing Modern codecs and CAS stores are
// authoritative. An acknowledged, frozen native guest and actual RtlTryWriteSram
// adapter are prerequisites; see issue #1125.
//
// This protects common stale-selector, stale-profile, guest write failure and
// concurrent overwrite cases. It is NOT power-loss atomic across the SRAM and
// typed profile files. Do not claim full fresh-process recovery on this helper.

#include "host_product_store.hpp"
#include "host_profile_catalog.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_store.hpp"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <utility>

namespace ur::product {

enum class BaldosaProfileCommitStatus {
    Saved,
    Unchanged,
    Rejected,
    SelectorChanged,
    ProfileChanged,
    MetadataWriteFailed,
    NativeSramWriteFailed,
    RollbackConflict,
};

// This callback MUST only write the exact 8192 guest bytes supplied at a
// native host-acknowledged stable boundary to its already selected save root.
// In particular, it must not silently redirect to anonymous "saves/".
using BaldosaNativeSramWriter = bool (*)(void* context);

struct BaldosaProfileCommitRequest {
    std::filesystem::path user_root;
    std::string boot_profile_id;
    HostProductState expected_selector;
    HostProfileState expected_profile;
    const std::uint8_t* frozen_guest_sram = nullptr;
    std::size_t frozen_guest_sram_size = 0;
    bool native_checkpoint_acknowledged = false;
    BaldosaNativeSramWriter write_native_sram = nullptr;
    void* write_context = nullptr;
};

inline BaldosaProfileCommitStatus commit_baldosa_profile_snapshot(
    const BaldosaProfileCommitRequest& request) {
    namespace fs = std::filesystem;
    std::error_code ec;
    if (!request.native_checkpoint_acknowledged ||
        !request.write_native_sram ||
        !request.frozen_guest_sram ||
        request.frozen_guest_sram_size != kStockSramBytes ||
        !request.user_root.is_absolute() ||
        !fs::is_directory(request.user_root, ec) || ec ||
        !is_valid_profile_id(request.boot_profile_id) ||
        request.expected_profile.profile_id != request.boot_profile_id ||
        !request.expected_profile.stock_sram ||
        !request.expected_selector.active_profile_id ||
        *request.expected_selector.active_profile_id !=
            request.boot_profile_id)
        return BaldosaProfileCommitStatus::Rejected;

    const auto selector_path = (request.user_root / "host-state-v1.txt").string();
    const auto global = load_host_product_state_file(selector_path);
    if (!global.loaded() || !(*global.state == request.expected_selector))
        return BaldosaProfileCommitStatus::SelectorChanged;

    const auto roster = load_host_profile_catalog_file(
        (request.user_root / "profiles-v1.txt").string());
    if (!roster ||
        !profile_catalog_authorizes_state(*roster, request.expected_profile))
        return BaldosaProfileCommitStatus::Rejected;

    const auto save_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, request.boot_profile_id);
    if (!save_root.isolated()) return BaldosaProfileCommitStatus::Rejected;
    const auto state_path =
        (request.user_root / save_root.save_root / "host-profile.txt").string();
    const auto current = load_host_profile_state_file(
        ExecutionMode::Modern, state_path, request.boot_profile_id);
    if (!current.loaded() || !(*current.state == request.expected_profile))
        return BaldosaProfileCommitStatus::ProfileChanged;

    HostProfileState candidate = request.expected_profile;
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, candidate, request.frozen_guest_sram,
            request.frozen_guest_sram_size) !=
        HostProfileTransferStatus::Applied)
        return BaldosaProfileCommitStatus::Rejected;

    // A genuinely unchanged image has no profile generation or native write
    // obligation. The previous native save remains authoritative on disk.
    if (candidate.stock_sram == request.expected_profile.stock_sram)
        return BaldosaProfileCommitStatus::Unchanged;

    // Never write the global active-profile selector or another rider's path.
    // Our CAS prevents losing a concurrent metadata update. A later native
    // SRAM write failure may roll back only this exact intermediate value.
    const auto saved = save_host_profile_state_file_if_current(
        ExecutionMode::Modern, state_path, request.expected_profile, candidate);
    if (saved == HostProfileSaveStatus::Conflict)
        return BaldosaProfileCommitStatus::ProfileChanged;
    if (saved != HostProfileSaveStatus::Saved)
        return BaldosaProfileCommitStatus::MetadataWriteFailed;

    if (!request.write_native_sram(request.write_context)) {
        const auto reverted = save_host_profile_state_file_if_current(
            ExecutionMode::Modern, state_path, candidate,
            request.expected_profile);
        return reverted == HostProfileSaveStatus::Saved
            ? BaldosaProfileCommitStatus::NativeSramWriteFailed
            : BaldosaProfileCommitStatus::RollbackConflict;
    }
    return BaldosaProfileCommitStatus::Saved;
}

}  // namespace ur::product

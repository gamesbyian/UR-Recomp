#pragma once

// Select an EXISTING Modern named racer only for the NEXT native process.
// No changes to the live guest, SRAM, profile files, Records or catalog.
// The caller must require an explicit user action and enforce an exit/restart
// barrier before this new selector is usable. This is backend policy, NOT a
// player-facing switch or physical controller acceptance.
//
// Use exactly the already-shipping typed catalog/global/profile codecs and
// persistent OS-handle path locks. Never discover profiles from directories.
#include "baldosa_native_first_profile.hpp"

#include <algorithm>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

enum class BaldosaExistingProfileSelectionStatus {
    SelectedForNextBoot,
    AlreadySelected,
    InvalidRequest,
    RejectedAuthority,
    BusyOrIoError,
};

struct BaldosaExistingProfileSelectionResult {
    BaldosaExistingProfileSelectionStatus status =
        BaldosaExistingProfileSelectionStatus::InvalidRequest;
    std::string next_profile_id;

    bool selected() const noexcept {
        return status ==
            BaldosaExistingProfileSelectionStatus::SelectedForNextBoot;
    }
};

// Emergency selector admission: a crashed currently selected source may
// have missing/corrupt typed or raw bytes. Never read them as authoritative,
// but refuse redirected paths and require canonical real directories. The
// destination is independently validated using the full ordinary policy.
inline bool baldosa_native_damaged_source_paths_are_safe(
    const std::filesystem::path& root,
    const std::filesystem::path& save_root) {
    namespace fs = std::filesystem;
    if (!baldosa_native_real_directory(root / "saves") ||
        !baldosa_native_real_directory(root / save_root))
        return false;
    for (const auto* name : {"host-profile.txt", "save.srm"}) {
        std::error_code ec;
        const auto st = fs::symlink_status(root / save_root / name, ec);
        if (st.type() == fs::file_type::not_found &&
            (!ec || ec == std::errc::no_such_file_or_directory))
            continue;
        if (ec || !fs::is_regular_file(st) || fs::is_symlink(st))
            return false;
    }
    return true;
}

inline BaldosaExistingProfileSelectionResult
select_baldosa_existing_profile_for_next_boot(
    const std::filesystem::path& user_root,
    std::string_view expected_active_profile,
    std::string_view requested_profile,
    bool allow_damaged_current = false,
    bool validate_only = false) {
    namespace fs = std::filesystem;
    using Status = BaldosaExistingProfileSelectionStatus;

    // Refuse path traversal, anonymous selection, or an implicit profile
    // directory scan. The only two filesystem owners inspected/locked are
    // the explicitly named source and destination. A third unrelated racer
    // (even with damaged SRAM) may not strand the requested healthy one.
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !is_safe_profile_storage_id(expected_active_profile) ||
        !is_safe_profile_storage_id(requested_profile) ||
        expected_active_profile == requested_profile)
        return {Status::InvalidRequest, {}};

    const fs::path selector = user_root / "host-state-v1.txt";
    const fs::path catalog = user_root / "profiles-v1.txt";
    if (!baldosa_native_real_file(selector) ||
        !baldosa_native_real_file(catalog) ||
        !baldosa_native_real_directory(user_root / "saves"))
        return {Status::RejectedAuthority, {}};

    // Existing native checkpoint order: selector -> catalog -> typed state.
    // Holding BOTH typed locks prevents one source checkpoint from changing
    // either owner between authorization and selector publication. Order
    // their two canonical path strings to avoid cross-selection deadlocks.
    TournamentLaunchPathLock selector_lock(selector.string(), true);
    if (!selector_lock.acquired())
        return {Status::BusyOrIoError, {}};
    TournamentLaunchPathLock catalog_lock(catalog.string(), true);
    if (!catalog_lock.acquired())
        return {Status::BusyOrIoError, {}};

    const auto global = load_host_product_state_file(selector.string());
    const auto roster = load_host_profile_catalog_file(catalog.string());
    if (!global.loaded() || !global.state->active_profile_id ||
        *global.state->active_profile_id != expected_active_profile ||
        !roster || roster->size() < 2u)
        return {Status::RejectedAuthority, {}};

    // Canonical catalog decoding already rejects invalid or colliding IDs
    // across ALL entries. Under the catalog lock select only the requested
    // two entries; unrelated profiles are neither read nor locked.
    std::vector<const HostProfileCatalogEntry*> selected;
    selected.reserve(2);
    std::vector<fs::path> typed_paths;
    typed_paths.reserve(2);
    bool found_source = false, found_destination = false;
    for (const auto& entry : *roster) {
        if (entry.profile_id != expected_active_profile &&
            entry.profile_id != requested_profile)
            continue;
        if (!is_safe_profile_storage_id(entry.profile_id) ||
            !valid_racer_identity(entry.identity))
            return {Status::RejectedAuthority, {}};
        const auto location = resolve_host_profile_save_root(
            ExecutionMode::Modern, entry.profile_id);
        if (!location.isolated() ||
            !(allow_damaged_current &&
              entry.profile_id == expected_active_profile
                  ? baldosa_native_damaged_source_paths_are_safe(
                        user_root, location.save_root)
                  : baldosa_native_selected_profile_paths_are_real(
                        user_root, location.save_root)))
            return {Status::RejectedAuthority, {}};
        typed_paths.push_back(
            user_root / location.save_root / "host-profile.txt");
        selected.push_back(&entry);
        found_source |= entry.profile_id == expected_active_profile;
        found_destination |= entry.profile_id == requested_profile;
    }
    if (!found_source || !found_destination || selected.size() != 2u)
        return {Status::RejectedAuthority, {}};

    std::sort(typed_paths.begin(), typed_paths.end());
    if (typed_paths[0] == typed_paths[1])
        return {Status::RejectedAuthority, {}};
    TournamentLaunchPathLock first_lock(typed_paths[0].string(), true);
    if (!first_lock.acquired())
        return {Status::BusyOrIoError, {}};
    TournamentLaunchPathLock second_lock(typed_paths[1].string(), true);
    if (!second_lock.acquired())
        return {Status::BusyOrIoError, {}};

    // Repeat all admissibility checks *under* every lock, including the
    // selected global state. A catalog row alone never authenticates SRAM.
    if (!baldosa_native_real_file(selector) ||
        !baldosa_native_real_file(catalog))
        return {Status::RejectedAuthority, {}};
    const auto again = load_host_product_state_file(selector.string());
    const auto current_roster =
        load_host_profile_catalog_file(catalog.string());
    if (!again.loaded() || !again.state->active_profile_id ||
        *again.state->active_profile_id != expected_active_profile ||
        !current_roster || *current_roster != *roster)
        return {Status::RejectedAuthority, {}};

    for (const auto* chosen : selected) {
        const auto& entry = *chosen;
        const auto location = resolve_host_profile_save_root(
            ExecutionMode::Modern, entry.profile_id);
        if (!location.isolated() ||
            !(allow_damaged_current &&
              entry.profile_id == expected_active_profile
                  ? baldosa_native_damaged_source_paths_are_safe(
                        user_root, location.save_root)
                  : baldosa_native_selected_profile_paths_are_real(
                        user_root, location.save_root)))
            return {Status::RejectedAuthority, {}};
        // No bytes from the crashed source authorize destination activation.
        if (allow_damaged_current &&
            entry.profile_id == expected_active_profile)
            continue;
        const auto profile = load_host_profile_state_file(
            ExecutionMode::Modern,
            (user_root / location.save_root / "host-profile.txt").string(),
            entry.profile_id);
        if (!profile.loaded() || !profile.state->stock_sram ||
            !catalog_entry_matches_profile_state(entry, *profile.state) ||
            !stock_sram_format_signature_present(
                profile.state->stock_sram->data(),
                profile.state->stock_sram->size()) ||
            !baldosa_sram_file_matches_exact(
                user_root / location.save_root / "save.srm",
                profile.state->stock_sram->data(), kStockSramBytes))
            return {Status::RejectedAuthority, {}};
    }

    // The caller owns selector lock; save_if_current would acquire that same
    // lock twice and can self-deadlock. Use the established atomic staged
    // store only AFTER the exact locked previous state has been rechecked.
    auto next = *again.state;
    next.active_profile_id = std::string(requested_profile);
    // The live original guest still owns the old SRAM at controller X/A.
    // Frontend approval is a validated, in-memory next-boot REQUEST only.
    // The actual source raw + typed shutdown checkpoint must complete
    // BEFORE this authoritative selector may be changed.
    if (validate_only)
        return {Status::SelectedForNextBoot, std::string(requested_profile)};
    if (save_host_product_state_file(selector.string(), next) !=
        HostProductSaveStatus::Saved)
        return {Status::BusyOrIoError, {}};
    return {Status::SelectedForNextBoot, std::string(requested_profile)};
}

// Explicit emergency action, never used by ordinary controller selection.
// Requires a separately confirmed target ID and leaves both snapshots of
// the crashed current racer untouched, even if its typed sidecar is missing.
// Caller must restart the native process before playing the new selection.
inline BaldosaExistingProfileSelectionResult
select_baldosa_healthy_profile_from_damaged_for_next_boot(
    const std::filesystem::path& user_root,
    std::string_view expected_active_profile,
    std::string_view requested_profile) {
    return select_baldosa_existing_profile_for_next_boot(
        user_root, expected_active_profile, requested_profile, true);
}

}  // namespace ur::product

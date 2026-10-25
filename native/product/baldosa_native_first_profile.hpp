#pragma once

// First-run Baldosa Modern preset creation. No new profile formats or guest
// SRAM edits: the exact existing Modern codecs and canonical stock clean SRAM
// prepare the NEXT native process. A just-created profile must never become
// active in the already-running anonymous guest.
//
// Only an explicitly empty Modern selector/catalog may be initialized here;
// general profile creation, rename, reset and live switching remain owned by
// the established full Modern product host.
#include "baldosa_native_profile_path_guard.hpp"
#include "baldosa_native_profile_sram_checkpoint.hpp"
#include "clean_stock_sram.hpp"
#include "host_product_store.hpp"
#include "host_profile_catalog.hpp"
#include "host_profile_runtime.hpp"
#include "host_profile_store.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <system_error>
#include <vector>

namespace ur::product {

enum class BaldosaFirstRacerStatus {
    Created,
    Invalid,
    AlreadyConfigured,
    ExistingData,
    IoError,
    Recovered,  // an already durable catalog/typed/raw triplet now selected
};

struct BaldosaFirstRacerResult {
    BaldosaFirstRacerStatus status = BaldosaFirstRacerStatus::Invalid;
    std::string profile_id;

    bool created() const noexcept {
        return status == BaldosaFirstRacerStatus::Created ||
               status == BaldosaFirstRacerStatus::Recovered;
    }
};

inline bool baldosa_first_profile_entry_absent(
    const std::filesystem::path& pathname) {
    std::error_code ec;
    const auto st = std::filesystem::symlink_status(pathname, ec);
    return st.type() == std::filesystem::file_type::not_found &&
           (!ec || ec == std::errc::no_such_file_or_directory);
}

inline BaldosaFirstRacerResult create_baldosa_first_preset_for_next_boot(
    const std::filesystem::path& user_root, std::size_t preset_index) {
    namespace fs = std::filesystem;
    // Never make a profile under CWD, a relative override, or a redirected
    // user root. The launcher itself owns the per-user path policy.
    const auto preset = make_legacy_racer_identity(preset_index);
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !preset || !valid_racer_identity(*preset))
        return {BaldosaFirstRacerStatus::Invalid, {}};

    const fs::path global = user_root / "host-state-v1.txt";
    const fs::path catalog = user_root / "profiles-v1.txt";
    const auto existing = load_host_product_state_file(global.u8string());
    // load_host_product_state_file reports a dangling symlink as missing
    // on some hosts. Creation must never follow or repair such a selector.
    if (existing.status != HostProductLoadStatus::Missing ||
        !baldosa_first_profile_entry_absent(global))
        return {BaldosaFirstRacerStatus::AlreadyConfigured, {}};
    if (!baldosa_first_profile_entry_absent(catalog))
        return {BaldosaFirstRacerStatus::ExistingData, {}};

    const std::string id = make_profile_id(preset->name, {});
    const auto target = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::optional<std::string>{id});
    if (!target.isolated()) return {BaldosaFirstRacerStatus::Invalid, {}};
    const fs::path saves = user_root / "saves";
    const fs::path profile_dir = user_root / target.save_root;
    if (baldosa_first_profile_entry_absent(saves)) {
        std::error_code ec;
        if (!fs::create_directory(saves, ec) || ec)
            return {BaldosaFirstRacerStatus::IoError, {}};
    }
    if (!baldosa_native_real_directory(saves) ||
        !baldosa_first_profile_entry_absent(profile_dir))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    std::error_code ec;
    if (!fs::create_directory(profile_dir, ec) || ec)
        return {BaldosaFirstRacerStatus::IoError, {}};

    auto state = make_default_host_profile_state(id);
    if (!state) return {BaldosaFirstRacerStatus::Invalid, {}};
    state->racer_identity = *preset;
    // The established Modern host projects a selected stock rider to
    // clean profile SRAM offset 0x0748. A non-default first-time preset
    // MUST boot with its own rider selection, not Mike's stock default.
    // Modify only a private copy for this new identity: the canonical
    // embedded clean source is immutable and other profiles are untouched.
    auto source = clean_stock_sram();
    source[0x0748] = preset->rider_index;
    if (!stock_sram_format_signature_present(source.data(), source.size()) ||
        capture_stock_sram_for_profile(
            ExecutionMode::Modern, *state,
            source.data(), source.size()) != HostProfileTransferStatus::Applied)
        return {BaldosaFirstRacerStatus::Invalid, {}};

    const fs::path typed = profile_dir / "host-profile.txt";
    if (save_host_profile_state_file_if_current(
            ExecutionMode::Modern, typed.u8string(), std::nullopt, *state) !=
        HostProfileSaveStatus::Saved)
        return {BaldosaFirstRacerStatus::IoError, {}};
    // Only create a previously absent raw file. No 'repair' or automatic
    // replacement of another process's SRAM is ever attempted here.
    const fs::path raw = profile_dir / "save.srm";
    if (!baldosa_first_profile_entry_absent(raw))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    {
        std::ofstream out(raw, std::ios::binary | std::ios::out);
        if (!out.write(
                reinterpret_cast<const char*>(source.data()),
                static_cast<std::streamsize>(source.size())) || !out.flush())
            return {BaldosaFirstRacerStatus::IoError, {}};
    }
    if (!baldosa_native_selected_profile_paths_are_real(
            user_root, target.save_root) ||
        !baldosa_sram_file_matches_exact(raw, source.data(), source.size()))
        return {BaldosaFirstRacerStatus::IoError, {}};

    // The catalog is the penultimate publication. Hold its existing
    // OS-handle lock while checking CREATE ONLY. The global active selector
    // is the final CAS publication; process death earlier leaves no active
    // racer and therefore cannot make the next boot adopt partial data.
    {
        TournamentLaunchPathLock catalog_lock(catalog, true);
        if (!catalog_lock.acquired())
            return {BaldosaFirstRacerStatus::IoError, {}};
        if (!baldosa_first_profile_entry_absent(catalog) ||
            load_host_product_state_file(global.u8string()).status !=
                HostProductLoadStatus::Missing)
            return {BaldosaFirstRacerStatus::AlreadyConfigured, {}};
        if (!save_host_profile_catalog_file(
                catalog.u8string(), {{id, *preset}}))
            return {BaldosaFirstRacerStatus::IoError, {}};
    }
    HostProductState selected{};
    selected.active_profile_id = id;
    if (save_host_product_state_file_if_current(
            global.u8string(), std::nullopt, selected) !=
        HostProductSaveStatus::Saved)
        return {BaldosaFirstRacerStatus::IoError, {}};
    return {BaldosaFirstRacerStatus::Created, id};
}


// Explicit recovery of precisely ONE already-published, well-formed first
// racer whose active selector was never committed. This is NOT a general
// orphan-directory scanner or an automatic profile adoption mechanism.
// A user must choose the exact original preset from the native root before
// this function can restore only the missing global selector. Never delete,
// overwrite, or silently manufacture a profile/catalog/raw SRAM pair.
inline BaldosaFirstRacerResult recover_baldosa_first_preset_for_next_boot(
    const std::filesystem::path& user_root, std::size_t preset_index) {
    namespace fs = std::filesystem;
    const auto expected = make_legacy_racer_identity(preset_index);
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !expected || !valid_racer_identity(*expected))
        return {BaldosaFirstRacerStatus::Invalid, {}};
    const fs::path global = user_root / "host-state-v1.txt";
    const fs::path catalog_path = user_root / "profiles-v1.txt";
    // Incomplete or malformed profile data must remain intact for manual
    // diagnosis. A symlink, existing selector or absent catalog may not
    // become a different active player after a crash.
    if (!baldosa_first_profile_entry_absent(global))
        return {BaldosaFirstRacerStatus::AlreadyConfigured, {}};
    if (!baldosa_native_real_file(catalog_path))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    const auto roster = load_host_profile_catalog_file(catalog_path.u8string());
    if (!roster || roster->size() != 1u ||
        !(roster->front().identity == *expected) ||
        !is_safe_profile_storage_id(roster->front().profile_id))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    const auto& id = roster->front().profile_id;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, id);
    if (!location.isolated() ||
        !baldosa_native_selected_profile_paths_are_real(
            user_root, location.save_root))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    const auto typed = user_root / location.save_root / "host-profile.txt";

    // The same canonical lock order as the existing native guest shutdown:
    // selector -> catalog -> typed profile. Nonblocking failure leaves all
    // bytes untouched so another process remains the sole authority.
    TournamentLaunchPathLock selector_lock(global, true);
    if (!selector_lock.acquired())
        return {BaldosaFirstRacerStatus::IoError, {}};
    TournamentLaunchPathLock catalog_lock(catalog_path, true);
    if (!catalog_lock.acquired())
        return {BaldosaFirstRacerStatus::IoError, {}};
    TournamentLaunchPathLock typed_lock(typed, true);
    if (!typed_lock.acquired())
        return {BaldosaFirstRacerStatus::IoError, {}};
    if (!baldosa_first_profile_entry_absent(global) ||
        load_host_product_state_file(global.u8string()).status !=
            HostProductLoadStatus::Missing ||
        !baldosa_native_real_file(catalog_path) ||
        !baldosa_native_selected_profile_paths_are_real(
            user_root, location.save_root))
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    const auto reread = load_host_profile_catalog_file(
        catalog_path.u8string());
    if (!reread || *reread != *roster)
        return {BaldosaFirstRacerStatus::ExistingData, {}};
    const auto profile = load_host_profile_state_file(
        ExecutionMode::Modern, typed.u8string(), id);
    if (!profile.loaded() || !profile.state->stock_sram ||
        !catalog_entry_matches_profile_state(
            roster->front(), *profile.state) ||
        !baldosa_sram_file_matches_exact(
            user_root / location.save_root / "save.srm",
            profile.state->stock_sram->data(), kStockSramBytes))
        return {BaldosaFirstRacerStatus::ExistingData, {}};

    HostProductState selected{};
    selected.active_profile_id = id;
    // The external selector lock plus repeated absence check are the same
    // create-only CAS critical section used by the standard product store.
    // Call its staged-write primitive directly: save_if_current() acquires
    // this SAME selector lock internally and would self-deadlock here.
    // Typed/catalog/raw content is immutable throughout this publication.
    if (save_host_product_state_file(global.u8string(), selected) !=
        HostProductSaveStatus::Saved)
        return {BaldosaFirstRacerStatus::IoError, {}};
    return {BaldosaFirstRacerStatus::Recovered, id};
}

}  // namespace ur::product

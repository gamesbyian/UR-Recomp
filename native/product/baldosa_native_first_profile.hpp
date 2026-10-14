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
};

struct BaldosaFirstRacerResult {
    BaldosaFirstRacerStatus status = BaldosaFirstRacerStatus::Invalid;
    std::string profile_id;

    bool created() const noexcept {
        return status == BaldosaFirstRacerStatus::Created;
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
    const auto existing = load_host_product_state_file(global.string());
    if (existing.status != HostProductLoadStatus::Missing)
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
    const auto& source = clean_stock_sram();
    if (!stock_sram_format_signature_present(source.data(), source.size()) ||
        capture_stock_sram_for_profile(
            ExecutionMode::Modern, *state,
            source.data(), source.size()) != HostProfileTransferStatus::Applied)
        return {BaldosaFirstRacerStatus::Invalid, {}};

    const fs::path typed = profile_dir / "host-profile.txt";
    if (save_host_profile_state_file_if_current(
            ExecutionMode::Modern, typed.string(), std::nullopt, *state) !=
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
        TournamentLaunchPathLock catalog_lock(catalog.string(), true);
        if (!catalog_lock.acquired())
            return {BaldosaFirstRacerStatus::IoError, {}};
        if (!baldosa_first_profile_entry_absent(catalog) ||
            load_host_product_state_file(global.string()).status !=
                HostProductLoadStatus::Missing)
            return {BaldosaFirstRacerStatus::AlreadyConfigured, {}};
        if (!save_host_profile_catalog_file(
                catalog.string(), {{id, *preset}}))
            return {BaldosaFirstRacerStatus::IoError, {}};
    }
    HostProductState selected{};
    selected.active_profile_id = id;
    if (save_host_product_state_file_if_current(
            global.string(), std::nullopt, selected) !=
        HostProductSaveStatus::Saved)
        return {BaldosaFirstRacerStatus::IoError, {}};
    return {BaldosaFirstRacerStatus::Created, id};
}

}  // namespace ur::product

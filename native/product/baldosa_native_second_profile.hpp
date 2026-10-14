#pragma once

// Bounded *second* named stock racer for a P1-owned Modern installation.
// The same typed profile, canonical 8 KiB source SRAM, catalog, and OS
// lock/atomic-staged writers as first-racer setup are the ONLY authorities.
// An additional P2 profile is NOT a live cartridge switch or a new frontend
// and must not alter the active P1 selector or original SRAM.
//
// This minimal backend admits exactly a one-entry verified roster and adds
// one genuinely different stock preset. Later multi-racer editing requires
// a separately reviewed transaction; never infer ownership from orphans.

#include "baldosa_native_first_profile.hpp"

#include <string_view>

namespace ur::product {

enum class BaldosaSecondRacerStatus {
    Created,
    Invalid,
    ExistingData,
    BusyOrIoError,
    Recovered, // exact staged typed/raw P2 committed; catalog publication resumed
};

struct BaldosaSecondRacerResult {
    BaldosaSecondRacerStatus status = BaldosaSecondRacerStatus::Invalid;
    std::string profile_id;

    bool created() const noexcept {
        return status == BaldosaSecondRacerStatus::Created ||
               status == BaldosaSecondRacerStatus::Recovered;
    }
};

inline BaldosaSecondRacerResult create_baldosa_second_preset_for_next_boot(
    const std::filesystem::path& user_root,
    std::string_view expected_active_profile,
    std::size_t preset_index) {
    namespace fs = std::filesystem;
    const auto proposed = make_legacy_racer_identity(preset_index);
    if (!proposed || !valid_racer_identity(*proposed) ||
        !is_safe_profile_storage_id(expected_active_profile) ||
        !user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root))
        return {BaldosaSecondRacerStatus::Invalid, {}};

    const fs::path global_path = user_root / "host-state-v1.txt";
    const fs::path catalog_path = user_root / "profiles-v1.txt";
    const fs::path saves_path = user_root / "saves";
    if (!baldosa_native_real_file(global_path) ||
        !baldosa_native_real_file(catalog_path) ||
        !baldosa_native_real_directory(saves_path))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    // Publication lock order is shared with native checkpoint and the
    // first-racer recovery: global -> catalog -> current typed profile.
    // External profile creation may not race another P1 selection or source
    // checkpoint. Never nest the locking CAS store below these leases.
    TournamentLaunchPathLock global_lock(global_path.string(), true);
    if (!global_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    TournamentLaunchPathLock catalog_lock(catalog_path.string(), true);
    if (!catalog_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    const auto selected =
        load_host_product_state_file(global_path.string());
    const auto roster =
        load_host_profile_catalog_file(catalog_path.string());
    if (!selected.loaded() || !selected.state->active_profile_id ||
        *selected.state->active_profile_id != expected_active_profile ||
        !roster || roster->size() != 1u ||
        roster->front().profile_id != expected_active_profile ||
        !is_safe_profile_storage_id(roster->front().profile_id) ||
        !valid_racer_identity(roster->front().identity) ||
        roster->front().identity == *proposed)
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    const auto active_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(expected_active_profile));
    if (!active_root.isolated() ||
        !baldosa_native_selected_profile_paths_are_real(
            user_root, active_root.save_root))
        return {BaldosaSecondRacerStatus::ExistingData, {}};
    const fs::path active_typed =
        user_root / active_root.save_root / "host-profile.txt";
    TournamentLaunchPathLock active_lock(active_typed.string(), true);
    if (!active_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    // A catalog row is NOT authentication by itself. Verify complete typed
    // ownership and exact matching raw SRAM before permitting another name
    // to be published in this P1 user's catalog.
    const auto active = load_host_profile_state_file(
        ExecutionMode::Modern, active_typed.string(),
        std::string(expected_active_profile));
    if (!active.loaded() || !active.state->stock_sram ||
        !catalog_entry_matches_profile_state(roster->front(), *active.state) ||
        !baldosa_sram_file_matches_exact(
            user_root / active_root.save_root / "save.srm",
            active.state->stock_sram->data(), kStockSramBytes))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    const std::string id = make_profile_id(proposed->name, *roster);
    if (id.empty() || id == expected_active_profile ||
        !is_safe_profile_storage_id(id))
        return {BaldosaSecondRacerStatus::Invalid, {}};
    const auto target = resolve_host_profile_save_root(
        ExecutionMode::Modern, id);
    if (!target.isolated())
        return {BaldosaSecondRacerStatus::Invalid, {}};
    const fs::path directory = user_root / target.save_root;
    if (!baldosa_first_profile_entry_absent(directory))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    // Exclusive new directory is the only writable profile target. The
    // current P1 raw SRAM, typed state and selector remain BYTE-EXACT.
    std::error_code ec;
    if (!fs::create_directory(directory, ec) || ec)
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    auto state = make_default_host_profile_state(id);
    if (!state)
        return {BaldosaSecondRacerStatus::Invalid, {}};
    state->racer_identity = *proposed;
    auto fresh_source = clean_stock_sram();
    fresh_source[0x0748] = proposed->rider_index;
    if (!stock_sram_format_signature_present(
            fresh_source.data(), fresh_source.size()) ||
        capture_stock_sram_for_profile(
            ExecutionMode::Modern, *state,
            fresh_source.data(), fresh_source.size()) !=
                HostProfileTransferStatus::Applied)
        return {BaldosaSecondRacerStatus::Invalid, {}};

    const fs::path typed_path = directory / "host-profile.txt";
    if (save_host_profile_state_file_if_current(
            ExecutionMode::Modern, typed_path.string(), std::nullopt,
            *state) != HostProfileSaveStatus::Saved)
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    const fs::path raw_path = directory / "save.srm";
    if (!baldosa_first_profile_entry_absent(raw_path))
        return {BaldosaSecondRacerStatus::ExistingData, {}};
    {
        std::ofstream raw(raw_path, std::ios::binary | std::ios::out);
        if (!raw.write(
                reinterpret_cast<const char*>(fresh_source.data()),
                static_cast<std::streamsize>(fresh_source.size())) ||
            !raw.flush())
            return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    }
    if (!baldosa_native_selected_profile_paths_are_real(
            user_root, target.save_root) ||
        !baldosa_sram_file_matches_exact(
            raw_path, fresh_source.data(), kStockSramBytes))
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    // Publish the single new row LAST, under the existing catalog OS lock.
    // save_host_profile_catalog_file_if_current() would acquire the same
    // lock again here: deliberately use its established staged-store
    // primitive, after the roster was loaded under THIS exclusive lock.
    std::vector<HostProfileCatalogEntry> expanded = *roster;
    expanded.push_back({id, *proposed});
    if (!save_host_profile_catalog_file(catalog_path.string(), expanded))
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    // Global selection remains the original, verified P1 throughout.
    return {BaldosaSecondRacerStatus::Created, id};
}


// A native process can die AFTER writing a complete new P2 typed/raw stock
// profile but BEFORE appending its catalog entry. Retrying ordinary creation
// then refuses the existing directory forever. Recover only after the user
// explicitly chooses the SAME stock preset from the native P2 modal; do not
// scan orphan folders, repair partial bytes or switch the live P1 guest.
//
// Revalidate current P1 selector, single-row catalog and both isolated SRAM
// owners under the canonical global -> catalog -> P1 typed -> P2 typed
// interprocess locks. The new catalog row is the ONLY publication.
inline BaldosaSecondRacerResult recover_baldosa_second_preset_for_next_boot(
    const std::filesystem::path& user_root,
    std::string_view expected_active_profile,
    std::size_t preset_index) {
    namespace fs = std::filesystem;
    const auto preset = make_legacy_racer_identity(preset_index);
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !is_safe_profile_storage_id(expected_active_profile) ||
        !preset || !valid_racer_identity(*preset))
        return {BaldosaSecondRacerStatus::Invalid, {}};

    const fs::path selector = user_root / "host-state-v1.txt";
    const fs::path catalog = user_root / "profiles-v1.txt";
    if (!baldosa_native_real_file(selector) ||
        !baldosa_native_real_file(catalog) ||
        !baldosa_native_real_directory(user_root / "saves"))
        return {BaldosaSecondRacerStatus::ExistingData, {}};
    TournamentLaunchPathLock selector_lock(selector.string(), true);
    if (!selector_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    TournamentLaunchPathLock catalog_lock(catalog.string(), true);
    if (!catalog_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    const auto selected = load_host_product_state_file(selector.string());
    const auto roster = load_host_profile_catalog_file(catalog.string());
    if (!selected.loaded() || !selected.state->active_profile_id ||
        *selected.state->active_profile_id != expected_active_profile ||
        !roster || roster->size() != 1u ||
        roster->front().profile_id != expected_active_profile ||
        !is_safe_profile_storage_id(roster->front().profile_id) ||
        !valid_racer_identity(roster->front().identity) ||
        roster->front().identity == *preset)
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    const auto p1 = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(expected_active_profile));
    const std::string id = make_profile_id(preset->name, *roster);
    const auto p2 = resolve_host_profile_save_root(ExecutionMode::Modern, id);
    if (!p1.isolated() || !p2.isolated() ||
        !is_safe_profile_storage_id(id) ||
        id == expected_active_profile ||
        !baldosa_native_selected_profile_paths_are_real(user_root, p1.save_root) ||
        !baldosa_native_selected_profile_paths_are_real(user_root, p2.save_root))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    const fs::path active_typed =
        user_root / p1.save_root / "host-profile.txt";
    const fs::path staged_typed =
        user_root / p2.save_root / "host-profile.txt";
    TournamentLaunchPathLock active_lock(active_typed.string(), true);
    if (!active_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    TournamentLaunchPathLock staged_lock(staged_typed.string(), true);
    if (!staged_lock.acquired())
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};

    // Files may change between discovery and lock acquisition. No missing,
    // redirected or malformed canonical path is ever repaired or adopted.
    if (!baldosa_native_real_file(selector) ||
        !baldosa_native_real_file(catalog) ||
        !baldosa_native_selected_profile_paths_are_real(user_root, p1.save_root) ||
        !baldosa_native_selected_profile_paths_are_real(user_root, p2.save_root))
        return {BaldosaSecondRacerStatus::ExistingData, {}};
    const auto current = load_host_product_state_file(selector.string());
    const auto current_roster = load_host_profile_catalog_file(catalog.string());
    const auto active = load_host_profile_state_file(
        ExecutionMode::Modern, active_typed.string(),
        std::string(expected_active_profile));
    if (!current.loaded() || *current.state != *selected.state ||
        !current_roster || *current_roster != *roster ||
        !active.loaded() || !active.state->stock_sram ||
        !catalog_entry_matches_profile_state(roster->front(), *active.state) ||
        !baldosa_sram_file_matches_exact(
            user_root / p1.save_root / "save.srm",
            active.state->stock_sram->data(), kStockSramBytes))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    // The staging directory must contain ONLY the exactly reproducible
    // initial typed profile and its raw 8-KiB stock image. Additional files,
    // progression, a foreign ID, a short save or a symlink disqualify it.
    const fs::path staged_root = user_root / p2.save_root;
    std::error_code ec;
    std::size_t files = 0;
    fs::directory_iterator it(staged_root, ec), end;
    if (ec) return {BaldosaSecondRacerStatus::ExistingData, {}};
    for (; it != end; it.increment(ec)) {
        if (ec) return {BaldosaSecondRacerStatus::ExistingData, {}};
        const auto name = it->path().filename();
        if (name != "host-profile.txt" && name != "save.srm")
            return {BaldosaSecondRacerStatus::ExistingData, {}};
        ++files;
    }
    if (ec || files != 2u)
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    auto expected = make_default_host_profile_state(id);
    if (!expected) return {BaldosaSecondRacerStatus::Invalid, {}};
    expected->racer_identity = *preset;
    auto stock = clean_stock_sram();
    stock[0x0748] = preset->rider_index;
    if (!stock_sram_format_signature_present(stock.data(), stock.size()) ||
        capture_stock_sram_for_profile(
            ExecutionMode::Modern, *expected,
            stock.data(), stock.size()) != HostProfileTransferStatus::Applied)
        return {BaldosaSecondRacerStatus::Invalid, {}};

    const auto staged = load_host_profile_state_file(
        ExecutionMode::Modern, staged_typed.string(), id);
    if (!staged.loaded() || !(*staged.state == *expected) ||
        !baldosa_sram_file_matches_exact(
            staged_root / "save.srm", stock.data(), kStockSramBytes))
        return {BaldosaSecondRacerStatus::ExistingData, {}};

    // Under the existing catalog lock the standard staged store is the sole
    // writer; never recursively take its if-current lock. Any failure leaves
    // the source P1, staged P2 and catalog intact for explicit diagnosis.
    auto expanded = *roster;
    expanded.push_back({id, *preset});
    if (!save_host_profile_catalog_file(catalog.string(), expanded))
        return {BaldosaSecondRacerStatus::BusyOrIoError, {}};
    return {BaldosaSecondRacerStatus::Recovered, id};
}

}  // namespace ur::product

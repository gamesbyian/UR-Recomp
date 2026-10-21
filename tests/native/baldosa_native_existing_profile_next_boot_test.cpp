#include "baldosa_native_existing_profile_next_boot.hpp"
#include "baldosa_native_second_profile.hpp"
#include "baldosa_native_sram_recovery.hpp"
#include "baldosa_native_manual_sram_recovery.hpp"

#include <cassert>
#include <cstdio>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

// Simulate a non-cooperating external writer claiming the target only after
// this process has durably staged its intended immutable receipt.
static fs::path g_competing_archive;
static void publish_competing_archive() {
    std::ofstream out(g_competing_archive, std::ios::binary);
    assert(out.good());
    out << "preexisting external receipt";
    assert(out.good());
}

std::string bytes(const fs::path& file) {
    std::ifstream in(file, std::ios::binary);
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}

int main() {
    using Status = BaldosaExistingProfileSelectionStatus;
    const fs::path root = fs::temp_directory_path() /
        ("ur-existing-p1-nextboot-" + std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    assert(fs::create_directory(root));
    const auto archive = root / "immutable-recovery-receipt.bin";
    assert(write_host_create_staged(
        archive.string(), "original receipt", "qa-archive"));
    assert(bytes(archive) == "original receipt");
    assert(!write_host_create_staged(
        archive.string(), "new receipt", "qa-archive"));
    assert(bytes(archive) == "original receipt");
    g_competing_archive = root / "concurrent-receipt.bin";
    assert(!write_host_create_staged(
        g_competing_archive.string(), "candidate receipt", "qa-race",
        publish_competing_archive));
    assert(bytes(g_competing_archive) == "preexisting external receipt");
    const auto empty = root / "empty";
    assert(fs::create_directory(empty));

    // No default, implicit catalog scan, or anonymous live guest identity.
    assert(select_baldosa_existing_profile_for_next_boot(
               empty, "mike", "andrew").status ==
           Status::RejectedAuthority);
    assert(select_baldosa_existing_profile_for_next_boot(
               fs::path("relative-root"), "mike", "andrew").status ==
           Status::InvalidRequest);
    assert(create_baldosa_first_preset_for_next_boot(empty, 0).created());
    assert(select_baldosa_existing_profile_for_next_boot(
               empty, "mike", "andrew").status ==
           Status::RejectedAuthority);
    assert(create_baldosa_second_preset_for_next_boot(
               empty, "mike", 1).created());

    const fs::path global = empty / "host-state-v1.txt";
    const fs::path catalog = empty / "profiles-v1.txt";
    const fs::path mtyped = empty / "saves/profile-mike/host-profile.txt";
    const fs::path araw = empty / "saves/profile-andrew/save.srm";
    const fs::path mraw = empty / "saves/profile-mike/save.srm";
    const fs::path atyped = empty / "saves/profile-andrew/host-profile.txt";
    const auto before = load_host_product_state_file(global.string());
    assert(before.loaded() && before.state->active_profile_id == "mike");
    auto settings = *before.state;
    settings.settings.pause_on_focus_loss = false;
    assert(save_host_product_state_file_if_current(
        global.string(), *before.state, settings) ==
        HostProductSaveStatus::Saved);
    const std::string roster_before = bytes(catalog);
    const std::string mike_typed_before = bytes(mtyped);
    const std::string mike_raw_before = bytes(mraw);
    const std::string andrew_typed_before = bytes(atyped);
    const std::string andrew_raw_before = bytes(araw);
    assert(mike_raw_before.size() == kStockSramBytes &&
           andrew_raw_before.size() == kStockSramBytes &&
           !mike_typed_before.empty() && !andrew_typed_before.empty());

    // Only a current-owner-confirmed profile selection is accepted. No
    // source or destination SRAM capture, mutation or catalog rewrite.
    for (const auto& invalid : {
        select_baldosa_existing_profile_for_next_boot(
            empty, "andrew", "mike"),
        select_baldosa_existing_profile_for_next_boot(
            empty, "mike", "mike"),
        select_baldosa_existing_profile_for_next_boot(
            empty, "mike", "../andrew"),
        select_baldosa_existing_profile_for_next_boot(
            empty, "mike", "unregistered"),
    }) {
        assert(!invalid.selected());
    }
    assert(load_host_product_state_file(global.string())
               .state->active_profile_id == "mike");
    {
        TournamentLaunchPathLock outside_lock(global.string(), true);
        assert(outside_lock.acquired());
        assert(select_baldosa_existing_profile_for_next_boot(
                   empty, "mike", "andrew").status ==
               Status::BusyOrIoError);
    }
    assert(load_host_product_state_file(global.string())
               .state->active_profile_id == "mike");

    // The live controller approves a REQUEST, not an immediate selector
    // mutation. Keep all authorized file bytes exact until ORIGINAL native
    // RtlWriteSram and the typed CAS have both succeeded on shutdown.
    const auto checked_only = select_baldosa_existing_profile_for_next_boot(
        empty, "mike", "andrew", false, true);
    assert(checked_only.selected() &&
           checked_only.next_profile_id == "andrew");
    assert(load_host_product_state_file(global.string())
               .state->active_profile_id == "mike");
    assert(bytes(catalog) == roster_before);
    assert(bytes(mtyped) == mike_typed_before);
    assert(bytes(mraw) == mike_raw_before);
    assert(bytes(atyped) == andrew_typed_before);
    assert(bytes(araw) == andrew_raw_before);

    const auto swapped =
        select_baldosa_existing_profile_for_next_boot(
            empty, "mike", "andrew");
    assert(swapped.selected() && swapped.next_profile_id == "andrew");
    const auto after = load_host_product_state_file(global.string());
    assert(after.loaded() && after.state->active_profile_id == "andrew" &&
           !after.state->settings.pause_on_focus_loss);
    assert(bytes(catalog) == roster_before);
    assert(bytes(mtyped) == mike_typed_before);
    assert(bytes(mraw) == mike_raw_before);
    assert(bytes(atyped) == andrew_typed_before);
    assert(bytes(araw) == andrew_raw_before);
    assert(select_baldosa_existing_profile_for_next_boot(
               empty, "mike", "andrew").status ==
           Status::RejectedAuthority);
    assert(select_baldosa_existing_profile_for_next_boot(
               empty, "andrew", "mike").selected());
    assert(load_host_product_state_file(global.string())
               .state->active_profile_id == "mike");
    assert(bytes(catalog) == roster_before);
    assert(bytes(mraw) == mike_raw_before);
    assert(bytes(araw) == andrew_raw_before);

    // Corrupted guest raw SRAM is NOT fixed by a selector change, and no
    // rollback to a different profile is permitted on wrong typed/catalog.
    {
        std::fstream raw(araw, std::ios::binary |
                               std::ios::in | std::ios::out);
        raw.seekp(0x0748);
        raw.put(static_cast<char>(0x7f));
        raw.flush();
    }
    const std::string corrupt_raw = bytes(araw);
    assert(select_baldosa_existing_profile_for_next_boot(
               empty, "mike", "andrew").status ==
           Status::RejectedAuthority);
    assert(bytes(araw) == corrupt_raw);
    assert(load_host_product_state_file(global.string())
               .state->active_profile_id == "mike");

#ifndef _WIN32
    const auto redirected = root / "redirected";
    assert(fs::create_directory(redirected));
    assert(create_baldosa_first_preset_for_next_boot(redirected, 0).created());
    assert(create_baldosa_second_preset_for_next_boot(
               redirected, "mike", 1).created());
    fs::remove(redirected / "saves/profile-andrew/save.srm");
    fs::create_symlink(mraw, redirected / "saves/profile-andrew/save.srm");
    assert(select_baldosa_existing_profile_for_next_boot(
               redirected, "mike", "andrew").status ==
           Status::RejectedAuthority);
#endif

    // An exact durable intent is a write-ahead authorization, not a
    // permission to promote an arbitrary full-size raw save. Exercise
    // independently restarted "processes" through the same production
    // selector/catalog/typed/raw codecs and persistent OS locks.
    const auto intent_fixture = [&](const char* label) {
        const fs::path dir = root / label;
        assert(fs::create_directory(dir));
        assert(create_baldosa_first_preset_for_next_boot(dir, 0).created());
        assert(create_baldosa_second_preset_for_next_boot(
            dir, "mike", 1).created());
        return dir;
    };
    const auto before_save = [&](const fs::path& dir) {
        const auto state = load_host_product_state_file(
            (dir / "host-state-v1.txt").string());
        const auto profile = load_host_profile_state_file(
            ExecutionMode::Modern,
            (dir / "saves/profile-mike/host-profile.txt").string(), "mike");
        assert(state.loaded() && profile.loaded() &&
               profile.state->stock_sram);
        return std::make_pair(*state.state, *profile.state);
    };
    const auto make_changed = [](const HostProfileState& state) {
        auto bytes = *state.stock_sram;
        bytes[0x0a10] ^= 0x31u;
        return bytes;
    };
    const auto write_bytes = [](const fs::path& path,
                                const std::array<std::uint8_t,
                                    kStockSramBytes>& data) {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        assert(out);
        out.write(reinterpret_cast<const char*>(data.data()), data.size());
        assert(out.good());
    };
    // Canonical multi-racer catalogs are legal, even though the current
    // native P2-creation UI deliberately stops at two. A historical Modern
    // roster may have 3+, and broken unrelated racers must not lock out an
    // authenticated healthy destination. No alternate catalog format.
    const auto register_third_profile = [&](const fs::path& dir) {
        const auto third = make_legacy_racer_identity(2);
        assert(third && valid_racer_identity(*third));
        const fs::path catalog = dir / "profiles-v1.txt";
        auto roster = load_host_profile_catalog_file(catalog.string());
        assert(roster && roster->size() == 2);
        const std::string id = make_profile_id(third->name, *roster);
        assert(!id.empty() && is_safe_profile_storage_id(id));
        const auto location = resolve_host_profile_save_root(
            ExecutionMode::Modern, id);
        assert(location.isolated());
        const fs::path directory = dir / location.save_root;
        assert(fs::create_directory(directory));
        auto profile = make_default_host_profile_state(id);
        assert(profile);
        profile->racer_identity = *third;
        auto raw = clean_stock_sram();
        raw[0x0748] = third->rider_index;
        assert(capture_stock_sram_for_profile(
            ExecutionMode::Modern, *profile, raw.data(), raw.size()) ==
            HostProfileTransferStatus::Applied);
        assert(save_host_profile_state_file_if_current(
            ExecutionMode::Modern,
            (directory / "host-profile.txt").string(),
            std::nullopt, *profile) == HostProfileSaveStatus::Saved);
        write_bytes(directory / "save.srm", raw);
        roster->push_back({id, *third});
        assert(save_host_profile_catalog_file(catalog.string(), *roster));
        return id;
    };
    {
        const auto dir = intent_fixture("three-entry-roster-unrelated-broken");
        const auto id = register_third_profile(dir);
        const auto third_typed =
            dir / "saves" / ("profile-" + id) / "host-profile.txt";
        const auto third_raw =
            dir / "saves" / ("profile-" + id) / "save.srm";
        const std::string unrelated_raw = bytes(third_raw);
        fs::remove(third_typed); // unrelated and genuinely damaged
        const auto roster_before = bytes(dir / "profiles-v1.txt");
        const auto andrew_raw = bytes(dir / "saves/profile-andrew/save.srm");
        const auto andrew_typed =
            bytes(dir / "saves/profile-andrew/host-profile.txt");
        assert(select_baldosa_existing_profile_for_next_boot(
            dir, "mike", "andrew").selected());
        assert(select_baldosa_existing_profile_for_next_boot(
            dir, "andrew", "mike").selected());
        assert(!select_baldosa_existing_profile_for_next_boot(
            dir, "mike", id).selected()); // chosen destination is broken
        const fs::path mike_raw = dir / "saves/profile-mike/save.srm";
        auto damaged = bytes(mike_raw);
        assert(damaged.size() == kStockSramBytes);
        damaged[0x0748] ^= 0x31;
        { std::ofstream out(mike_raw, std::ios::binary | std::ios::trunc);
          out.write(damaged.data(), damaged.size());
          assert(out.good()); }
        const auto mike_typed = bytes(
            dir / "saves/profile-mike/host-profile.txt");
        assert(select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", "andrew").selected());
        assert(bytes(mike_raw) == damaged);
        assert(bytes(dir / "saves/profile-mike/host-profile.txt") == mike_typed);
        assert(bytes(dir / "profiles-v1.txt") == roster_before);
        assert(bytes(third_raw) == unrelated_raw && !fs::exists(third_typed));
        assert(bytes(dir / "saves/profile-andrew/save.srm") == andrew_raw);
        assert(bytes(dir / "saves/profile-andrew/host-profile.txt") ==
               andrew_typed);
        assert(load_host_product_state_file(
            (dir / "host-state-v1.txt").string()).state->active_profile_id ==
            "andrew");
    }
    {
        const auto dir = intent_fixture("three-entry-roster-healthy-third");
        const auto third = register_third_profile(dir);
        const auto original_third_raw =
            bytes(dir / "saves" / ("profile-" + third) / "save.srm");
        const auto original_roster = bytes(dir / "profiles-v1.txt");
        fs::remove(dir / "saves/profile-mike/host-profile.txt");
        // Previously the hardcoded two-entry condition rejected this.
        assert(select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", third).selected());
        assert(bytes(dir / "profiles-v1.txt") == original_roster);
        assert(bytes(dir / "saves" / ("profile-" + third) / "save.srm") ==
               original_third_raw);
        assert(!fs::exists(dir / "saves/profile-mike/host-profile.txt"));
    }
    const auto stage_intent = [&](const fs::path& dir,
                                  const HostProductState& global,
                                  const HostProfileState& profile,
                                  const std::array<std::uint8_t,
                                      kStockSramBytes>& live) {
        TournamentLaunchPathLock sel(
            (dir / "host-state-v1.txt").string(), true);
        TournamentLaunchPathLock cat(
            (dir / "profiles-v1.txt").string(), true);
        TournamentLaunchPathLock typed(
            (dir / "saves/profile-mike/host-profile.txt").string(), true);
        assert(sel.acquired() && cat.acquired() && typed.acquired());
        const BaldosaSramCheckpoint req{
            dir, global, profile, live.data(), live.size()};
        return prepare_baldosa_sram_intent_under_lock(req);
    };
    {
        const auto dir = intent_fixture("intent-before-raw");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        // Staging must not change a single raw/typed authority byte.
        const auto raw = dir / "saves/profile-mike/save.srm";
        const std::string old_raw = bytes(raw);
        const std::string old_typed = bytes(
            dir / "saves/profile-mike/host-profile.txt");
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Rejected);
        const auto pending = dir / "saves/profile-mike/native-sram-checkpoint.pending";
        const std::string exact_guest_intent = bytes(pending);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Cleared);
        assert(!fs::exists(pending));
        assert(bytes(raw) == old_raw);
        assert(bytes(dir / "saves/profile-mike/host-profile.txt") == old_typed);
        fs::path retained_uncommitted;
        std::size_t retained_count = 0;
        for (const auto& entry : fs::directory_iterator(
                 dir / "saves/profile-mike")) {
            if (entry.path().filename().string().find(
                    "native-sram-uncommitted-") == 0) {
                retained_uncommitted = entry.path();
                ++retained_count;
            }
        }
        assert(retained_count == 1);
        assert(bytes(retained_uncommitted) == exact_guest_intent);
        const auto retained = decode_baldosa_sram_intent(
            bytes(retained_uncommitted), "mike");
        assert(retained && retained->previous == profile &&
               retained->next.stock_sram == changed &&
               retained->next.autosave_generation ==
                   profile.autosave_generation + 1);
        // An uncommitted copy must never silently mint typed progress,
        // a run record, or another cold-start repair.
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
        assert(bytes(retained_uncommitted) == exact_guest_intent);
        assert(!fs::exists(dir / "runs"));
    }
    {
        const auto dir = intent_fixture("intent-before-raw-archive-conflict");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        const auto root = dir / "saves/profile-mike";
        const auto pending = root / "native-sram-checkpoint.pending";
        const auto original = bytes(pending);
        const auto old_raw = bytes(root / "save.srm");
        const auto old_typed = bytes(root / "host-profile.txt");
        const auto intent = read_baldosa_sram_intent(pending, "mike");
        assert(intent);
        assert(archive_baldosa_recovered_intent(root, *intent, true));
        fs::path archive;
        for (const auto& entry : fs::directory_iterator(root)) {
            if (entry.path().filename().string().find(
                    "native-sram-uncommitted-") == 0) {
                assert(archive.empty());
                archive = entry.path();
            }
        }
        assert(!archive.empty());
        // Hostile preexisting same-name receipt has no authority.
        // A retry must refuse rather than replace it or retire pending.
        { std::ofstream out(archive, std::ios::binary | std::ios::trunc);
          assert(out);
          out << "foreign untrusted archive";
          assert(out.good()); }
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::IoError);
        assert(bytes(archive) == "foreign untrusted archive");
        assert(bytes(pending) == original);
        assert(bytes(root / "save.srm") == old_raw);
        assert(bytes(root / "host-profile.txt") == old_typed);
        fs::remove(archive);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Cleared);
        assert(bytes(archive) == original && !fs::exists(pending));
        assert(bytes(root / "save.srm") == old_raw);
        assert(bytes(root / "host-profile.txt") == old_typed);
    }
    {
        const auto dir = intent_fixture("intent-after-raw");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        const std::string original = bytes(typed);
        write_bytes(raw, changed);  // abrupt _Exit(86) before typed CAS
        const std::string changed_raw = bytes(raw);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Reconciled);
        const auto reread = load_host_profile_state_file(
            ExecutionMode::Modern, typed.string(), "mike");
        assert(reread.loaded() && reread.state->stock_sram == changed);
        assert(reread.state->autosave_generation ==
               profile.autosave_generation + 1);
        assert(bytes(raw) == changed_raw);
        assert(bytes(typed) != original);
        fs::path history;
        std::size_t history_count = 0;
        for (const auto& entry : fs::directory_iterator(
                 dir / "saves/profile-mike")) {
            if (entry.path().filename().string().find(
                    "native-sram-recovered-") == 0) {
                history = entry.path();
                ++history_count;
            }
        }
        assert(history_count == 1 && fs::is_regular_file(history));
        const auto receipt = decode_baldosa_sram_intent(bytes(history), "mike");
        assert(receipt && receipt->previous == profile &&
               receipt->next == *reread.state);
        const std::string archived = bytes(history);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
        assert(bytes(history) == archived);
        assert(!fs::exists(dir / "runs"));
        assert(!fs::exists(dir / "multiplayer-runs"));
    }
    {
        const auto dir = intent_fixture("intent-after-typed");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        auto next = profile;
        assert(capture_stock_sram_for_profile(
            ExecutionMode::Modern, next, changed.data(), changed.size()) ==
               HostProfileTransferStatus::Applied);
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        write_bytes(dir / "saves/profile-mike/save.srm", changed);
        assert(save_host_profile_state_file_if_current(
            ExecutionMode::Modern, typed.string(), profile, next) ==
               HostProfileSaveStatus::Saved);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Reconciled);
        assert(before_save(dir).second == next);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
    }
    {
        const auto dir = intent_fixture("intent-untrusted");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        auto foreign = changed;
        foreign[0x0711] ^= 0x45u;
        write_bytes(raw, foreign); // partial/out-of-band untrusted bytes
        const std::string raw_before = bytes(raw);
        const std::string typed_before = bytes(typed);
        const std::string roster_before = bytes(dir / "profiles-v1.txt");
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        // Ordinary switch still rejects untrusted source. Emergency switch
        // permits independently authenticated healthy destination only.
        assert(!select_baldosa_existing_profile_for_next_boot(
            dir, "mike", "andrew").selected());
        assert(select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", "andrew").selected());
        assert(bytes(raw) == raw_before && bytes(typed) == typed_before &&
               bytes(dir / "profiles-v1.txt") == roster_before);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "andrew") ==
               BaldosaSramIntentStatus::NoIntent);
        assert(!select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", "andrew").selected());  // stale expected selector
    }
    {
        const auto dir = intent_fixture("intent-missing-typed");
        const auto damaged = dir / "saves/profile-mike/host-profile.txt";
        const auto old_raw = bytes(dir / "saves/profile-mike/save.srm");
        fs::remove(damaged);
        assert(select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", "andrew").selected());
        assert(!fs::exists(damaged));
        assert(bytes(dir / "saves/profile-mike/save.srm") == old_raw);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "andrew") ==
               BaldosaSramIntentStatus::NoIntent);
    }
    {
        const auto dir = intent_fixture("intent-corrupt");
        const auto pending = dir /
            "saves/profile-mike/native-sram-checkpoint.pending";
        { std::ofstream out(pending, std::ios::binary);
          out << "bad intent"; }
        const auto before = before_save(dir);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        assert(before_save(dir).second == before.second);
        assert(bytes(pending) == "bad intent");
    }


    {
        // A malformed pending intent must NEVER auto-authorize guest raw.
        // But a human's explicit typed rollback can preserve opaque bad
        // intent, preserve original guest raw and restore the known-good pair.
        const auto dir = intent_fixture("malformed-intent-explicit-typed");
        const auto [global, profile] = before_save(dir);
        const auto root = dir / "saves/profile-mike";
        const auto raw = root / "save.srm";
        const auto typed = root / "host-profile.txt";
        const auto pending = root / "native-sram-checkpoint.pending";
        const auto selector = dir / "host-state-v1.txt";
        const auto roster = dir / "profiles-v1.txt";
        const std::string old_typed = bytes(typed);
        const std::string old_selector = bytes(selector);
        const std::string old_catalog = bytes(roster);
        write_bytes(raw, make_changed(profile));
        const std::string changed_raw = bytes(raw);
        const std::string corrupt("INVALID\0INTENT\xff", 15);
        { std::ofstream out(pending, std::ios::binary);
          out.write(corrupt.data(), corrupt.size()); }
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(bytes(raw) == changed_raw &&
               bytes(typed) == old_typed && bytes(pending) == corrupt);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(!fs::exists(pending));
        assert(bytes(raw) ==
               std::string(reinterpret_cast<const char*>(
                   profile.stock_sram->data()), kStockSramBytes));
        assert(bytes(typed) == old_typed &&
               bytes(selector) == old_selector &&
               bytes(roster) == old_catalog);
        std::size_t manual_count = 0, bad_intent_count = 0;
        for (const auto& entry : fs::directory_iterator(root)) {
            const std::string name = entry.path().filename().string();
            if (name.find("native-sram-manual-archive-") == 0) {
                ++manual_count;
                assert(bytes(entry.path()).find(changed_raw) !=
                       std::string::npos);
            } else if (name.find("native-sram-untrusted-intent-") == 0) {
                ++bad_intent_count;
                const auto record = bytes(entry.path());
                assert(record.find(
                    "UR-BALDOSA-UNTRUSTED-SRAM-INTENT/1\n") == 0);
                assert(record.substr(record.size() - corrupt.size()) ==
                       corrupt);
            }
        }
        assert(manual_count == 1 && bad_intent_count == 1);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::AlreadyConsistent);
    }
    {
        // Even if original raw == typed, malformed pending remains a cold
        // blocker until explicit archive-first typed retirement.
        const auto dir = intent_fixture("malformed-intent-old-raw");
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto pending = dir /
            "saves/profile-mike/native-sram-checkpoint.pending";
        const auto canonical = bytes(raw);
        const auto canonical_typed = bytes(typed);
        { std::ofstream out(pending, std::ios::binary);
          out << "bad intent"; }
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(!fs::exists(pending) && bytes(raw) == canonical &&
               bytes(typed) == canonical_typed);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
    }
    {
        // Never read a huge or redirected pending path into the manual
        // untrusted-intent archive, or discard it under a recovery choice.
        const auto dir = intent_fixture("malformed-intent-too-large");
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto pending = dir /
            "saves/profile-mike/native-sram-checkpoint.pending";
        const auto old_raw = bytes(raw), old_typed = bytes(typed);
        { std::ofstream out(pending, std::ios::binary);
          out << std::string(100001, 'X'); }
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(bytes(raw) == old_raw && bytes(typed) == old_typed &&
               bytes(pending).size() == 100001);
    }


    {
        // Historical post-raw/pre-typed _Exit(86) WITHOUT any intent: the
        // guest-authored bytes cannot be promoted without human choice.
        const auto dir = intent_fixture("legacy-raw-choice");
        const auto [global, profile] = before_save(dir);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto guest = make_changed(profile);
        const std::string original_typed = bytes(typed);
        write_bytes(raw, guest);
        const std::string guest_raw = bytes(raw);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "andrew", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::RestoredRaw);
        assert(bytes(raw) == guest_raw);
        const auto after = load_host_profile_state_file(
            ExecutionMode::Modern, typed.string(), "mike");
        assert(after.loaded() && after.state->stock_sram == guest);
        assert(after.state->autosave_generation ==
               profile.autosave_generation + 1);
        assert(bytes(typed) != original_typed);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::AlreadyConsistent);
        const auto archives = [&] {
            std::vector<fs::path> found;
            for (const auto& entry : fs::directory_iterator(
                     dir / "saves/profile-mike"))
                if (entry.path().filename().string().find(
                        "native-sram-manual-archive-") == 0)
                    found.push_back(entry.path());
            return found;
        }();
        assert(archives.size() == 1);
        const std::string archive = bytes(archives[0]);
        assert(archive.find("UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n") == 0);
        assert(archive.find(original_typed) != std::string::npos);
        assert(archive.find(guest_raw) != std::string::npos);
        assert(!fs::exists(dir / "runs") &&
               !fs::exists(dir / "multiplayer-runs"));
    }
    {
        // The loader accepts harmless noncanonical typed text. A manual
        // recovery archive must retain the ACTUAL original file bytes, not
        // silently encode the decoded state back to canonical formatting.
        const auto dir = intent_fixture("legacy-typed-exact-file-archive");
        const auto [global, profile] = before_save(dir);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const std::string canonical = bytes(typed);
        const auto header_end = canonical.find('\n');
        assert(header_end != std::string::npos);
        const std::string noncanonical =
            canonical.substr(0, header_end + 1) + "\n" +
            canonical.substr(header_end + 1);
        { std::ofstream out(typed, std::ios::binary | std::ios::trunc);
          assert(out && out.write(noncanonical.data(),
                                  static_cast<std::streamsize>(noncanonical.size()))); }
        const auto accepted = load_host_profile_state_file(
            ExecutionMode::Modern, typed.string(), "mike");
        assert(accepted.loaded() && *accepted.state == profile);
        const auto changed = make_changed(profile);
        write_bytes(raw, changed);
        const std::string interrupted_raw = bytes(raw);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(bytes(typed) == noncanonical && bytes(raw) != interrupted_raw);
        std::size_t count = 0;
        for (const auto& entry : fs::directory_iterator(
                 dir / "saves/profile-mike")) {
            if (entry.path().filename().string().find(
                    "native-sram-manual-archive-") != 0)
                continue;
            ++count;
            const std::string expected =
                "UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n" +
                std::to_string(noncanonical.size()) + "\n1\n8192\n" +
                noncanonical + interrupted_raw;
            assert(bytes(entry.path()) == expected);
        }
        assert(count == 1);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::AlreadyConsistent);
    }
    {
        const auto dir = intent_fixture("legacy-typed-choice");
        const auto [global, profile] = before_save(dir);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto guest = make_changed(profile);
        const std::string baseline = bytes(typed);
        write_bytes(raw, guest);
        const std::string guest_raw = bytes(raw);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(bytes(typed) == baseline);
        assert(baldosa_sram_file_matches_exact(
            raw, profile.stock_sram->data(), kStockSramBytes));
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::AlreadyConsistent);
        std::size_t archives = 0;
        for (const auto& entry : fs::directory_iterator(
                 dir / "saves/profile-mike")) {
            if (entry.path().filename().string().find(
                    "native-sram-manual-archive-") == 0) {
                ++archives;
                assert(bytes(entry.path()).find(guest_raw) !=
                       std::string::npos);
            }
        }
        assert(archives == 1);
    }
    {
        const auto dir = intent_fixture("legacy-short-raw");
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto baseline = bytes(typed);
        { std::ofstream out(raw, std::ios::binary | std::ios::trunc);
          out << "SHORT!"; }
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(bytes(raw) == "SHORT!" && bytes(typed) == baseline);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(bytes(typed) == baseline);
    }
    {
        const auto dir = intent_fixture("legacy-journal-conflict");
        const auto [global, profile] = before_save(dir);
        const auto next = make_changed(profile);
        assert(stage_intent(dir, global, profile, next) ==
               BaldosaSramIntentStatus::Prepared);
        write_bytes(dir / "saves/profile-mike/save.srm", next);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Reconciled);
    }

    {
        const auto dir = intent_fixture("partial-raw-explicit-rollback");
        const auto [global, profile] = before_save(dir);
        const auto changed = make_changed(profile);
        const auto raw = dir / "saves/profile-mike/save.srm";
        const auto typed = dir / "saves/profile-mike/host-profile.txt";
        const auto pending = dir /
            "saves/profile-mike/native-sram-checkpoint.pending";
        assert(stage_intent(dir, global, profile, changed) ==
               BaldosaSramIntentStatus::Prepared);
        const std::string intent_bytes = bytes(pending);
        { std::ofstream out(raw, std::ios::binary | std::ios::trunc);
          out << "INTERRUPTED NATIVE WRITE"; }
        const std::string partial = bytes(raw);
        const std::string committed = bytes(typed);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Rejected);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(bytes(raw) == partial && bytes(typed) == committed &&
               bytes(pending) == intent_bytes);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::RestoredCommitted);
        assert(bytes(typed) == committed);
        assert(!fs::exists(pending));
        assert(baldosa_sram_file_matches_exact(
            raw, profile.stock_sram->data(), kStockSramBytes));
        bool saw_raw = false, saw_intent = false;
        for (const auto& entry : fs::directory_iterator(
                 dir / "saves/profile-mike")) {
            const auto name = entry.path().filename().string();
            if (name.find("native-sram-manual-archive-") == 0) {
                saw_raw = bytes(entry.path()).find(partial) !=
                          std::string::npos;
            }
            if (name.find("native-sram-recovered-") == 0) {
                saw_intent = bytes(entry.path()) == intent_bytes;
            }
        }
        assert(saw_raw && saw_intent);
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::RestoreCommitted) ==
               BaldosaManualSramRecoveryStatus::AlreadyConsistent);
        assert(!fs::exists(dir / "runs"));
    }
    {
        const auto dir = intent_fixture("legacy-missing-sidecar");
        fs::remove(dir / "saves/profile-mike/host-profile.txt");
        const std::string before = bytes(
            dir / "saves/profile-mike/save.srm");
        assert(recover_baldosa_legacy_sram_explicit(
            dir, "mike", BaldosaManualSramChoice::TrustGuestRaw) ==
               BaldosaManualSramRecoveryStatus::Rejected);
        assert(bytes(dir / "saves/profile-mike/save.srm") == before);
        assert(select_baldosa_healthy_profile_from_damaged_for_next_boot(
            dir, "mike", "andrew").selected());
    }

    fs::remove_all(root);
    std::puts("PASS: next-boot named P1 selection preserves original typed/"
              "raw/catalog bytes, rejects stale owner, corrupt SRAM and "
              "selector lock contention");
}

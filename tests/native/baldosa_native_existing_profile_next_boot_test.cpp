#include "baldosa_native_existing_profile_next_boot.hpp"
#include "baldosa_native_second_profile.hpp"
#include "baldosa_native_sram_recovery.hpp"

#include <cassert>
#include <cstdio>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

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
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::Cleared);
        assert(bytes(raw) == old_raw);
        assert(bytes(dir / "saves/profile-mike/host-profile.txt") == old_typed);
        assert(recover_baldosa_sram_intent_on_cold_boot(dir, "mike") ==
               BaldosaSramIntentStatus::NoIntent);
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
        const auto history = dir / "saves/profile-mike" /
            ("native-sram-recovered-" +
             std::to_string(profile.autosave_generation) + "-to-" +
             std::to_string(profile.autosave_generation + 1) + ".txt");
        assert(fs::is_regular_file(history));
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

    fs::remove_all(root);
    std::puts("PASS: next-boot named P1 selection preserves original typed/"
              "raw/catalog bytes, rejects stale owner, corrupt SRAM and "
              "selector lock contention");
}

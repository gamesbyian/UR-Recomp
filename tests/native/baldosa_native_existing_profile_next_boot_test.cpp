#include "baldosa_native_existing_profile_next_boot.hpp"
#include "baldosa_native_second_profile.hpp"

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
    fs::remove_all(root);
    std::puts("PASS: next-boot named P1 selection preserves original typed/"
              "raw/catalog bytes, rejects stale owner, corrupt SRAM and "
              "selector lock contention");
}

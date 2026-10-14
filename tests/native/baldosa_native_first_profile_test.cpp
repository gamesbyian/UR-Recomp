#include "baldosa_native_first_profile.hpp"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

int main() {
    const auto stamp = std::chrono::steady_clock::now()
                           .time_since_epoch().count();
    const fs::path workspace = fs::temp_directory_path() /
        ("ur-native-first-racer-" + std::to_string(stamp));
    assert(fs::create_directory(workspace));
    const auto empty = workspace / "empty";
    assert(fs::create_directory(empty));
    const auto bad = create_baldosa_first_preset_for_next_boot(empty, 999u);
    assert(bad.status == BaldosaFirstRacerStatus::Invalid);
    assert(!fs::exists(empty / "host-state-v1.txt"));
    assert(!fs::exists(empty / "profiles-v1.txt"));
    assert(create_baldosa_first_preset_for_next_boot(
        fs::path("relative-folder"), 0).status ==
        BaldosaFirstRacerStatus::Invalid);

    // The same established catalog, typed state and exact 8KiB clean stock
    // image are now durable BEFORE the new native process reads its SRAM.
    const auto made = create_baldosa_first_preset_for_next_boot(empty, 0);
    assert(made.created() && made.profile_id == "mike");
    const auto selector =
        load_host_product_state_file((empty / "host-state-v1.txt").string());
    const auto catalog =
        load_host_profile_catalog_file((empty / "profiles-v1.txt").string());
    assert(selector.loaded() && selector.state->active_profile_id == "mike");
    assert(catalog && catalog->size() == 1);
    const auto identity = make_legacy_racer_identity(0);
    assert(identity && (*catalog)[0].identity == *identity);
    const auto save_root = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string("mike"));
    assert(save_root.isolated());
    assert(baldosa_native_selected_profile_paths_are_real(
        empty, save_root.save_root));
    const auto state = load_host_profile_state_file(
        ExecutionMode::Modern,
        (empty / save_root.save_root / "host-profile.txt").string(), "mike");
    assert(state.loaded() && state.state->stock_sram &&
           state.state->racer_identity == identity);
    const auto& canonical = clean_stock_sram();
    assert(*state.state->stock_sram == canonical);
    const fs::path raw = empty / save_root.save_root / "save.srm";
    assert(fs::file_size(raw) == kStockSramBytes);
    assert(baldosa_sram_file_matches_exact(
        raw, canonical.data(), canonical.size()));
    const auto before = fs::last_write_time(raw);
    assert(create_baldosa_first_preset_for_next_boot(empty, 1).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
    assert(fs::last_write_time(raw) == before);

    // A foreign/broken catalog, a dangling redirected save path, and
    // corrupted global state may not be silently overwritten.
    const auto foreign = workspace / "foreign";
    assert(fs::create_directory(foreign));
    { std::ofstream out(foreign / "profiles-v1.txt"); out << "junk\n"; }
    assert(create_baldosa_first_preset_for_next_boot(foreign, 0).status ==
           BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(foreign / "host-state-v1.txt"));
    { std::ofstream out(foreign / "host-state-v1.txt"); out << "corrupt\n"; }
    assert(create_baldosa_first_preset_for_next_boot(foreign, 0).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
#ifndef _WIN32
    const auto dangling = workspace / "dangling-selector";
    assert(fs::create_directory(dangling));
    fs::create_symlink("nonexistent-global-target",
                       dangling / "host-state-v1.txt");
    assert(create_baldosa_first_preset_for_next_boot(dangling, 0).status ==
           BaldosaFirstRacerStatus::AlreadyConfigured);
    assert(!fs::exists(dangling / "profiles-v1.txt"));
#endif

    const auto redirect = workspace / "redirect";
    assert(fs::create_directory(redirect));
    fs::create_directory(redirect / "saves");
    fs::create_directory(redirect / "saves/profile-mike");
    assert(create_baldosa_first_preset_for_next_boot(redirect, 0).status ==
           BaldosaFirstRacerStatus::ExistingData);
    assert(!fs::exists(redirect / "host-state-v1.txt"));
    fs::remove_all(workspace);
    std::puts("PASS: first Modern preset creation uses canonical clean SRAM "
              "and exact next-process catalog identity; refuses overwrite");
}

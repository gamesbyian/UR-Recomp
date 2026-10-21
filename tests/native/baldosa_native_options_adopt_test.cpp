#include "baldosa_native_options.hpp"

#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iterator>
#include <string>

namespace fs = std::filesystem;
using namespace ur::product;

namespace {

HostProductState read(const std::string& path) {
    const auto loaded = load_host_product_state_file(path);
    assert(loaded.loaded());
    return *loaded.state;
}

void missing_store_is_never_created(const fs::path& dir) {
    const auto path = (dir / "missing" / "options-v1.txt").string();
    assert(baldosa_options_adopt_live_display(path, 1, 1) == BaldosaOptionsAdopt::NoStore);
    assert(!fs::exists(path));
}

void live_change_is_recorded_once(const fs::path& dir) {
    const auto path = (dir / "options-v1.txt").string();
    HostProductState state;
    state.settings.display_mode = HostDisplayMode::Fullscreen;
    state.settings.vsync_mode = HostVSyncMode::On;
    state.settings.pause_on_focus_loss = false;  // unrelated field survives
    assert(save_host_product_state_file(path, state) == HostProductSaveStatus::Saved);

    // Alt+Enter left exclusive for windowed.
    assert(baldosa_options_adopt_live_display(path, 0, 1) == BaldosaOptionsAdopt::Saved);
    auto after = read(path);
    assert(after.settings.display_mode == HostDisplayMode::Windowed);
    assert(after.settings.vsync_mode == HostVSyncMode::On);
    assert(!after.settings.pause_on_focus_loss);
    // Nothing more to do while the live display stays put.
    assert(baldosa_options_adopt_live_display(path, 0, 1) == BaldosaOptionsAdopt::Unchanged);
    // Alt+Enter back into borderless.
    assert(baldosa_options_adopt_live_display(path, 1, 1) == BaldosaOptionsAdopt::Saved);
    assert(read(path).settings.display_mode == HostDisplayMode::BorderlessFullscreen);
}

void out_of_range_values_are_refused(const fs::path& dir) {
    const auto path = (dir / "options-v1.txt").string();
    const auto before = read(path);
    assert(baldosa_options_adopt_live_display(path, 3, 1) == BaldosaOptionsAdopt::Failed);
    assert(baldosa_options_adopt_live_display(path, 1, -1) == BaldosaOptionsAdopt::Failed);
    assert(read(path) == before);
}

void damaged_store_is_left_alone(const fs::path& dir) {
    const auto path = (dir / "damaged-options-v1.txt").string();
    {
        std::ofstream out(path, std::ios::binary);
        out << "not a host state file\n";
    }
    assert(baldosa_options_adopt_live_display(path, 2, 1) == BaldosaOptionsAdopt::NoStore);
    std::ifstream in(path, std::ios::binary);
    std::string text((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    assert(text == "not a host state file\n");
}

}  // namespace

int main() {
    const fs::path dir = fs::temp_directory_path() /
        ("ur-options-adopt-" + std::to_string(static_cast<unsigned long>(
            std::hash<std::string>{}(fs::current_path().string()))));
    fs::remove_all(dir);
    fs::create_directories(dir);
    missing_store_is_never_created(dir);
    live_change_is_recorded_once(dir);
    out_of_range_values_are_refused(dir);
    damaged_store_is_left_alone(dir);
    fs::remove_all(dir);
    std::puts("PASS: live display adopted into an existing typed store only");
    return 0;
}

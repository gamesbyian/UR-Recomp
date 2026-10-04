#include "host_product_store.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>

using namespace ur::product;

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string path = argv[1];

    std::remove(path.c_str());
    auto missing = load_host_product_state_file(path);
    assert(missing.status == HostProductLoadStatus::Missing);
    assert(!missing.state);

    HostProductState state;
    state.settings.pause_on_focus_loss = false;
    state.settings.vibration_enabled = false;
    state.settings.display_mode = HostDisplayMode::Fullscreen;
    state.settings.vsync_mode = HostVSyncMode::Adaptive;
    state.settings.presentation_fps_mode = HostPresentationFpsMode::Fps144;
    state.active_profile_id = "local.profile";
    assert(save_host_product_state_file(path, state) == HostProductSaveStatus::Saved);

    const auto loaded = load_host_product_state_file(path);
    assert(loaded.loaded());
    assert(*loaded.state == state);

    {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        out << "UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\n";
    }
    const auto rejected = load_host_product_state_file(path);
    assert(rejected.status == HostProductLoadStatus::Rejected);
    assert(!rejected.state);

    {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        out << std::string(4097, 'x');
    }
    const auto oversized = load_host_product_state_file(path);
    assert(oversized.status == HostProductLoadStatus::Rejected);
    assert(!oversized.state);

    std::remove(path.c_str());
    return 0;
}

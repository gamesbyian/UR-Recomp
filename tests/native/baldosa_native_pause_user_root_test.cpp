// Native path witness for the Modern pause lifecycle's Options consumers.
// The test process receives SNESRECOMP_USER_DATA_DIR from Python via the
// platform's ordinary process environment, including a non-ACP Win32 name.
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>

#include "baldosa_native_options_user_root.hpp"
#include "host_product_store.hpp"
#include "local_tournament_utf8_path.hpp"

int main() {
    namespace fs = std::filesystem;
    using namespace ur::product;

#if defined(_WIN32)
    const wchar_t* raw_root = _wgetenv(L"SNESRECOMP_USER_DATA_DIR");
    if (!raw_root || !*raw_root) return 1;
    const fs::path root(raw_root);
    const std::string expected = baldosa_options_path(root).u8string();
#else
    const char* raw_root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!raw_root || !*raw_root) return 1;
    const fs::path root(raw_root);
    const std::string expected = baldosa_options_path(root).string();
#endif
    const std::string options = baldosa_native_options_user_path_utf8();
    if (options.empty() || options != expected ||
        host_native_path_from_utf8(options) != baldosa_options_path(root))
        return 2;

    std::error_code ec;
    fs::create_directories(root, ec);
    if (ec) return 3;

    HostProductState state;
    state.settings.pause_on_focus_loss = false;
    if (save_host_product_state_file(options, state) != HostProductSaveStatus::Saved)
        return 4;
    const auto loaded = load_host_product_state_file(options);
    if (!loaded.loaded() || loaded.state->settings.pause_on_focus_loss)
        return 5;

    // The same UTF-8 path is used by the live display/vsync adoption route.
    if (baldosa_options_adopt_live_display(options, 1, 0) !=
        BaldosaOptionsAdopt::Saved)
        return 6;
    const auto adopted = load_host_product_state_file(options);
    if (!adopted.loaded() || adopted.state->settings.pause_on_focus_loss ||
        adopted.state->settings.display_mode != HostDisplayMode::BorderlessFullscreen ||
        adopted.state->settings.vsync_mode != HostVSyncMode::Off)
        return 7;

    std::puts("PASS: Unicode user root preserves focus pause and live display Options");
    return 0;
}

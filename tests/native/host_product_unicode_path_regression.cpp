// Source-bound proposed Windows storage regression, not yet integrated.
// Original observation: UR-Recomp main 3250a3762bdedea53793f4eed0789cab6ea43495.
// SDL_GetPrefPath supplies UTF-8; product_user_data_path retains its bytes.
// This test passes that same encoding to the production host-state store.
// Do not interpret a Linux pass as a Windows qualification.
#include "host_product_store.hpp"

#include <chrono>
#include <cstdio>
#include <filesystem>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace fs = std::filesystem;
using namespace ur::product;

int main() {
    const auto stamp = std::chrono::steady_clock::now()
                           .time_since_epoch().count();
#if defined(_WIN32)
    const auto pid = static_cast<unsigned long>(GetCurrentProcessId());
#else
    const auto pid = static_cast<unsigned long>(getpid());
#endif
    const fs::path root = fs::temp_directory_path() /
        ("ur-host-unicode-" + std::to_string(pid) + "-" +
         std::to_string(stamp));
    const fs::path native_dir = root / fs::u8path(u8"profile-\u6D4B\u8BD5-\U0001F3AE");
    const fs::path native_target = native_dir / "host-state-v1.txt";
    std::error_code ec;
    fs::create_directories(native_dir, ec);
    if (ec) {
        std::fprintf(stderr, "FAIL: unable to create native Unicode fixture\n");
        return 2;
    }

    // This is exactly the UTF-8 string representation returned by SDL's
    // preference-path API, without any ANSI code-page conversion.
    const std::string utf8_target = native_target.u8string();
    HostProductState expected;
    expected.active_profile_id = "local.profile";
    expected.settings.pause_on_focus_loss = false;

    const auto saved = save_host_product_state_file(utf8_target, expected);
    const auto loaded = load_host_product_state_file(utf8_target);
    const bool ok = saved == HostProductSaveStatus::Saved &&
                    loaded.loaded() && *loaded.state == expected &&
                    fs::is_regular_file(native_target);

#if defined(_WIN32)
    std::fprintf(stderr, "Windows ANSI code page: %u\n", GetACP());
#endif
    fs::remove_all(root, ec);
    if (!ok) {
        std::fprintf(stderr,
                     "FAIL: UTF-8 SDL-style path did not round-trip through "
                     "production host-state save/load\n");
        return 1;
    }
    std::puts("host_product_unicode_path_regression: ok");
    return 0;
}

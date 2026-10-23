// ROM-free negative: an ordinary selected profile under a symlinked *parent*
// of user_root must not pass admission. This is distinct from the leaf-only
// redirected-root regression merged in #2319.
#include "baldosa_native_profile_path_guard.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;
using ur::product::baldosa_native_selected_profile_paths_are_real;

int main() {
    const fs::path workspace = fs::temp_directory_path() /
        ("ur-profile-ancestor-" + std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    const fs::path real_parent = workspace / "real-parent";
    const fs::path real_root = real_parent / "actual-user-root";
    const fs::path profile = real_root / "saves" / "profile-alpha";
    std::error_code ec;
    fs::create_directories(profile, ec);
    if (ec) return 2;
    { std::ofstream(profile / "host-profile.txt") << "profile"; }
    { std::ofstream(profile / "save.srm") << "sram"; }
    const fs::path selected = "saves/profile-alpha";
    if (!baldosa_native_selected_profile_paths_are_real(real_root, selected))
        return 3;

    const fs::path alias_parent = workspace / "alias-parent";
    fs::create_directory_symlink(real_parent, alias_parent, ec);
    if (ec) {
        std::cout << "SKIP: symlink creation unavailable: " << ec.message() << '\n';
        fs::remove_all(workspace, ec);
        return 0;
    }
    const fs::path redirected_root = alias_parent / "actual-user-root";
    if (!baldosa_native_selected_profile_paths_are_real(redirected_root, selected)) {
        std::cout << "PASS: redirected ancestor rejected\n";
        fs::remove_all(workspace, ec);
        return 0;
    }
    std::cerr << "FAIL: redirected ancestor was accepted despite symlinked parent\n";
    fs::remove_all(workspace, ec);
    return 1;
}

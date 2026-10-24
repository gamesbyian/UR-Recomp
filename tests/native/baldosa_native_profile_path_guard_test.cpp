#include "baldosa_native_profile_path_guard.hpp"

#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;
using ur::product::baldosa_native_selected_profile_paths_are_real;

int main() {
    const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
    const fs::path workspace = fs::temp_directory_path() /
        ("ur-profile-root-guard-" + std::to_string(stamp));
    assert(fs::create_directory(workspace));
    const fs::path real_root = workspace / "actual-user-root";
    const fs::path profile = real_root / "saves/profile-alpha";
    assert(fs::create_directories(profile));
    { std::ofstream(profile / "host-profile.txt") << "profile"; }
    { std::ofstream(profile / "save.srm") << "sram"; }
    const fs::path selected = "saves/profile-alpha";
    assert(baldosa_native_selected_profile_paths_are_real(real_root, selected));
    assert(!baldosa_native_selected_profile_paths_are_real(
        real_root, "saves/profile-alpha/../profile-alpha"));

    // symlink_status() on descendants follows a redirected ancestor.
    // Check the user root itself before trusting its child file types.
    const fs::path redirected_root = workspace / "redirected-user-root";
    std::error_code ec;
    fs::create_directory_symlink(real_root, redirected_root, ec);
    if (!ec) {
        assert(!baldosa_native_selected_profile_paths_are_real(
            redirected_root, selected));
        assert(fs::exists(profile / "save.srm"));
    } else {
        std::cout << "SKIP: symlink creation unsupported: " << ec.message() << '\n';
    }
    fs::remove_all(workspace);
    std::cout << "PASS: direct named-profile root and redirected-root guard\n";
}

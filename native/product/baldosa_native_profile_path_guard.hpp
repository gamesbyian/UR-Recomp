#pragma once

// Native Modern named-profile path admission. Reuse the existing profile,
// catalog and SRAM codecs; this guard only rejects symlinked ancestors/files
// before a product boundary opens the selected profile. It is a preflight,
// not a promise of race-free opening against an uncooperating filesystem
// adversary. Existing nonblocking OS locks still coordinate typed writers.
#include <filesystem>
#include <system_error>

namespace ur::product {

inline bool baldosa_native_real_directory(
    const std::filesystem::path& candidate) {
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(candidate, ec);
    return !ec && std::filesystem::is_directory(status) &&
        !std::filesystem::is_symlink(status);
}

inline bool baldosa_native_real_file(
    const std::filesystem::path& candidate) {
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(candidate, ec);
    return !ec && std::filesystem::is_regular_file(status) &&
        !std::filesystem::is_symlink(status);
}

inline bool baldosa_native_selected_profile_paths_are_real(
    const std::filesystem::path& user_root,
    const std::filesystem::path& selected_save_root) {
    namespace fs = std::filesystem;
    // This guard accepts only the canonical product-resolved subtree.
    if (!user_root.is_absolute() || selected_save_root.is_absolute() ||
        selected_save_root.parent_path() != fs::path("saves") ||
        selected_save_root.filename().string().rfind("profile-", 0) != 0)
        return false;
    const auto profile = user_root / selected_save_root;
    return baldosa_native_real_directory(user_root) &&
           baldosa_native_real_directory(user_root / "saves") &&
        baldosa_native_real_directory(profile) &&
        baldosa_native_real_file(profile / "host-profile.txt") &&
        baldosa_native_real_file(profile / "save.srm");
}

} // namespace ur::product

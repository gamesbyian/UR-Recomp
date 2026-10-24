#pragma once

// Native Modern named-profile path admission. Reuse the existing profile,
// catalog and SRAM codecs; this guard only rejects symlinked ancestors/files
// before a product boundary opens the selected profile. It is a preflight,
// not a promise of race-free opening against an uncooperating filesystem
// adversary. Existing nonblocking OS locks still coordinate typed writers.
#include <filesystem>
#include <system_error>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ur::product {

// Windows junctions and other directory reparse points are not reliably
// classified as symbolic links by C++17 symlink_status(). The selected save
// path must not traverse any reparse point, including an ancestor above the
// user-data root. This is a preflight, not a TOCTOU-free handle admission.
inline bool baldosa_native_not_reparse_point(
    const std::filesystem::path& candidate) {
#if defined(_WIN32)
    const DWORD attributes = GetFileAttributesW(candidate.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
           (attributes & FILE_ATTRIBUTE_REPARSE_POINT) == 0;
#else
    (void)candidate;
    return true;
#endif
}

inline bool baldosa_native_real_directory(
    const std::filesystem::path& candidate) {
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(candidate, ec);
    return !ec && std::filesystem::is_directory(status) &&
        !std::filesystem::is_symlink(status) &&
        baldosa_native_not_reparse_point(candidate);
}

inline bool baldosa_native_real_file(
    const std::filesystem::path& candidate) {
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(candidate, ec);
    return !ec && std::filesystem::is_regular_file(status) &&
        !std::filesystem::is_symlink(status) &&
        baldosa_native_not_reparse_point(candidate);
}

inline bool baldosa_native_real_directory_chain(
    const std::filesystem::path& user_root) {
    // symlink_status(child) follows any redirected parent. Check every
    // component from the user-data root to the filesystem root explicitly.
    for (auto current = user_root; !current.empty();) {
        if (!baldosa_native_real_directory(current)) return false;
        const auto parent = current.parent_path();
        if (parent == current) break;
        current = parent;
    }
    return true;
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
    return baldosa_native_real_directory_chain(user_root) &&
           baldosa_native_real_directory(user_root / "saves") &&
        baldosa_native_real_directory(profile) &&
        baldosa_native_real_file(profile / "host-profile.txt") &&
        baldosa_native_real_file(profile / "save.srm");
}

} // namespace ur::product

#pragma once
// The product and SDL preference-path APIs carry UTF-8 bytes. On Windows,
// narrow filesystem::path constructors use the active code page, not UTF-8.
// Convert only at the native filesystem boundary; POSIX paths stay bytewise.
#include <cstddef>
#include <filesystem>
#include <string>

namespace ur::product {
inline std::filesystem::path host_native_path_from_utf8(const std::string& utf8) {
#if defined(_WIN32)
    return std::filesystem::u8path(utf8);
#else
    return std::filesystem::path(utf8);
#endif
}

// SDL_GetPrefPath and the override can name a filesystem root. Removing every
// trailing separator turns POSIX "/" into an empty path and Windows "C:\\"
// into drive-relative "C:", which redirects profile and Records I/O.
// Preserve the root prefix while trimming separators on ordinary directories.
inline std::string host_trim_user_data_root(std::string root) {
    if (root.empty()) return root;
    const auto separator = [](char c) { return c == '/' || c == '\\'; };
    const auto ascii_letter = [](char c) {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    };
    std::size_t minimum = separator(root[0]) ? 1u : 0u;
    if (root.size() >= 2 && separator(root[0]) && separator(root[1])) {
        minimum = 2;
    }
    if (root.size() >= 3 && ascii_letter(root[0]) && root[1] == ':' &&
        separator(root[2])) {
        minimum = 3;
    }
    // Extended-length drive roots (\\\\?\\C:\\) need the same protection.
    if (root.size() >= 7 && separator(root[0]) && separator(root[1]) &&
        (root[2] == '?' || root[2] == '.') && separator(root[3]) &&
        ascii_letter(root[4]) && root[5] == ':' && separator(root[6])) {
        minimum = 7;
    }
    while (root.size() > minimum && separator(root.back())) root.pop_back();
    return root;
}
}  // namespace ur::product

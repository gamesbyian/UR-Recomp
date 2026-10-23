#pragma once
// The product and SDL preference-path APIs carry UTF-8 bytes. On Windows,
// narrow filesystem::path constructors use the active code page, not UTF-8.
// Convert only at the native filesystem boundary; POSIX paths stay bytewise.
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
}  // namespace ur::product

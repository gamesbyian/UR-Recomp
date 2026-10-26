#pragma once

#include <cstdlib>
#include <filesystem>
#include <string>

#include "baldosa_native_options.hpp"

namespace ur::product {

// The native Options store accepts UTF-8 filenames, even on Win32. Read the
// same wide user root as the Modern frontend before joining options-v1.txt;
// a narrow getenv()/filesystem::path(char*) round trip loses non-ACP names.
inline std::string baldosa_native_options_user_path_utf8() {
#if defined(_WIN32)
    const wchar_t* root = _wgetenv(L"SNESRECOMP_USER_DATA_DIR");
    if (!root || !*root) return {};
    return baldosa_options_path(std::filesystem::path(root)).u8string();
#else
    const char* root = std::getenv("SNESRECOMP_USER_DATA_DIR");
    if (!root || !*root) return {};
    return baldosa_options_path(std::filesystem::path(root)).string();
#endif
}

}  // namespace ur::product

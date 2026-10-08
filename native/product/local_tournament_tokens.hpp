#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#if defined(_MSC_VER)
#pragma comment(lib, "bcrypt.lib")
#endif
#elif defined(__linux__)
#include <cerrno>
#include <sys/random.h>
#elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__)
#include <cstdlib>
#endif

namespace ur::product {

// Never use clocks, counters, profile names, guest input, saved artifact IDs
// or predictable PRNGs to mint tournament or per-fixture attempt identity.
// These are 128-bit independent instance markers, NOT authorization secrets.
// Refuse the operation if platform OS entropy cannot be obtained.
inline std::optional<std::string> mint_local_tournament_token() noexcept {
    std::array<std::uint8_t, 16> bytes{};
#if defined(_WIN32)
    const NTSTATUS result = BCryptGenRandom(
        nullptr, bytes.data(), static_cast<ULONG>(bytes.size()),
        BCRYPT_USE_SYSTEM_PREFERRED_RNG);
    if (!BCRYPT_SUCCESS(result)) return std::nullopt;
#elif defined(__linux__)
    std::size_t filled = 0;
    while (filled < bytes.size()) {
        const auto count = getrandom(
            bytes.data() + filled, bytes.size() - filled, 0);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) return std::nullopt;
        filled += static_cast<std::size_t>(count);
    }
#elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__)
    arc4random_buf(bytes.data(), bytes.size());
#else
    return std::nullopt;
#endif
    constexpr char digits[] = "0123456789abcdef";
    std::string token(32, '0');
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        token[i * 2] = digits[bytes[i] >> 4];
        token[i * 2 + 1] = digits[bytes[i] & 0x0f];
    }
    return token;
}

} // namespace ur::product

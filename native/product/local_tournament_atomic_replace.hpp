#pragma once

// Generic host-owned mutable-file writer, first introduced for tournament
// sessions/checkpoints and now used by profiles, profile catalogs and options.
// A fixed path+".tmp" races across processes: another writer can truncate or
// rename a staged payload before its owner publishes it. Private same-directory
// reservations preserve complete-file visibility and the previous good target
// on failed staging; replacement remains last-writer-wins.
//
// This is NOT a cross-process compare-and-swap or multi-file transaction.
// Concurrent save-versus-retire, stale attempt deletion, and power-loss fsync
// durability need separate QA-02 design and acceptance.

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ur::product {
namespace detail {

inline std::optional<std::filesystem::path> reserve_tournament_staging(
    const std::filesystem::path& parent,
    std::string_view family) {
    namespace fs = std::filesystem;
    if (family.empty()) return std::nullopt;
    static std::atomic<std::uint64_t> serial{0};
    const fs::path base = parent.empty() ? fs::path(".") : parent;
    for (unsigned attempt = 0; attempt < 32; ++attempt) {
        const auto tick = std::chrono::steady_clock::now()
            .time_since_epoch().count();
        const fs::path candidate = base /
            (".pending-" + std::string(family) + "-" +
             std::to_string(tick) + "-" +
             std::to_string(serial.fetch_add(1, std::memory_order_relaxed)));
        std::error_code ec;
        if (fs::create_directory(candidate, ec)) return candidate;
        if (ec) return std::nullopt;
    }
    return std::nullopt;
}

} // namespace detail

inline bool write_host_replace_staged(
    const std::string& final_name,
    std::string_view data,
    std::string_view staging_family) {
    namespace fs = std::filesystem;
    if (final_name.empty() || data.empty()) return false;
    const fs::path final_path(final_name);
    const auto staging = detail::reserve_tournament_staging(
        final_path.parent_path(), staging_family);
    if (!staging) return false;
    const fs::path tmp = *staging / "record.tmp";
    const auto cleanup = [&] {
        std::error_code ec;
        fs::remove_all(*staging, ec);
    };
    std::FILE* file = std::fopen(tmp.string().c_str(), "wb");
    if (!file) {
        cleanup();
        return false;
    }
    const auto written = std::fwrite(data.data(), 1, data.size(), file);
    const bool flushed = std::fflush(file) == 0;
    const bool closed = std::fclose(file) == 0;
    if (written != data.size() || !flushed || !closed) {
        cleanup();
        return false;
    }
#if defined(_WIN32)
    const bool published = MoveFileExW(
        tmp.c_str(), final_path.c_str(),
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    std::error_code ec;
    fs::rename(tmp, final_path, ec);
    const bool published = !ec;
#endif
    cleanup();
    return published;
}

// Compatibility entrypoint for the tournament stores and existing tests.
inline bool write_tournament_replace_staged(
    const std::string& final_name,
    std::string_view data,
    std::string_view staging_family) {
    return write_host_replace_staged(final_name, data, staging_family);
}

} // namespace ur::product

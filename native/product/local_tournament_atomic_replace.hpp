#pragma once

// Generic host-owned mutable-file writer, first introduced for tournament
// sessions/checkpoints and now used by profiles, profile catalogs and options.
// A fixed path+".tmp" races across processes: another writer can truncate or
// rename a staged payload before its owner publishes it. Private same-directory
// reservations preserve complete-file visibility and the previous good target
// on failed staging; replacement remains last-writer-wins.
//
// This is NOT a cross-process compare-and-swap or multi-file transaction.
// File-content durability is requested before publication; exact Windows
// device/power-loss witnesses and cross-file commit durability are still open.

#include <atomic>
#include <cerrno>
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
#include <io.h>
#else
#include <fcntl.h>
#include <unistd.h>
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


inline bool sync_staged_file(std::FILE* file) {
    if (!file) return false;
#if defined(_WIN32)
    const int descriptor = _fileno(file);
    if (descriptor < 0) return false;
    const intptr_t handle = _get_osfhandle(descriptor);
    return handle != -1 && FlushFileBuffers(
        reinterpret_cast<HANDLE>(handle)) != 0;
#else
    const int descriptor = fileno(file);
    if (descriptor < 0) return false;
    int result = -1;
    do {
        result = fsync(descriptor);
    } while (result < 0 && errno == EINTR);
    return result == 0;
#endif
}

inline void sync_published_directory_best_effort(
    const std::filesystem::path& parent) {
#if !defined(_WIN32)
    // Atomic rename alone does not durably record its directory entry.
    // Publication has already occurred and the bool API cannot distinguish
    // "published but directory sync failed" from a genuinely failed write.
    // Do not return false and invite a compensating rollback after commit.
    const auto directory = parent.empty() ? std::filesystem::path(".") : parent;
    const int fd = open(directory.c_str(), O_RDONLY | O_DIRECTORY);
    if (fd < 0) return;
    int result = -1;
    do {
        result = fsync(fd);
    } while (result < 0 && errno == EINTR);
    (void)result;
    (void)close(fd);
#else
    (void)parent;
#endif
}

} // namespace detail

inline bool write_host_replace_staged(
    const std::string& final_name,
    std::string_view data,
    std::string_view staging_family,
    void (*after_staging_for_test)() = nullptr) {
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
    // fwrite/fflush/fclose merely drain userspace buffering. When the OS
    // cannot persist these bytes, reject the staged write BEFORE the rename
    // can hide a previously valid profile/SRAM/catalog/checkpoint.
    const bool synced = written == data.size() && flushed &&
                        detail::sync_staged_file(file);
    const bool closed = std::fclose(file) == 0;
    if (written != data.size() || !flushed || !synced || !closed) {
        cleanup();
        return false;
    }
    // An optional test callback models immediate process death after close
    // and before the atomic visibility transition. Production never supplies it.
    if (after_staging_for_test) after_staging_for_test();
#if defined(_WIN32)
    const bool published = MoveFileExW(
        tmp.c_str(), final_path.c_str(),
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    std::error_code ec;
    fs::rename(tmp, final_path, ec);
    const bool published = !ec;
#endif
    if (published) detail::sync_published_directory_best_effort(
        final_path.parent_path());
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

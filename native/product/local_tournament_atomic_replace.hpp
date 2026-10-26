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

// Existing codec writers close std::ofstream before returning, so they
// cannot pass their original FILE handle to sync_staged_file. Reopen only
// the private, already closed staged file with write access and require an
// OS durability request BEFORE claiming any public immutable filename.
// On Windows, preserve native Unicode path support with _wfopen.
inline bool sync_closed_staged_file(const std::filesystem::path& staged) {
#if defined(_WIN32)
    std::FILE* file = _wfopen(staged.c_str(), L"rb+");
#else
    std::FILE* file = std::fopen(staged.c_str(), "rb+");
#endif
    if (!file) return false;
    const bool synced = sync_staged_file(file);
    const bool closed = std::fclose(file) == 0;
    return synced && closed;
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
    const std::filesystem::path& final_path,
    std::string_view data,
    std::string_view staging_family,
    void (*after_staging_for_test)() = nullptr,
    bool (*sync_override_for_test)(std::FILE*) = nullptr,
    void (*after_publication_for_test)() = nullptr) {
    namespace fs = std::filesystem;
    if (final_path.empty() || data.empty()) return false;
    const auto staging = detail::reserve_tournament_staging(
        final_path.parent_path(), staging_family);
    if (!staging) {
#if defined(_WIN32) && defined(UR_ATOMIC_REPLACE_TEST_DIAGNOSTICS)
        std::fprintf(stderr, "WIN32_ATOMIC_REPLACE_DIAGNOSTIC stage=reserve error=%lu\\n",
                     static_cast<unsigned long>(GetLastError()));
#endif
        return false;
    }
    const fs::path tmp = *staging / "record.tmp";
    const auto cleanup = [&] {
        std::error_code ec;
        fs::remove_all(*staging, ec);
    };
#if defined(_WIN32)
    // Preserve the native UTF-16 path across Windows staging; ANSI conversion
    // cannot round-trip some player profile names.
    std::FILE* file = _wfopen(tmp.c_str(), L"wb");
#else
    std::FILE* file = std::fopen(tmp.c_str(), "wb");
#endif
    if (!file) {
#if defined(_WIN32) && defined(UR_ATOMIC_REPLACE_TEST_DIAGNOSTICS)
        std::fprintf(stderr, "WIN32_ATOMIC_REPLACE_DIAGNOSTIC stage=open errno=%d error=%lu\\n",
                     errno, static_cast<unsigned long>(GetLastError()));
#endif
        cleanup();
        return false;
    }
    const auto written = std::fwrite(data.data(), 1, data.size(), file);
    const bool flushed = std::fflush(file) == 0;
    // fwrite/fflush/fclose merely drain userspace buffering. When the OS
    // cannot persist these bytes, reject the staged write BEFORE the rename
    // can hide a previously valid profile/SRAM/catalog/checkpoint.
    const bool synced = written == data.size() && flushed &&
                        (sync_override_for_test
                            ? sync_override_for_test(file)
                            : detail::sync_staged_file(file));
    const bool closed = std::fclose(file) == 0;
    if (written != data.size() || !flushed || !synced || !closed) {
#if defined(_WIN32) && defined(UR_ATOMIC_REPLACE_TEST_DIAGNOSTICS)
        std::fprintf(stderr, "WIN32_ATOMIC_REPLACE_DIAGNOSTIC stage=sync written=%zu expected=%zu flushed=%d synced=%d closed=%d errno=%d\\n",
                     written, data.size(), static_cast<int>(flushed),
                     static_cast<int>(synced), static_cast<int>(closed), errno);
#endif
        cleanup();
        return false;
    }
    // An optional test callback models immediate process death after close
    // and before the atomic visibility transition. Production never supplies it.
    if (after_staging_for_test) after_staging_for_test();
#if defined(_WIN32)
    // Contending Windows writers can briefly deny a rename while an old
    // destination handle is being released. Retry transient sharing/lock
    // errors against the SAME fully synced stage, without rewriting bytes.
    // Permanent permission, disk-full and no-replace intent failures are
    // never retried here; a persistent denial retains the old canonical file.
    bool published = false;
    for (unsigned attempt = 0; attempt < 8; ++attempt) {
        if (MoveFileExW(tmp.c_str(), final_path.c_str(),
                MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0) {
            published = true;
            break;
        }
        const DWORD error = GetLastError();
#if defined(UR_ATOMIC_REPLACE_TEST_DIAGNOSTICS)
        if (attempt == 7 || (error != ERROR_SHARING_VIOLATION &&
                             error != ERROR_LOCK_VIOLATION))
            std::fprintf(stderr, "WIN32_ATOMIC_REPLACE_DIAGNOSTIC stage=rename error=%lu attempt=%u\\n",
                         static_cast<unsigned long>(error), attempt);
#endif
        if ((error != ERROR_SHARING_VIOLATION &&
             error != ERROR_LOCK_VIOLATION) || attempt == 7)
            break;
        Sleep(1u << attempt);  // Bounded total: 127 ms.
    }
#else
    std::error_code ec;
    fs::rename(tmp, final_path, ec);
    const bool published = !ec;
#endif
    if (published) {
        detail::sync_published_directory_best_effort(final_path.parent_path());
        // Fault injection: the canonical file is now visible and the private
        // staging reservation is empty, but its cleanup has not run yet.
        // Production never provides this callback.
        if (after_publication_for_test) after_publication_for_test();
    }
    cleanup();
    return published;
}

// Recovery intents and forensic receipts need no-replace publication: a
// concurrent writer may create the final name after an earlier absence test.
// Do not use the normal last-writer-wins settings/profile replacement here.
// Stage and request an OS flush BEFORE claiming an immutable destination.
inline bool write_host_create_staged_native(
    const std::filesystem::path& target,
    std::string_view data,
    std::string_view staging_family,
    void (*after_staging_for_test)() = nullptr) {
    namespace fs = std::filesystem;
    if (target.empty() || data.empty()) return false;
    const auto stage = detail::reserve_tournament_staging(
        target.parent_path(), staging_family);
    if (!stage) return false;
    const auto tmp = *stage / "record.tmp";
    const auto cleanup = [&] {
        std::error_code ec;
        fs::remove_all(*stage, ec);
    };
#if defined(_WIN32)
    std::FILE* file = _wfopen(tmp.c_str(), L"wb");
#else
    std::FILE* file = std::fopen(tmp.c_str(), "wb");
#endif
    if (!file) {
        cleanup();
        return false;
    }
    const auto written = std::fwrite(data.data(), 1, data.size(), file);
    const bool flushed = std::fflush(file) == 0;
    const bool synced = written == data.size() && flushed &&
                        detail::sync_staged_file(file);
    const bool closed = std::fclose(file) == 0;
    if (!synced || !closed) {
        cleanup();
        return false;
    }
    if (after_staging_for_test) after_staging_for_test();
#if defined(_WIN32)
    // Same-volume MoveFileExW without REPLACE_EXISTING atomically refuses
    // an occupied name. Retain WRITE_THROUGH from the original staged
    // durability contract without permitting a last-writer-wins replace.
    const bool published = MoveFileExW(
        tmp.c_str(), target.c_str(), MOVEFILE_WRITE_THROUGH) != 0;
#else
    // POSIX rename would overwrite. Atomic hard-link creation never does.
    std::error_code ec;
    fs::create_hard_link(tmp, target, ec);
    const bool published = !ec;
#endif
    if (published)
        detail::sync_published_directory_best_effort(target.parent_path());
    cleanup();
    return published;
}

// Preserve the existing narrow-path contract for legacy callers; native
// Windows paths must use write_host_create_staged_native instead.
inline bool write_host_create_staged(
    const std::string& final_name,
    std::string_view data,
    std::string_view staging_family,
    void (*after_staging_for_test)() = nullptr) {
    return write_host_create_staged_native(
        std::filesystem::path(final_name), data, staging_family,
        after_staging_for_test);
}

// Compatibility entrypoint for the tournament stores and existing tests.
inline bool write_tournament_replace_staged(
    const std::string& final_name,
    std::string_view data,
    std::string_view staging_family) {
    return write_host_replace_staged(final_name, data, staging_family);
}

} // namespace ur::product

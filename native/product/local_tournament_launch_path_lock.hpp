#pragma once

// Scoped interprocess exclusion for one mutable tournament launch pathname.
// Both publication and exact-attempt retirement MUST acquire the SAME lock
// before observing or changing the canonical path. Lock ownership belongs to
// the OS file handle, not a removable .lock sentinel, so crashing a process
// releases its lock and no stale PID/time-based takeover can delete live data.
//
// Important boundaries: protects cooperating UR-Recomp writers on a local
// filesystem. It is not a multi-file transaction, network-filesystem lease,
// or permission to infer a result from arbitrary Records files.

#include <cerrno>
#include <filesystem>
#include <string>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/file.h>
#include <unistd.h>
#endif

namespace ur::product {

class TournamentLaunchPathLock {
public:
    explicit TournamentLaunchPathLock(const std::string& target) {
        if (target.empty()) return;
        const std::filesystem::path lock_path =
            std::filesystem::path(target).concat(".urmutex");
#if defined(_WIN32)
        file_ = CreateFileW(
            lock_path.c_str(), GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (file_ == INVALID_HANDLE_VALUE) return;
        if (!LockFileEx(file_, LOCKFILE_EXCLUSIVE_LOCK, 0, 1u, 0u,
                        &overlapped_)) {
            CloseHandle(file_);
            file_ = INVALID_HANDLE_VALUE;
        }
#else
        fd_ = open(lock_path.c_str(), O_CREAT | O_RDWR, 0600);
        if (fd_ < 0) return;
        int result;
        do {
            result = flock(fd_, LOCK_EX);
        } while (result < 0 && errno == EINTR);
        if (result < 0) {
            close(fd_);
            fd_ = -1;
        }
#endif
    }

    TournamentLaunchPathLock(const TournamentLaunchPathLock&) = delete;
    TournamentLaunchPathLock& operator=(const TournamentLaunchPathLock&) = delete;

    ~TournamentLaunchPathLock() {
#if defined(_WIN32)
        if (file_ != INVALID_HANDLE_VALUE) {
            (void)UnlockFileEx(file_, 0, 1u, 0u, &overlapped_);
            CloseHandle(file_);
        }
#else
        if (fd_ >= 0) {
            (void)flock(fd_, LOCK_UN);
            (void)close(fd_);
        }
#endif
    }

    bool acquired() const noexcept {
#if defined(_WIN32)
        return file_ != INVALID_HANDLE_VALUE;
#else
        return fd_ >= 0;
#endif
    }

private:
#if defined(_WIN32)
    HANDLE file_ = INVALID_HANDLE_VALUE;
    OVERLAPPED overlapped_{};
#else
    int fd_ = -1;
#endif
};

} // namespace ur::product

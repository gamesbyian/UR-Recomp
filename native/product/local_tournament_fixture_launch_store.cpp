#include "local_tournament_fixture_launch_store.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <cerrno>
#include <cstdio>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace ur::product {
namespace {

LocalTournamentLaunchFileResult error_result(
    LocalTournamentLaunchFileStatus status,
    const char* detail) {
    return {status, std::nullopt, detail};
}

} // namespace

LocalTournamentLaunchFileStatus save_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentPendingFixture& pending) {
    if (path.empty()) return LocalTournamentLaunchFileStatus::Rejected;
    const std::string encoded = encode_local_tournament_pending_fixture(pending);
    if (encoded.empty() || encoded.size() > kLocalTournamentLaunchMaxBytes) {
        return LocalTournamentLaunchFileStatus::Rejected;
    }

    // Publish and exact-attempt retirement serialize on this same OS lock.
    // Unique staging avoids partial writes; this additionally prevents a
    // stale read/compare/remove from deleting a newer launched attempt.
    TournamentLaunchPathLock lock(path);
    if (!lock.acquired()) return LocalTournamentLaunchFileStatus::IoError;
    if (!write_tournament_replace_staged(path, encoded, "urlaunch")) {
        return LocalTournamentLaunchFileStatus::IoError;
    }
    return LocalTournamentLaunchFileStatus::Saved;
}

namespace {

// Strict bounded disk decoding alone does not authorize restarting a guest
// attempt. The public restore API adds the active unfinished-fixture check;
// exact-match retirement may instead follow a successfully committed result.
LocalTournamentLaunchFileResult read_local_tournament_launch_file(
    const std::string& path) {
    if (path.empty()) {
        return error_result(LocalTournamentLaunchFileStatus::Rejected,
                            "empty launch checkpoint path");
    }
    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        return errno == ENOENT
            ? error_result(LocalTournamentLaunchFileStatus::Missing,
                           "launch checkpoint absent")
            : error_result(LocalTournamentLaunchFileStatus::IoError,
                           "cannot open launch checkpoint");
    }
    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return error_result(LocalTournamentLaunchFileStatus::IoError,
                            "cannot size launch checkpoint");
    }
    const long size = std::ftell(file);
    if (size <= 0 ||
        size > static_cast<long>(kLocalTournamentLaunchMaxBytes)) {
        std::fclose(file);
        return error_result(LocalTournamentLaunchFileStatus::Rejected,
                            "invalid launch checkpoint size");
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return error_result(LocalTournamentLaunchFileStatus::IoError,
                            "cannot rewind launch checkpoint");
    }

    std::string encoded(static_cast<std::size_t>(size), '\0');
    const std::size_t read =
        std::fread(encoded.data(), 1u, encoded.size(), file);
    const bool closed = std::fclose(file) == 0;
    if (read != encoded.size() || !closed) {
        return error_result(LocalTournamentLaunchFileStatus::IoError,
                            "short read or close failure");
    }
    const auto decoded = decode_local_tournament_pending_fixture(encoded);
    if (!decoded) {
        return error_result(LocalTournamentLaunchFileStatus::Rejected,
                            "invalid canonical checkpoint");
    }
    return {LocalTournamentLaunchFileStatus::Loaded, *decoded, {}};
}

} // namespace

LocalTournamentLaunchFileResult load_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentState& active_tournament,
    std::string_view active_tournament_id) {
    auto loaded = read_local_tournament_launch_file(path);
    if (!loaded.loaded()) return loaded;
    if (loaded.pending->tournament_id != active_tournament_id ||
        !local_tournament_pending_matches_fixture(
            *loaded.pending, active_tournament)) {
        return error_result(LocalTournamentLaunchFileStatus::Rejected,
                            "checkpoint invalid for active tournament");
    }
    return loaded;
}

LocalTournamentLaunchFileStatus retire_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentPendingFixture& expected_pending) {
    const std::string expected_bytes =
        encode_local_tournament_pending_fixture(expected_pending);
    if (expected_bytes.empty()) return LocalTournamentLaunchFileStatus::Rejected;
    TournamentLaunchPathLock lock(path);
    if (!lock.acquired()) return LocalTournamentLaunchFileStatus::IoError;
    // The lock remains held through the entire read-validate-unlink sequence.
    // A competing publication cannot replace this path after validation.
    const auto loaded = read_local_tournament_launch_file(path);
    if (!loaded.loaded()) return loaded.status;
    if (encode_local_tournament_pending_fixture(*loaded.pending) !=
        expected_bytes) {
        return LocalTournamentLaunchFileStatus::Rejected;
    }
    // No-op if the expected checkpoint was superseded, with the lock held
    // until the actual removal has completed. Never delete a newer attempt.
    errno = 0;
    if (std::remove(path.c_str()) == 0) {
        return LocalTournamentLaunchFileStatus::Saved;
    }
    return errno == ENOENT
        ? LocalTournamentLaunchFileStatus::Missing
        : LocalTournamentLaunchFileStatus::IoError;
}

} // namespace ur::product

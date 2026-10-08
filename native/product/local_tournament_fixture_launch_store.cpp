#include "local_tournament_fixture_launch_store.hpp"

#include <cerrno>
#include <cstdio>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace ur::product {
namespace {

bool replace_file_atomically(
    const std::string& temporary,
    const std::string& destination) noexcept {
#if defined(_WIN32)
    return MoveFileExA(
        temporary.c_str(), destination.c_str(),
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    return std::rename(temporary.c_str(), destination.c_str()) == 0;
#endif
}

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

    const std::string temporary = path + ".tmp";
    std::FILE* file = std::fopen(temporary.c_str(), "wb");
    if (!file) return LocalTournamentLaunchFileStatus::IoError;
    const std::size_t written =
        std::fwrite(encoded.data(), 1u, encoded.size(), file);
    const bool flushed = std::fflush(file) == 0;
    const bool closed = std::fclose(file) == 0;
    if (written != encoded.size() || !flushed || !closed) {
        std::remove(temporary.c_str());
        return LocalTournamentLaunchFileStatus::IoError;
    }
    if (!replace_file_atomically(temporary, path)) {
        std::remove(temporary.c_str());
        return LocalTournamentLaunchFileStatus::IoError;
    }
    return LocalTournamentLaunchFileStatus::Saved;
}

LocalTournamentLaunchFileResult load_local_tournament_launch_file(
    const std::string& path,
    const LocalTournamentState& active_tournament,
    std::string_view active_tournament_id) {
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
    if (!decoded ||
        decoded->tournament_id != active_tournament_id ||
        !local_tournament_pending_matches_fixture(
            *decoded, active_tournament)) {
        return error_result(LocalTournamentLaunchFileStatus::Rejected,
                            "checkpoint invalid for active tournament");
    }
    return {
        LocalTournamentLaunchFileStatus::Loaded, *decoded, {},
    };
}

LocalTournamentLaunchFileStatus retire_local_tournament_launch_file(
    const std::string& path) {
    if (path.empty()) return LocalTournamentLaunchFileStatus::Rejected;
    errno = 0;
    if (std::remove(path.c_str()) == 0) {
        return LocalTournamentLaunchFileStatus::Saved;
    }
    return errno == ENOENT
        ? LocalTournamentLaunchFileStatus::Missing
        : LocalTournamentLaunchFileStatus::IoError;
}

} // namespace ur::product

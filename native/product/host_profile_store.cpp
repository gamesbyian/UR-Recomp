#include "host_profile_store.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <cerrno>
#include <cstdio>
#include <filesystem>
#include <string>

namespace ur::product {
namespace {

constexpr long kMaxProfileStateBytes =
    static_cast<long>(kStockSramBytes * 2 + 1024);

}  // namespace

HostProfileLoadResult load_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id) {
    if (!policy_for(mode).host_profiles) {
        return {
            HostProfileLoadStatus::RejectedByPolicy,
            std::nullopt,
            "profile persistence disabled by execution policy"};
    }
    if (path.empty() || !is_valid_profile_id(expected_profile_id)) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "invalid profile load request"};
    }

    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        if (errno == ENOENT) {
            return {HostProfileLoadStatus::Missing, std::nullopt, {}};
        }
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to open profile-state file"};
    }

    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to size profile-state file"};
    }
    const long size = std::ftell(file);
    if (size < 0 || size > kMaxProfileStateBytes) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "profile-state file size is invalid"};
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to rewind profile-state file"};
    }

    std::string encoded(static_cast<std::size_t>(size), '\0');
    if (size > 0) {
        const std::size_t read = std::fread(
            encoded.data(), 1, static_cast<std::size_t>(size), file);
        if (read != static_cast<std::size_t>(size)) {
            std::fclose(file);
            return {
                HostProfileLoadStatus::IoError,
                std::nullopt,
                "short profile-state read"};
        }
    }
    if (std::fclose(file) != 0) {
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to close profile-state file"};
    }

    const auto decoded = decode_host_profile_state(encoded);
    if (!decoded) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            decoded.error};
    }
    if (decoded.state->profile_id != expected_profile_id) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "profile-state identifier mismatch"};
    }

    return {HostProfileLoadStatus::Loaded, decoded.state, {}};
}

HostProfileResolveResult resolve_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id) {
    const auto loaded =
        load_host_profile_state_file(mode, path, expected_profile_id);
    if (loaded.loaded()) {
        return {HostProfileResolveStatus::Loaded, loaded.state, {}};
    }
    if (loaded.status == HostProfileLoadStatus::RejectedByPolicy) {
        return {
            HostProfileResolveStatus::RejectedByPolicy,
            std::nullopt,
            loaded.error};
    }
    if (loaded.status == HostProfileLoadStatus::IoError) {
        return {HostProfileResolveStatus::IoError, std::nullopt, loaded.error};
    }

    auto fallback = make_default_host_profile_state(expected_profile_id);
    if (!fallback) {
        return {
            HostProfileResolveStatus::IoError,
            std::nullopt,
            "unable to construct default profile state"};
    }

    if (loaded.status == HostProfileLoadStatus::Missing) {
        return {
            HostProfileResolveStatus::DefaultedMissing,
            fallback,
            {}};
    }
    return {
        HostProfileResolveStatus::DefaultedMalformed,
        fallback,
        loaded.error};
}

HostProfileSaveStatus save_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& state) {
    if (!policy_for(mode).host_profiles || path.empty()) {
        return HostProfileSaveStatus::Rejected;
    }

    const std::string encoded = encode_host_profile_state(state);
    if (encoded.empty() ||
        encoded.size() > static_cast<std::size_t>(kMaxProfileStateBytes)) {
        return HostProfileSaveStatus::Rejected;
    }

    if (!write_host_replace_staged(path, encoded, "urprofile")) {
        return HostProfileSaveStatus::IoError;
    }
    return HostProfileSaveStatus::Saved;
}

// Caller already owns host-profile.txt.urmutex (and may also hold the
// selector lease). Never reacquire the profile lock on this path.
HostProfileSaveStatus save_host_profile_state_file_if_current_under_lock(
    ExecutionMode mode,
    const std::string& path,
    const std::optional<HostProfileState>& expected_current,
    const HostProfileState& next) {
    if (!policy_for(mode).host_profiles || path.empty() ||
        encode_host_profile_state(next).empty() ||
        (expected_current &&
         expected_current->profile_id != next.profile_id)) {
        return HostProfileSaveStatus::Rejected;
    }

    const auto current =
        load_host_profile_state_file(mode, path, next.profile_id);
    if (expected_current) {
        if (current.status == HostProfileLoadStatus::IoError)
            return HostProfileSaveStatus::IoError;
        if (!current.loaded() || !(*current.state == *expected_current))
            return HostProfileSaveStatus::Conflict;
    } else {
        if (current.status == HostProfileLoadStatus::IoError)
            return HostProfileSaveStatus::IoError;
        if (current.status != HostProfileLoadStatus::Missing)
            return HostProfileSaveStatus::Conflict;
    }
    return save_host_profile_state_file(mode, path, next);
}

HostProfileSaveStatus save_host_profile_state_file_if_current(
    ExecutionMode mode,
    const std::string& path,
    const std::optional<HostProfileState>& expected_current,
    const HostProfileState& next) {
    // Preserve the old reject-before-I/O behavior for invalid input.
    if (!policy_for(mode).host_profiles || path.empty() ||
        encode_host_profile_state(next).empty() ||
        (expected_current &&
         expected_current->profile_id != next.profile_id)) {
        return HostProfileSaveStatus::Rejected;
    }
    // The same persistent lock used by all existing profile CAS writers.
    TournamentLaunchPathLock lock(path);
    if (!lock.acquired()) return HostProfileSaveStatus::IoError;
    return save_host_profile_state_file_if_current_under_lock(
        mode, path, expected_current, next);
}

HostProfileSaveStatus remove_host_profile_state_file_if_current(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& expected_current) {
    if (!policy_for(mode).host_profiles || path.empty() ||
        encode_host_profile_state(expected_current).empty()) {
        return HostProfileSaveStatus::Rejected;
    }
    TournamentLaunchPathLock lock(path);
    if (!lock.acquired()) return HostProfileSaveStatus::IoError;
    const auto current = load_host_profile_state_file(
        mode, path, expected_current.profile_id);
    if (current.status == HostProfileLoadStatus::IoError)
        return HostProfileSaveStatus::IoError;
    if (!current.loaded() || !(*current.state == expected_current))
        return HostProfileSaveStatus::Conflict;
    std::error_code ec;
    const bool removed = std::filesystem::remove(path, ec);
    if (!removed || ec) return HostProfileSaveStatus::IoError;
    return HostProfileSaveStatus::Saved;
}


bool reusable_aborted_profile_creation_root(const std::string& root_path) {
    namespace fs = std::filesystem;
    if (root_path.empty()) return false;
    const fs::path root(root_path);
    std::error_code ec;
    const auto status = fs::symlink_status(root, ec);
    // Do not follow a renamed/symlinked profile root or adopt an existing
    // SRAM/progression namespace merely because the catalog lacks its row.
    if (ec || status.type() != fs::file_type::directory) return false;
    fs::directory_iterator it(root, ec);
    if (ec) return false;
    const fs::directory_iterator end;
    for (; it != end; it.increment(ec)) {
        if (ec || it->path().filename() != "host-profile.txt.urmutex") {
            return false;
        }
        const auto entry_status = it->symlink_status(ec);
        if (ec || entry_status.type() != fs::file_type::regular) {
            return false;
        }
    }
    return !ec;
}


bool pristine_unregistered_profile_creation_root(const std::string& root_path) {
    namespace fs = std::filesystem;
    if (root_path.empty()) return false;
    const fs::path root(root_path);
    std::error_code ec;
    if (fs::symlink_status(root, ec).type() != fs::file_type::directory ||
        ec) return false;
    bool has_profile = false;
    fs::directory_iterator it(root, ec);
    if (ec) return false;
    for (; it != fs::directory_iterator{}; it.increment(ec)) {
        if (ec) return false;
        const auto name = it->path().filename();
        if (name == "host-profile.txt" ||
            name == "host-profile.txt.urmutex") {
            if (it->symlink_status(ec).type() != fs::file_type::regular ||
                ec) return false;
            if (name == "host-profile.txt") has_profile = true;
            continue;
        }
        // A process killed *after* canonical rename, but before removal of
        // its private reservation, leaves an EMPTY staging directory. The
        // profile mutex is held by the caller while it verifies the complete
        // pristine state and publishes the roster. Retain this forensic
        // directory rather than deleting or adopting any unfinished payload.
        const std::string stage_name = name.string();
        if (stage_name.rfind(".pending-urprofile-", 0) != 0 ||
            it->symlink_status(ec).type() != fs::file_type::directory ||
            ec) return false;
        const bool empty = fs::is_empty(it->path(), ec);
        if (ec || !empty) return false;
    }
    return !ec && has_profile;
}

}  // namespace ur::product
